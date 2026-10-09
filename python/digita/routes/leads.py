"""Demande d'audit stratégique (ContactController::submitAudit)."""
import logging

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import config, db, php
from ..services import email

log = logging.getLogger("digita.leads")


def _json(payload):
    return Response(php.json_encode(payload), media_type="application/json")


async def submit_audit(request):
    form = await request.form()
    name = form.get("name")
    mail = form.get("email")
    website = form.get("website", "Non précisé")

    if not php.t(name) or not php.t(mail):
        return _json({"success": False, "message": "Veuillez remplir les champs obligatoires."})
    # Base et SMTP sont bloquants : hors de la boucle asynchrone.
    return _json(await run_in_threadpool(_process, name, mail, website))


def _process(name, mail, website):
    try:
        subject = "Demande d'Audit Stratégique - " + name
        message = "Une nouvelle demande d'audit a été soumise.\n\n"
        message += "Nom : " + name + "\n"
        message += "Email : " + mail + "\n"
        message += "Site Web : " + website + "\n"
        db.execute("INSERT INTO contact_messages (name, email, phone, subject, message, status) "
                   "VALUES (?, ?, ?, ?, ?, ?)", [name, mail, "", subject, message, "new"])

        email.send_new_contact_notification(config.ADMIN_EMAIL, {
            "name": name, "email": mail, "subject": subject, "message": message, "phone": "N/A",
        })
        email.send_welcome(mail, name)

        return {"success": True,
                "message": "Votre demande a été prise en compte. Un consultant vous contactera prochainement."}
    except Exception as e:  # noqa: BLE001 — même comportement que le catch (Exception) PHP
        log.error("Erreur Audit Submission: %s", e)
        return {"success": False, "message": "Une erreur technique est survenue."}
