"""Envoi d'e-mails (équivalent de app/Services/EmailService.php).

Plus de SMTP propre à Digita : l'envoi passe par INES (même fournisseur et même compte que les
e-mails d'INES). Sans INES_API_KEY, l'e-mail est seulement journalisé et l'appelant continue, comme
mail() qui renvoie false sans lever d'erreur. MAIL_FROM (facultatif) : expéditeur, à déclarer chez
le fournisseur d'INES ; sinon l'adresse par défaut d'INES avec le nom « Digita Marketing ».
"""
import logging
import os

from .. import config, php
from . import ines

log = logging.getLogger("digita.email")

FROM_NAME = "DIGITA"
GOLD, INK, MUTED, LINE, BG = "#B8912E", "#14161c", "#5b6070", "#e7e3d8", "#f5f3ee"


def send(to, subject, body, template=None):
    """`template` : libellé de l'envoi dans le journal d'INES (Communications › Journal)."""
    if not ines.enabled():
        log.warning("INES non configuré, e-mail non envoyé : %s → %s", subject, to)
        return False
    return ines.send_email(to, subject, body, FROM_NAME, os.getenv("MAIL_FROM") or None, template=template)


# ---------------------------------------------------------------- mise en page commune
# Tableaux et styles en ligne : seule forme rendue pareil dans Gmail, Outlook et Apple Mail.
def _base():
    return config.APP_URL.rstrip("/")


def p(text_html):
    return f'<p style="margin:0 0 16px;font-size:15px;line-height:1.7;color:{MUTED};">{text_html}</p>'


def box(inner_html, accent=False):
    border = GOLD if accent else LINE
    return (f'<div style="margin:0 0 20px;padding:18px 22px;background:{BG};border:1px solid {border};'
            f'border-radius:10px;font-size:15px;line-height:1.7;color:{INK};">{inner_html}</div>')


def button(label, url):
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 24px;"><tr>'
            f'<td style="background:{INK};border-radius:8px;">'
            f'<a href="{php.h(url)}" style="display:inline-block;padding:14px 28px;font-size:15px;font-weight:600;'
            f'color:#ffffff;text-decoration:none;border-bottom:3px solid {GOLD};border-radius:8px;">{label}</a>'
            f'</td></tr></table>')


