"""Envoi d'e-mails (équivalent de app/Services/EmailService.php).

Le PHP utilisait mail() (sendmail d'OVH). Sur le VPS il n'y a pas de sendmail : l'envoi
passe par SMTP (variables MAIL_*). Sans configuration SMTP, l'e-mail est seulement journalisé
et l'appelant continue, comme mail() qui renvoie false sans lever d'erreur.
"""
import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from .. import php

log = logging.getLogger("digita.email")

FROM = "noreply@digita-marketing.com"
FROM_NAME = "Digita Marketing"


def send(to, subject, body, is_html=True):
    host = os.getenv("MAIL_HOST")
    if not host:
        log.warning("SMTP non configuré, e-mail non envoyé : %s → %s", subject, to)
        return False
    msg = EmailMessage()
    msg["From"] = formataddr((FROM_NAME, os.getenv("MAIL_FROM", FROM)))
    msg["Reply-To"] = os.getenv("MAIL_FROM", FROM)
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body, subtype="html" if is_html else "plain", charset="utf-8")
    try:
        with smtplib.SMTP(host, int(os.getenv("MAIL_PORT", "587")), timeout=15) as s:
            s.starttls()
            if os.getenv("MAIL_USERNAME"):
                s.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD", ""))
            s.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as e:
        log.error("Échec d'envoi à %s : %s", to, e)
        return False


def send_welcome(to, name):
    return send(to, "Bienvenue chez Digita Marketing", welcome_template(name))


def send_new_contact_notification(admin_email, data):
    return send(admin_email, "Nouveau message de contact", contact_notification_template(data))


def welcome_template(name):
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background: #f8f9fa; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h1>Bienvenue chez Digita Marketing !</h1>
                </div>
                <div class='content'>
                    <p>Bonjour {php.h(name)},</p>
                    <p>Merci de nous avoir contactés. Nous avons bien reçu votre message et nous vous répondrons dans les plus brefs délais.</p>
                    <p>Notre équipe est à votre disposition pour répondre à toutes vos questions.</p>
                    <p>Cordialement,<br>L'équipe Digita Marketing</p>
                </div>
                <div class='footer'>
                    <p>&copy; {php.date('Y')} Digita Marketing. Tous droits réservés.</p>
                </div>
            </div>
        </body>
        </html>
        """


def contact_notification_template(d):
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #667eea; color: white; padding: 20px; }}
                .content {{ padding: 20px; background: white; border: 1px solid #ddd; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #667eea; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h2>Nouveau message de contact</h2>
                </div>
                <div class='content'>
                    <div class='field'>
                        <span class='label'>Nom:</span> {php.h(d['name'])}
                    </div>
                    <div class='field'>
                        <span class='label'>Email:</span> {php.h(d['email'])}
                    </div>
                    <div class='field'>
                        <span class='label'>Téléphone:</span> {php.h(d.get('phone') if d.get('phone') is not None else 'Non renseigné')}
                    </div>
                    <div class='field'>
                        <span class='label'>Sujet:</span> {php.h(d['subject'])}
                    </div>
                    <div class='field'>
                        <span class='label'>Message:</span><br>
                        {php.nl2br(php.h(d['message']))}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
