"""Formulaires de prospects : demande d'audit, contact, newsletter."""
import logging
import re

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


# Ordre : le plus parlant d'abord (titre de l'affaire dans le CRM INES).
AUDIT_DETAILS = {"pack": "Pack", "goal": "Objectif", "sector": "Secteur", "company": "Entreprise",
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

        # Pour l'agent INES : l'essentiel d'abord (titre de l'affaire dans le CRM), sans l'en-tête de l'e-mail admin.
        brief = "\n".join([f"{label} : {value}" for label, value in details.items() if value and label != "Téléphone"]
                          + ([f"Site : {website}"] if website != "Non précisé" else [])) or "Demande de diagnostic"
        ines.push_lead(name, mail, "diagnostic", brief, phone or None, outreach=True, outreach_email=False,
                       tags=(f"pack:{details['Pack']}",) if details.get("Pack") else ())
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


# Démarchage reçu le 02/11/2026 (« ranking is not good on Google… SEO Packages… Can I send? ») : il a
# déclenché le premier contact, une affaire et un devis brouillon. Formules des offres non sollicitées
# (SEO, liens, refonte, sous-traitance), en anglais surtout.
PITCH_RX = re.compile(
    r"\b(seo (packages?|services?|strateg\w*|expert)|rank(ing)? (is not|on|your|higher)|first page of google"
    r"|page (1|one) of google|back ?links?|guest post|can i send|link building|web ?traffic|more traffic"
    r"|redesign (of )?your (web)?site|white ?label|outsourc\w*|virtual assistant|i checked your website)\b", re.I)
MIN_FILL_SECONDS = 3


def spam_reason(form, d, session):
    """Raison de classer le message en spam, ou None. « robot » : piège rempli, le message n'ira pas
    plus loin que la base. Les autres : enregistré et signalé, sans réponse automatique ni affaire."""
    if php.trim(form.get("site_web", "")):
        return "robot"
    shown = session.pop("contact_form_at", None)
    if shown is not None and php.time() - shown < MIN_FILL_SECONDS:
        return f"envoyé {php.time() - shown} s après l'ouverture de la page"
    if m := PITCH_RX.search(d["message"]):
        return f"démarchage (« {m.group(0)} »)"
    if len(re.findall(r"https?://", d["message"])) > 2:
        return "plus de 2 liens"
    return None


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

    # Même réponse au visiteur : un robot ou un démarcheur ne doit pas savoir qu'il a été repéré.
    ok = await run_in_threadpool(_save_contact, data, spam_reason(form, data, request.session))
    request.session["contact_flash"] = {"ok": ok, "message": (
        "Merci, votre message a bien été envoyé. Nous vous répondons sous 48 h." if ok
        else "Une erreur technique est survenue. Merci de réessayer ou d'utiliser le chat.")}
    return redirect("/contact#formulaire")


def _save_contact(d, spam=None):
    service = SERVICES.get(d["service"], d["service"] or "Non précisé")
    subject = ("[Spam ?] " if spam else "") + "Contact site - " + service
    message = (f"Organisation : {d['entreprise'] or 'Non précisée'}\nExpertise : {service}\n\n{d['message']}"
               + (f"\n\nClassé spam : {spam}" if spam else ""))
    try:
        db.execute("INSERT INTO contact_messages (name, email, phone, subject, message, status) "
                   "VALUES (?, ?, ?, ?, ?, ?)", [d["nom"][:100], d["email"][:100], d["telephone"][:20],
                                                 subject[:200], message, "new"])
    except Exception as e:  # noqa: BLE001
        log.error("Erreur formulaire contact : %s", e)
        return False
    if spam == "robot":
        return True
    # Pour l'agent INES : le message du prospect d'abord (il sert de titre à l'affaire dans le CRM).
    brief = "\n".join(x for x in (d["message"], f"Expertise : {service}",
                                   f"Organisation : {d['entreprise']}" if d["entreprise"] else "") if x)
    if spam:  # fiche CRM simple, signalée : ni premier contact, ni affaire, ni devis brouillon
        ines.push_lead(d["nom"], d["email"], "contact", f"{brief}\nClassé spam : {spam}", d["telephone"],
                       tags=("spam?", service))
    else:
        ines.push_lead(d["nom"], d["email"], "contact", brief, d["telephone"], outreach=True, tags=(service,))
    try:
        email.send_new_contact_notification(config.ADMIN_EMAIL, {
            "name": d["nom"], "email": d["email"], "subject": subject, "message": message,
            "phone": d["telephone"] or "N/A",
        })
    except Exception as e:  # noqa: BLE001 — le message est enregistré, l'e-mail est secondaire
        log.warning("Notification contact non envoyée : %s", e)
    return True


# ---------------------------------------------------------------- liste d'attente de la boutique
WAITLIST_INTERESTS = {"prompts": "Packs de prompts", "workflows": "Automatisations IA", "materiel": "Matériel", "tout": "Tout"}


async def boutique_waitlist(request):
    """« Me prévenir » de /boutique (ouverture prochaine) : enregistré dans les messages de contact et
    copié dans INES avec l'étiquette « liste-attente-boutique », pour l'e-mail d'ouverture."""
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "contact")
    mail = php.trim(form.get("email", "")).lower()
    interest = WAITLIST_INTERESTS.get(form.get("interest", ""), "Tout")
    if not security.valid_email(mail) or len(mail) > 100 or not form.get("consent"):
        request.session["waitlist_flash"] = {"ok": False, "message": "Merci d'indiquer une adresse e-mail valide et de cocher la case."}
        return redirect("/boutique#prevenir")
    if not php.trim(form.get("site_web", "")):  # piège à robots : rien n'est enregistré, même réponse
        await run_in_threadpool(_save_waitlist, mail, interest)
    request.session["waitlist_flash"] = {"ok": True, "message": "C'est noté : vous serez prévenu par e-mail dès l'ouverture de la boutique."}
    return redirect("/boutique#prevenir")


def _save_waitlist(mail, interest):
    try:
        db.execute("INSERT INTO contact_messages (name, email, phone, subject, message, status) VALUES (?, ?, ?, ?, ?, ?)",
                   [mail[:100], mail, "", "Liste d'attente boutique", f"Intérêt : {interest}", "new"])
    except Exception as e:  # noqa: BLE001
        log.error("Liste d'attente boutique non enregistrée : %s", e)
    ines.push_lead(mail, mail, "boutique", f"Liste d'attente de la boutique. Intérêt : {interest}",
                   tags=("liste-attente-boutique", interest))


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
