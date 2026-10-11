"""Anciennes tâches cron du PHP (scripts/cron/*.php), désormais déclenchées par INES.

INES est le seul planificateur (backend/app/project_cron_beat.py : PROJECT_CRON_JOBS) : il appelle
POST /internal/cron/<tâche> avec `Authorization: Bearer PROJECT_CRON_TOKEN`. La sauvegarde de la
base est faite directement par INES (PROJECT_BACKUP_DATABASES). Le sitemap n'a plus besoin de cron :
il est calculé à chaque demande. Vider le cache et OPTIMIZE TABLE (MySQL) n'ont pas d'équivalent
utile ici (pas de cache fichier, autovacuum PostgreSQL) et sont abandonnés.
"""
import hashlib
import hmac
import os
import urllib.parse

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import config, db, php
from ..models import article as Article
from ..models import formation as Formation
from ..services import email


def _json(payload, status=200):
    return Response(php.json_encode(payload), status_code=status, media_type="application/json")


def _token():
    return os.getenv("PROJECT_CRON_TOKEN", "")


def _authorized(request):
    return bool(_token()) and hmac.compare_digest(request.headers.get("authorization", ""), "Bearer " + _token())


def _cron(job):
    async def handler(request):
        if not _authorized(request):
            return _json({"error": "forbidden"}, 403)
        return _json(await run_in_threadpool(job))
    return handler


# ---------------------------------------------------------------- newsletter (lundi 10h)
def unsubscribe_sig(mail):
    return hmac.new(_token().encode(), mail.lower().encode(), hashlib.sha256).hexdigest()[:32]


