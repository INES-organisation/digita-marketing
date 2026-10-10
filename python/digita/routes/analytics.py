"""Suivi des visites et conversions (AnalyticsController::trackPageView / trackConversion).

Le contrôleur PHP appelle requireAdmin() dans son constructeur : ces routes ne servent
qu'aux administrateurs connectés, les autres visiteurs sont redirigés.
"""
import re

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import config, db, php, security
from .common import redirect


def _json(payload):
    return Response(php.json_encode(payload), media_type="application/json")


def _require_admin(request):
    site = config.CONSTANTS["SITE_URL"]
    if "user_id" not in request.session:
        return redirect(site + "/connexion")
    if request.session.get("user_role") != "admin":
        return redirect(site + "/")
    return None


def _silent(sql, params):
    try:
        db.execute(sql, params)
    except Exception:  # noqa: BLE001 — « Silencieux » dans le PHP
        pass


async def pageview(request):
    denied = _require_admin(request)
    if denied:
        return denied
    form = await request.form()
    page_url = form.get("page_url") if "page_url" in form else request.headers.get("referer", "")
    referrer = form.get("referrer", "")
    session_id = form.get("session_id") if "session_id" in form else security.session_id(request)
    ua = request.headers.get("user-agent", "")
    device = "mobile" if re.search(r"Mobile|Android|iPhone", ua, re.I) else \
        "tablet" if re.search(r"Tablet|iPad", ua, re.I) else "desktop"
    browser = next((b for b in ("Chrome", "Firefox", "Safari", "Edge") if b in ua), "autre")
    q = request.query_params
    await run_in_threadpool(_silent,
        "INSERT INTO page_views (session_id, user_id, page_url, referrer, utm_source, utm_medium, utm_campaign, "
        "device_type, browser) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [session_id, request.session.get("user_id"), page_url, referrer,
         q.get("utm_source"), q.get("utm_medium"), q.get("utm_campaign"), device, browser])
    return _json({"success": True})


async def conversion(request):
    denied = _require_admin(request)
    if denied:
        return denied
    form = await request.form()
    event_type = form.get("event_type", "")
    if php.empty(event_type):
        return _json({"success": False})
    await run_in_threadpool(_silent,
        "INSERT INTO conversions (session_id, user_id, event_type, event_data, source, page_url, value) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [security.session_id(request), request.session.get("user_id"), event_type, form.get("event_data", "{}"),
         form.get("source", ""), form.get("page_url", ""), php.floatval(form.get("value", 0))])
    return _json({"success": True})
