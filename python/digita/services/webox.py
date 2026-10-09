"""Client de l'API Webox (WeboxBridge.php) : santé du service et lancement d'une génération."""
import json
import logging
import os

import httpx

from .. import config

log = logging.getLogger("digita")


class WeboxError(Exception):
    pass


def _base():
    return os.getenv("WEBOX_API_URL", "http://localhost:8000").rstrip("/")


def _request(method, endpoint, data=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    key = os.getenv("WEBOX_API_KEY", "")
    if key:
        headers["Authorization"] = "Bearer " + key
    try:
        r = httpx.request(method, _base() + endpoint, headers=headers,
                          content=json.dumps(data) if data else None,
                          timeout=httpx.Timeout(30, connect=10))
    except httpx.HTTPError as exc:
        log.error("WeboxBridge cURL error: %s", exc)
        raise WeboxError(f"Erreur de connexion à Webox: {exc}") from exc
    try:
        decoded = r.json()
    except ValueError:
        decoded = None
    if r.status_code >= 400:
        detail = decoded if isinstance(decoded, dict) else {}
        msg = detail.get("detail") or detail.get("error") or f"Erreur HTTP {r.status_code}"
        log.error("WeboxBridge API error (%s): %s", r.status_code, msg)
        raise WeboxError(f"Erreur API Webox: {msg}")
    return decoded


def health_check():
    try:
        resp = _request("GET", "/health")
    except WeboxError:
        return False
    return isinstance(resp, dict) and resp.get("status") == "ok"


def create_website(brief):
    payload = {
        "project_type": brief.get("project_type", "website"),
        "business_name": brief.get("business_name", ""),
        "business_type": brief.get("business_type", ""),
        "description": brief.get("description", ""),
        "target_audience": brief.get("target_audience", ""),
        "style": brief.get("style", "modern"),
        "colors": brief.get("colors", []),
        "pages": brief.get("pages", ["accueil", "a-propos", "services", "contact"]),
        "features": brief.get("features", []),
        "content_tone": brief.get("content_tone", "professionnel"),
        "language": brief.get("language", "fr"),
        "callback_url": brief.get("callback_url", config.APP_URL.rstrip("/") + "/webhook/webox"),
    }
    return _request("POST", "/digita/website/create", payload)