def newsletter_html(articles, formations, unsubscribe_url):
    base = config.APP_URL.rstrip("/")
    def card(title, text, url, label):
        return (f"<div class='article'><h3>{php.h(title)}</h3><p>{php.h((text or '')[:150])}...</p>"
                f"<a href='{base}{url}'>{label} →</a></div>")
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
.container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
.header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
.content {{ padding: 20px; background: #f9fafb; }}
.article {{ margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px; }}
.footer {{ text-align: center; padding: 20px; font-size: 12px; color: #6b7280; }}
a {{ color: #2563eb; text-decoration: none; }}
</style></head><body><div class="container">
<div class="header"><h1>Newsletter Digita Marketing</h1><p>{php.date('d/m/Y')}</p></div>
<div class="content"><h2>📚 Derniers Articles</h2>
{''.join(card(a['title'], a.get('excerpt'), '/blog/' + a['slug'], 'Lire la suite') for a in articles)}
<h2>🎓 Nouvelles Formations</h2>
{''.join(card(f['title'], php.strip_tags(f.get('description') or ''), '/formations/' + f['slug'], 'Découvrir') for f in formations)}
</div><div class="footer"><p>Vous recevez cet email car vous êtes abonné à notre newsletter.</p>
<p><a href="{php.h(unsubscribe_url)}">Se désabonner</a></p></div></div></body></html>"""


def send_newsletter():
    subscribers = db.fetch_all("SELECT email FROM newsletters WHERE status = 'active' ORDER BY id")
    if not subscribers:
        return {"sent": 0, "failed": 0}
    articles, formations = Article.get_all_published(5), Formation.get_all_published(3)
    subject = "Newsletter Digita Marketing - " + php.date("d/m/Y")
    sent = 0
    for s in subscribers:
        url = (config.APP_URL.rstrip("/") + "/newsletter/unsubscribe?"
               + urllib.parse.urlencode({"email": s["email"], "sig": unsubscribe_sig(s["email"])}))
        sent += bool(email.send(s["email"], subject, newsletter_html(articles, formations, url)))
    return {"sent": sent, "failed": len(subscribers) - sent}


async def unsubscribe(request):
    mail = request.query_params.get("email", "")
    sig = request.query_params.get("sig", "")
    ok = bool(mail and _token()) and hmac.compare_digest(sig, unsubscribe_sig(mail))
    if ok:
        await run_in_threadpool(db.execute, "UPDATE newsletters SET status = 'inactive' WHERE LOWER(email) = ?",
                                [mail.lower()])
    msg = "Vous êtes désabonné de la newsletter Digita Marketing." if ok else "Lien de désabonnement invalide."
    return Response(f"<!DOCTYPE html><meta charset='utf-8'><p style='font-family:Arial;text-align:center;"
                    f"margin-top:15vh'>{msg}</p><p style='text-align:center'><a href='/'>Retour au site</a></p>",
                    status_code=200 if ok else 400, media_type="text/html")


# ---------------------------------------------------------------- séquences après achat (9h)
def sequence_html(title, body):
    return f"""<!DOCTYPE html><html><head><style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
.container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
.content {{ padding: 30px; background: #f8f9fa; }}
.footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
</style></head><body><div class='container'>
<div class='header'><h1>{php.h(title)}</h1></div>
<div class='content'>{php.nl2br(php.h(body))}</div>
<div class='footer'><p>&copy; {php.date('Y')} Digita Marketing. Tous droits réservés.</p>
<p><a href='{config.APP_URL}'>{config.APP_URL.split('//')[-1]}</a></p></div></div></body></html>"""


def process_email_sequences():
    """EmailService::processEmailSequences : commandes payées il y a `delay_days` jours, une seule fois
    par commande et séquence (email_logs.subject finit par « #id_commande »)."""
    sent = failed = 0
    for seq in db.fetch_all("SELECT * FROM email_sequences WHERE CAST(is_active AS int) = 1 AND trigger_event = 'purchase'"):
        orders = db.fetch_all(
            """SELECT o.id, o.user_id, u.email, u.username,
                      (SELECT string_agg(oi.product_name, ', ' ORDER BY oi.id) FROM order_items oi
                        WHERE oi.order_id = o.id) AS items_summary
               FROM orders o JOIN users u ON o.user_id = u.id
               WHERE o.status = 'paid' AND CAST(o.updated_at AS date) = CURRENT_DATE - CAST(? AS int)
                 AND NOT EXISTS (SELECT 1 FROM email_logs el WHERE el.sequence_id = ?
                                 AND el.subject LIKE '%#' || CAST(o.id AS text))""",
            [int(seq["delay_days"] or 0), seq["id"]])
        for o in orders:
            formation = o.get("items_summary") or "votre formation"
            subject = seq["subject"].replace("{formation}", formation)
            body = seq["body"].replace("{username}", o.get("username") or "Apprenant").replace("{formation}", formation)
            ok = email.send(o["email"], subject, sequence_html(subject, body))
            db.execute("INSERT INTO email_logs (user_id, sequence_id, email_to, subject, status) VALUES (?, ?, ?, ?, ?)",
                       [o["user_id"], seq["id"], o["email"], f"{subject} #{o['id']}", "sent" if ok else "failed"])
            sent, failed = sent + ok, failed + (not ok)
    return {"sent": sent, "failed": failed}


newsletter = _cron(send_newsletter)
email_sequences = _cron(process_email_sequences)


# ---------------------------------------------------------------- sitemap (était généré à 4h)
STATIC_PAGES = [("/", "1.0", "daily"), ("/services", "0.9", "weekly"), ("/formations", "0.9", "daily"),
                ("/blog", "0.9", "daily"), ("/boutique", "0.8", "weekly"), ("/solutions", "0.8", "weekly"),
                ("/catalogue", "0.8", "weekly"), ("/tarifs", "0.8", "monthly"), ("/a-propos", "0.7", "monthly"),
                ("/contact", "0.8", "monthly"), ("/mentions-legales", "0.3", "yearly"),
                ("/politique-confidentialite", "0.3", "yearly"), ("/conditions-generales", "0.3", "yearly")]


def sitemap_xml():
    base, today = config.APP_URL.rstrip("/"), php.date("Y-m-d")
    urls = [(p, prio, freq, today) for p, prio, freq in STATIC_PAGES]
    urls += [("/blog/" + a["slug"], "0.7", "weekly", str(a.get("updated_at") or today)[:10])
             for a in Article.get_all_published()]
    urls += [("/blog/categorie/" + c["slug"], "0.6", "weekly", today) for c in Article.get_categories()]
    urls += [("/formations/" + f["slug"], "0.8", "weekly", str(f.get("updated_at") or f.get("created_at") or today)[:10])
             for f in Formation.get_all_published()]
    urls += [("/formations/categorie/" + c["slug"], "0.6", "weekly", today) for c in Formation.get_categories()]
    body = "".join(f"<url><loc>{php.h(base + p)}</loc><changefreq>{freq}</changefreq><priority>{prio}</priority>"
                   f"<lastmod>{mod}</lastmod></url>" for p, prio, freq, mod in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')


async def sitemap(request):
    return Response(await run_in_threadpool(sitemap_xml), media_type="application/xml")