def layout(title, content_html, preheader="", unsubscribe_url=None):
    base = _base()
    unsub = (f'<br><a href="{php.h(unsubscribe_url)}" style="color:{MUTED};">Se désabonner</a>'
             if unsubscribe_url else "")
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{php.h(title)}</title></head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;">{php.h(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 16px;"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid {LINE};">
<tr><td style="padding:26px 32px 22px;border-bottom:3px solid {GOLD};">
<a href="{base}"><img src="{base}/assets/images/email/logo-email.png" width="200" alt="DIGITA" style="display:block;border:0;width:200px;height:auto;"></a>
</td></tr>
<tr><td style="padding:34px 32px 14px;">
<h1 style="margin:0 0 18px;font-size:22px;line-height:1.35;font-weight:700;color:{INK};">{php.h(title)}</h1>
{content_html}
</td></tr>
<tr><td style="padding:20px 32px;background:{BG};border-top:1px solid {LINE};font-size:12px;line-height:1.7;color:{MUTED};">
<strong style="color:{INK};">DIGITA</strong> · Stratégie, automatisation et marketing · La Réunion<br>
06 93 48 78 17 · <a href="{base}" style="color:{GOLD};text-decoration:none;">digita.buzz</a> ·
<a href="{base}/mentions-legales" style="color:{MUTED};">Mentions légales</a>{unsub}
</td></tr>
</table>
<p style="margin:16px 0 0;font-size:11px;color:#9a9eaa;">© {php.date('Y')} DIGITA. Tous droits réservés.</p>
</td></tr></table>
</body></html>"""


def signature():
    return p("À très vite,<br><strong style=\"color:%s;\">L'équipe DIGITA</strong>" % INK)


# ---------------------------------------------------------------- e-mails
def send_diagnostic_confirmation(to, name):
    """Réponse automatique immédiate à une demande de diagnostic (accueil, /diagnostic, fenêtre des pages)."""
    return send(to, "Votre diagnostic gratuit DIGITA : demande bien reçue", diagnostic_confirmation_template(name),
                template="diagnostic")


def send_booking_confirmation(to, name, when, cancel_url):
    """Confirmation d'un rendez-vous réservé dans INES Booking, avec son lien d'annulation."""
    return send(to, f"Rendez-vous confirmé : diagnostic DIGITA le {when}",
                booking_confirmation_template(name, when, cancel_url), template="rendez-vous")


def send_new_contact_notification(admin_email, data):
    return send(admin_email, "Nouveau message de contact", contact_notification_template(data), template="contact-admin")


def diagnostic_confirmation_template(name):
    base = _base()
    steps = "".join(
        f'<tr><td style="vertical-align:top;padding:6px 12px 6px 0;font-weight:700;color:{GOLD};">{i}</td>'
        f'<td style="padding:6px 0;color:{INK};">{t}</td></tr>'
        for i, t in enumerate([
            "Un consultant vous rappelle <strong>sous 24 h ouvrées</strong> pour fixer votre créneau de 30 minutes.",
            "Ensemble, nous regardons votre visibilité, le suivi de vos prospects et ce qui peut être automatisé.",
            "Vous repartez avec un plan d'action concret et priorisé, sans engagement.",
        ], 1))
    content = (p(f"Bonjour {php.h(name)},")
               + p("Merci pour votre demande de diagnostic gratuit. Voici la suite :")
               + box(f'<table role="presentation" cellpadding="0" cellspacing="0">{steps}</table>')
               + p("Sans attendre, vous pouvez lancer l'audit SEO automatique de votre site :")
               + button("Lancer l'audit SEO gratuit", f"{base}/outils/audit-seo")
               + p("Vous préférez appeler ? <strong>06 93 48 78 17</strong>.")
               + signature())
    return layout("Demande bien reçue", content, "Un consultant vous rappelle sous 24 h ouvrées.")


def booking_confirmation_template(name, when, cancel_url):
    base = _base()
    content = (p(f"Bonjour {php.h(name)},")
               + p("Votre diagnostic gratuit de 30 minutes avec un consultant DIGITA est réservé :")
               + box(f'<div style="text-align:center;font-size:18px;font-weight:700;">{php.h(when)}</div>'
                     f'<div style="text-align:center;font-size:13px;color:{MUTED};">heure de La Réunion</div>', accent=True)
               + p("Le consultant vous appelle à l'heure prévue au numéro que vous avez indiqué. Pour en tirer le "
                   "meilleur, notez vos priorités : trouver des clients, suivre vos devis, gagner du temps.")
               + p(f'Un empêchement ? <a href="{php.h(cancel_url)}" style="color:{GOLD};">Annuler ce rendez-vous</a>, '
                   f'puis réservez un autre créneau sur <a href="{base}/diagnostic" style="color:{GOLD};">digita.buzz/diagnostic</a>.')
               + p("Une question : <strong>06 93 48 78 17</strong>.")
               + signature())
    return layout("Rendez-vous confirmé", content, f"Votre diagnostic DIGITA : {when}.")


def contact_notification_template(d):
    def row(label, value):
        return (f'<tr><td style="padding:8px 12px 8px 0;vertical-align:top;font-size:13px;font-weight:600;color:{MUTED};'
                f'white-space:nowrap;">{label}</td><td style="padding:8px 0;font-size:15px;color:{INK};">{value}</td></tr>')
    phone = d.get("phone") if d.get("phone") is not None else "Non renseigné"
    content = (p("Un visiteur vient d'écrire depuis le site :")
               + box('<table role="presentation" cellpadding="0" cellspacing="0" width="100%">'
                     + row("Nom", php.h(d["name"]))
                     + row("E-mail", f'<a href="mailto:{php.h(d["email"])}" style="color:{GOLD};">{php.h(d["email"])}</a>')
                     + row("Téléphone", php.h(phone))
                     + row("Sujet", php.h(d["subject"]))
                     + "</table>")
               + box(php.nl2br(php.h(d["message"]))))
    return layout("Nouveau message de contact", content, f"{d['name']} : {d['subject']}")


def send_order_confirmation(to, order_id):
    return send(to, f"Confirmation de commande #{order_id}", order_confirmation_template(order_id), template="commande")


def order_confirmation_template(order_id):
    base = _base()
    content = (p(f"Votre commande <strong style=\"color:{INK};\">#{php.h(order_id)}</strong> est confirmée.")
               + p("Votre formation est dès maintenant accessible depuis votre espace apprenant.")
               + button("Accéder à mes formations", f"{base}/mes-formations")
               + p("Votre facture est disponible dans votre espace commandes.")
               + p("Merci pour votre confiance !") + signature())
    return layout("Commande confirmée", content, "Votre formation est accessible dès maintenant.")
