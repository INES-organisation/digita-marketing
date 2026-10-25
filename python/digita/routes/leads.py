"""Formulaires de prospects : demande d'audit, contact, newsletter."""
import logging

import httpx
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import booking, config, db, php, security
from ..services import email, ines
from ..render import render_view
from .common import redirect

log = logging.getLogger("digita.leads")


def _json(payload):
    return Response(php.json_encode(payload), media_type="application/json")


AUDIT_DETAILS = {"company": "Entreprise", "sector": "Secteur", "goal": "Objectif", "pack": "Pack",
                 "phone": "Téléphone"}


async def submit_audit(request):
    form = await request.form()
    name = form.get("name")
    mail = form.get("email")
    website = form.get("website") or "Non précisé"
    # Champs facultatifs des formulaires de diagnostic (accueil, /diagnostic) : qualifient le prospect.
    details = {label: php.trim(form.get(key) or "") for key, label in AUDIT_DETAILS.items()}
    # Créneau choisi sur /diagnostic : réservé dans INES Booking.
    day, slot = php.trim(form.get("date") or ""), php.trim(form.get("time_slot") or "")

    if not php.t(name) or not php.t(mail):
        return _json({"success": False, "message": "Veuillez remplir les champs obligatoires."})
    if day and slot and not details["Téléphone"]:
        return _json({"success": False, "message": "Indiquez votre téléphone : le consultant vous appelle à l'heure choisie."})
    # Base, INES et e-mails sont bloquants : hors de la boucle asynchrone.
    return _json(await run_in_threadpool(_process, name, mail, website, details, day, slot))


def _process(name, mail, website, details=None, day="", slot=""):
    details = details or {}
    phone = details.get("Téléphone", "")
    try:
        message = "Une nouvelle demande d'audit a été soumise.\n\n"
        message += "Nom : " + name + "\n"
        message += "Email : " + mail + "\n"
        message += "Site Web : " + website + "\n"
        for label, value in details.items():
            if value:
                message += label + " : " + value + "\n"

        status = None
        if day and slot:
            status, booking_message = booking.book(day, slot, name, mail, phone, message)
            if status == booking.TAKEN:
                return {"success": False, "message": booking_message}
            if status == booking.DOWN:  # INES injoignable : la demande devient une demande de rappel
                message += f"Créneau souhaité (non réservé, INES indisponible) : {booking.format_when(day, slot)}\n"
        subject = ("Diagnostic réservé - " if status == booking.BOOKED else "Demande d'Audit Stratégique - ") + name

        db.execute("INSERT INTO contact_messages (name, email, phone, subject, message, status) "
                   "VALUES (?, ?, ?, ?, ?, ?)", [name, mail, phone, subject, message, "new"])
        email.send_new_contact_notification(config.ADMIN_EMAIL, {
            "name": name, "email": mail, "subject": subject, "message": message, "phone": phone or "N/A",
        })
        if status == booking.BOOKED:  # lead INES et e-mail de confirmation déjà envoyés par booking.book
            return {"success": True, "booked": True, "message": booking_message}

        ines.push_lead(name, mail, "audit", message, phone or None)
        email.send_diagnostic_confirmation(mail, name)
        return {"success": True,
                "message": "Votre demande a été prise en compte. Un consultant vous rappelle sous 24 h ouvrées."}
    except Exception as e:  # noqa: BLE001 — même comportement que le catch (Exception) PHP
        log.error("Erreur Audit Submission: %s", e)
        return {"success": False, "message": "Une erreur technique est survenue."}


def booking_slots(request):
    """Créneaux libres du diagnostic de 30 min, lus en direct dans INES Booking."""
    try:
        days, _ = booking.available_days()
    except httpx.HTTPError as e:
        log.error("Créneaux INES indisponibles : %s", e)
        return _json({"success": False, "days": []})
    return _json({"success": True, "days": booking.days_for_display(days)})


# ---------------------------------------------------------------- formulaire de contact
SERVICES = {
    "strategie": "Conseil & Stratégie", "ia": "Intelligence Artificielle", "automation": "Automatisation",
    "prestige": "Identité de marque", "ecosysteme": "Écosystème Web",
}


