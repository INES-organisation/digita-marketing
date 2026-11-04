"""« Se connecter avec INES » (connexion unique WAO) : client OpenID Connect minimal.

Même fichier dans DIGITA, MultiProShop et Tony Alpha ; seul le rapprochement avec les comptes
locaux est propre à chaque site. Flux « authorization code » + PKCE : le navigateur passe par
l'adresse publique d'INES, l'échange du code et la lecture du profil passent par le réseau
Docker interne (pas de vérification de signature nécessaire : réponse obtenue directement du
fournisseur, avec le secret du client — OIDC Core 3.1.3.7).

Variables : INES_OIDC_CLIENT_ID, INES_OIDC_CLIENT_SECRET (sans elles, aucun bouton),
INES_OIDC_ISSUER (public, défaut https://ines.weballone.com/api/oidc),
INES_API_URL (interne, défaut http://ines-backend:8000).
"""
import base64
import hashlib
import hmac
import os
import secrets
from urllib.parse import urlencode

import httpx

_KEY = "ines_sso"


class SSOError(Exception):
    """Message affichable tel quel à la personne."""


def enabled():
    return bool(os.getenv("INES_OIDC_CLIENT_ID") and os.getenv("INES_OIDC_CLIENT_SECRET"))


def _issuer():
    return os.getenv("INES_OIDC_ISSUER", "https://ines.weballone.com/api/oidc").rstrip("/")


def _backend():
    return os.getenv("INES_API_URL", "http://ines-backend:8000").rstrip("/") + "/api/oidc"


def authorize_url(session, redirect_uri, next_url=None):
    """Prépare la demande (état + PKCE gardés en session) et renvoie l'adresse INES."""
    state, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(48)
    session[_KEY] = {"state": state, "verifier": verifier, "redirect_uri": redirect_uri, "next": next_url}
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return _issuer() + "/authorize?" + urlencode({
        "client_id": os.getenv("INES_OIDC_CLIENT_ID"), "redirect_uri": redirect_uri, "response_type": "code",
        "scope": "openid email profile", "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})


def fetch_identity(session, args):
    """Au retour d'INES : vérifie l'état, échange le code, renvoie (profil, next_url).

    Le profil contient sub, email (vérifié), name, preferred_username."""
    pending = session.pop(_KEY, None)
    if args.get("error"):
        raise SSOError("Connexion avec INES annulée.")
    if not pending or not hmac.compare_digest(str(args.get("state", "")), pending["state"]) or not args.get("code"):
        raise SSOError("La connexion avec INES a expiré. Merci de réessayer.")
    auth = (os.getenv("INES_OIDC_CLIENT_ID", ""), os.getenv("INES_OIDC_CLIENT_SECRET", ""))
    try:
        r = httpx.post(_backend() + "/token", auth=auth, timeout=10, data={
            "grant_type": "authorization_code", "code": args["code"], "redirect_uri": pending["redirect_uri"],
            "code_verifier": pending["verifier"]})
        r.raise_for_status()
        r = httpx.get(_backend() + "/userinfo", timeout=10,
                      headers={"Authorization": "Bearer " + r.json()["access_token"]})
        r.raise_for_status()
        info = r.json()
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise SSOError("INES ne répond pas pour le moment. Merci de réessayer.") from e
    if not info.get("sub") or not info.get("email") or info.get("email_verified") is not True:
        raise SSOError("Votre adresse e-mail INES doit être vérifiée.")
    info["email"] = info["email"].strip().lower()
    return info, pending.get("next")
