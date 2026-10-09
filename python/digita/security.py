"""Équivalents de CsrfMiddleware::check() et RateLimitMiddleware::check()."""
import hashlib
import secrets
import re

from starlette.responses import Response

from . import csrf, php

LIMITS = {
    "login": (5, 900), "register": (3, 3600), "contact": (10, 3600),
    "api": (100, 60), "default": (60, 60),
}


class Abort(Exception):
    """Interrompt le traitement avec une réponse (équivalent d'un die() PHP)."""

    def __init__(self, response):
        self.response = response


def _die(status, payload, headers=None):
    # die(json_encode(...)) en PHP : type de contenu HTML par défaut.
    return Abort(Response(php.json_encode(payload), status_code=status,
                          media_type="text/html", headers=headers))


def check_csrf(request, form):
    token = form.get(csrf.TOKEN_NAME) or request.headers.get("x-csrf-token")
    if not token or not csrf.validate(request.session, token):
        raise _die(403, {"error": "Token CSRF invalide ou manquant", "code": "CSRF_TOKEN_INVALID"})


def _identifier(request):
    # md5(REMOTE_ADDR . HTTP_USER_AGENT). Derrière nginx, uvicorn --proxy-headers
    # place l'IP du visiteur dans request.client.
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    return hashlib.md5((ip + ua).encode()).hexdigest()


def check_rate(request, action="default"):
    max_, window = LIMITS.get(action, LIMITS["default"])
    key = f"rate_limit_{action}_{_identifier(request)}"
    now = php.time()
    attempts = [t for t in request.session.get(key, []) if now - t < window]
    if len(attempts) >= max_:
        retry = window - (now - min(attempts))
        raise _die(429, {"error": "Trop de tentatives. Veuillez réessayer plus tard.",
                         "retry_after": retry, "code": "RATE_LIMIT_EXCEEDED"},
                   {"Retry-After": str(retry)})
    attempts.append(now)
    request.session[key] = attempts


def reset_rate(request, action="default"):
    request.session.pop(f"rate_limit_{action}_{_identifier(request)}", None)


EMAIL_RX = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")


def valid_email(s):
    return bool(EMAIL_RX.match(s or "")) and ".." not in s and not s.startswith(".")


def session_id(request):
    """Équivalent de session_id() : identifiant stable de la session du visiteur."""
    sid = request.session.get("_sid")
    if not sid:
        sid = request.session["_sid"] = secrets.token_hex(16)
    return sid


def remote_addr(request):
    return request.client.host if request.client else ""
