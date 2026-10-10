"""Pont vers INES : leads vers son CRM, IA via sa passerelle (même réseau Docker que ines-backend).

Sans INES_API_KEY, rien n'est envoyé : le site garde son comportement d'origine (base locale seule)."""
import logging
import os
import threading

import httpx

log = logging.getLogger("digita.ines")


def _url(path):
    return os.getenv("INES_API_URL", "http://ines-backend:8000").rstrip("/") + path


def _headers():
    return {"Authorization": "Bearer " + os.getenv("INES_API_KEY", "")}


def enabled():
    return bool(os.getenv("INES_API_KEY"))


def push_lead(name, email, source, notes="", phone=None):
    """Copie un lead dans le CRM INES, en arrière-plan : la base locale reste la référence et une
    panne d'INES ne bloque jamais le formulaire."""
    if not enabled() or not email:
        return
    payload = {"name": name or email, "email": email, "phone": phone or None, "category": "Lead DIGITA",
               "tags": ["DIGITA", source], "notes": notes or None}
    threading.Thread(target=_post_lead, args=(payload,), daemon=True).start()


def _post_lead(payload):
    try:
        httpx.post(_url("/api/v1/contacts/ingest"), json=payload, headers=_headers(), timeout=10).raise_for_status()
    except httpx.HTTPError as e:
        log.warning("Lead non transmis à INES (%s) : %s", payload["tags"][1], e)


def generate(messages, system=None, temperature=0.7, max_tokens=500):
    """Texte généré par la passerelle IA d'INES (POST /api/v1/generate). Lève httpx.HTTPError."""
    body = {"messages": messages, "system": system, "temperature": temperature, "max_tokens": max_tokens,
            # Le cache INES ne regarde que `prompt` : sans no_cache deux conversations différentes
            # recevraient la même réponse.
            "no_cache": True}
    if os.getenv("INES_AI_MODEL"):
        body["model"] = os.getenv("INES_AI_MODEL")
    r = httpx.post(_url("/api/v1/generate"), json=body, headers=_headers(), timeout=60)
    r.raise_for_status()
    return r.json().get("text") or ""
