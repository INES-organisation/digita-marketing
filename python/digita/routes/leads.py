"""Formulaires de prospects : demande d'audit, contact, newsletter."""
import logging

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import config, db, php, security
from ..services import email, ines
from .common import redirect

log = logging.getLogger("digita.leads")


def _json(payload):
    return Response(php.json_encode(payload), media_type="application/json")


AUDIT_DETAILS = {"company": "Entreprise", "sector": "Secteur", "goal": "Objectif", "phone": "Téléphone"}


async def submit_audit(request):
    form = await request.form()
    name = form.get("name")
    mail = form.get("email")
    website = form.get("website") or "Non précisé"
    # Champs facultatifs des formulaires de diagnostic (accueil, /diagnostic) : qualifient le prospect.
    details = {label: php.trim(form.get(key) or "") for key, label in AUDIT_DETAILS.items()}

    if not php.t(name) or not php.t(mail):
        return _json({"success": False, "message": "Veuillez remplir les champs obligatoires."})
    # Base et SMTP sont bloquants : hors de la boucle asynchrone.
    return _json(await run_in_threadpool(_process, name, mail, website, details))


def _process(name, mail, website, details=None):
    try:
        subject = "Demande d'Audit Stratégique - " + name
        message = "Une nouvelle demande d'audit a été soumise.\n\n"
        message += "Nom : " + name + "\n"
        message += "Email : " + mail + "\n"
        message += "Site Web : " + website + "\n"
        for label, value in (details or {}).items():
            if value:
                message += label + " : " + value + "\n"
        db.execute("INSERT INTO contact_messages (name, email, phone, subject, message, status) "
                   "VALUES (?, ?, ?, ?, ?, ?)", [name, mail, (details or {}).get("Téléphone", ""), subject, message, "new"])
        ines.push_lead(name, mail, "audit", message)

        email.send_new_contact_notification(config.ADMIN_EMAIL, {
            "name": name, "email": mail, "subject": subject, "message": message, "phone": "N/A",
        })
        email.send_diagnostic_confirmation(mail, name)

        return {"success": True,
                "message": "Votre demande a été prise en compte. Un consultant vous contactera prochainement."}
    except Exception as e:  # noqa: BLE001 — même comportement que le catch (Exception) PHP
        log.error("Erreur Audit Submission: %s", e)
        return {"success": False, "message": "Une erreur technique est survenue."}


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