async def submit_contact(request):
    """Formulaire de /contact : il n'avait pas de route POST (ni en PHP ni en Python), les messages
    se perdaient. Enregistré dans contact_messages, copié dans le CRM INES, notifié à l'admin."""
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "contact")

    data = {k: php.trim(form.get(k, "")) for k in ("nom", "entreprise", "email", "telephone", "service", "message")}
    if php.empty(data["nom"]) or php.empty(data["message"]) or not security.valid_email(data["email"]):
        request.session["contact_flash"] = {"ok": False, "message": "Merci d'indiquer votre nom, une adresse e-mail valide et votre message."}
        return redirect("/contact#formulaire")

    ok = await run_in_threadpool(_save_contact, data)
    request.session["contact_flash"] = {"ok": ok, "message": (
        "Merci, votre message a bien été envoyé. Nous vous répondons sous 48 h." if ok
        else "Une erreur technique est survenue. Merci de réessayer ou d'utiliser le chat.")}
    return redirect("/contact#formulaire")


def _save_contact(d):
    service = SERVICES.get(d["service"], d["service"] or "Non précisé")
    subject = "Contact site - " + service
    message = (f"Organisation : {d['entreprise'] or 'Non précisée'}\nExpertise : {service}\n\n{d['message']}")
    try:
        db.execute("INSERT INTO contact_messages (name, email, phone, subject, message, status) "
                   "VALUES (?, ?, ?, ?, ?, ?)", [d["nom"][:100], d["email"][:100], d["telephone"][:20],
                                                 subject[:200], message, "new"])
    except Exception as e:  # noqa: BLE001
        log.error("Erreur formulaire contact : %s", e)
        return False
    ines.push_lead(d["nom"], d["email"], "contact", message, d["telephone"])
    try:
        email.send_new_contact_notification(config.ADMIN_EMAIL, {
            "name": d["nom"], "email": d["email"], "subject": subject, "message": message,
            "phone": d["telephone"] or "N/A",
        })
    except Exception as e:  # noqa: BLE001 — le message est enregistré, l'e-mail est secondaire
        log.warning("Notification contact non envoyée : %s", e)
    return True


# ---------------------------------------------------------------- newsletter
async def subscribe_newsletter(request):
    """Inscription depuis le pied de page (le formulaire pointait vers une route inexistante)."""
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "contact")
    mail = php.trim(form.get("email", "")).lower()
    if not security.valid_email(mail) or len(mail) > 100:
        return _json({"success": False, "message": "Adresse e-mail invalide."})
    ok = await run_in_threadpool(_save_subscriber, mail)
    return _json({"success": ok, "message": "Merci, vous êtes inscrit à la newsletter." if ok
                  else "Une erreur technique est survenue, merci de réessayer."})


def _save_subscriber(mail):
    try:
        db.execute("INSERT INTO newsletters (email, status) VALUES (?, 'active') "
                   "ON CONFLICT (email) DO UPDATE SET status = 'active'", [mail])
    except Exception as e:  # noqa: BLE001
        log.error("Erreur inscription newsletter : %s", e)
        return False
    ines.push_lead(mail, mail, "newsletter")
    return True


# ---------------------------------------------------------------- annulation d'un rendez-vous
# Lien de l'e-mail de confirmation. GET n'annule pas (les messageries ouvrent les liens pour en
# faire un aperçu) : il affiche un bouton, et c'est le POST qui annule dans INES.
def _cancel_page(request, token, state, message=""):
    return render_view(request, "booking/cancel-content", {
        "title": "Annuler mon rendez-vous | DIGITA", "metaRobots": "noindex, nofollow",
        "extraCss": ["/assets/css/diagnostic.css"], "token": token, "state": state, "message": message,
    })


def cancel_booking_form(request):
    return _cancel_page(request, php.trim(request.query_params.get("token", "")), "confirm")


async def cancel_booking(request):
    form = await request.form()
    security.check_csrf(request, form)
    token = php.trim(form.get("token", ""))
    try:
        ok = bool(token) and await run_in_threadpool(ines.cancel_slot, token)
    except httpx.HTTPError as e:
        log.error("Annulation INES échouée : %s", e)
        return _cancel_page(request, token, "error", "L'annulation a échoué. Appelez-nous au 06 93 48 78 17.")
    if not ok:
        return _cancel_page(request, token, "error", "Ce rendez-vous est introuvable ou déjà annulé.")
    return _cancel_page(request, token, "done")
