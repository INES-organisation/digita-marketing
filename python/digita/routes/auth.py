"""Connexion / inscription (AuthController.php) et mot de passe oublié."""
import hashlib
import secrets

import bcrypt
from starlette.concurrency import run_in_threadpool

from .. import config, db, php, security
from ..services import email, ines, ines_sso
from ..render import render_view
from .common import redirect


def _authenticated(request):
    return "user_id" in request.session


def show_login(request):
    if _authenticated(request):
        return redirect("/admin/dashboard")
    resp = render_view(request, "auth/login", {
        "title": "Connexion | DIGITA", "metaRobots": "noindex, follow",
        "error": request.session.get("login_error"),
        "success": request.session.get("login_success"),
        "inesSso": ines_sso.enabled(),
    })
    request.session.pop("login_error", None)
    request.session.pop("login_success", None)
    return resp


def show_register(request):
    if _authenticated(request):
        return redirect("/admin/dashboard")
    resp = render_view(request, "auth/register", {
        "title": "Inscription | DIGITA", "metaRobots": "noindex, follow",
        "error": request.session.get("register_error"),
        "inesSso": ines_sso.enabled(),
    })
    request.session.pop("register_error", None)
    return resp


# ---------------------------------------------------------------- traitement des formulaires
def _hash(password):
    # password_hash(PASSWORD_DEFAULT) : bcrypt coût 10, préfixe $2y$ pour rester lisible par PHP.
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt(10)).decode().replace("$2b$", "$2y$", 1)


def _verify(password, stored):
    try:
        return bcrypt.checkpw(password.encode()[:72], stored.replace("$2y$", "$2b$", 1).encode())
    except (ValueError, TypeError):
        return False


def _find_user(mail):
    # MySQL (collation *_ci) compare les e-mails sans tenir compte de la casse.
    return db.fetch("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", [mail])


def _create_user(mail, password):
    db.execute("INSERT INTO users (email, password, role) VALUES (?, ?, ?)", [mail, _hash(password), "user"])
    ines.push_lead(mail, mail, "inscription", "Compte créé sur digita.buzz")
    return _find_user(mail)


def _login_session(request, user):
    request.session["user_id"] = user["id"]
    request.session["user_email"] = user["email"]
    request.session["user_role"] = user.get("role") or "user"


async def login(request):
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "login")

    mail = php.trim(form.get("email", ""))
    password = form.get("password", "")
    if php.empty(mail) or php.empty(password):
        request.session["login_error"] = "Tous les champs sont obligatoires."
        return redirect("/connexion")

    user = await run_in_threadpool(_find_user, mail)
    if user and await run_in_threadpool(_verify, password, user["password"]):
        _login_session(request, user)
        security.reset_rate(request, "login")
        return redirect("/admin/dashboard")
    request.session["login_error"] = "Identifiants incorrects."
    return redirect("/connexion")


async def register(request):
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "register")

    mail = php.trim(form.get("email", ""))
    password = form.get("password", "")
    password2 = form.get("password2", "")

    error = None
    if php.empty(mail) or php.empty(password) or php.empty(password2):
        error = "Tous les champs sont obligatoires."
    elif not security.valid_email(mail):
        error = "Adresse email invalide."
    elif password != password2:
        error = "Les mots de passe ne correspondent pas."
    elif php.strlen(password) < 8:
        error = "Le mot de passe doit contenir au moins 8 caractères."
    elif await run_in_threadpool(_find_user, mail):
        error = "Cet email est déjà utilisé."
    if error:
        request.session["register_error"] = error
        return redirect("/inscription")

    _login_session(request, await run_in_threadpool(_create_user, mail, password))
    return redirect("/admin/dashboard")


# ---------------------------------------------------------------- « Se connecter avec INES »
# Connexion unique WAO (04/11/2026). Compte retrouvé par son identifiant INES, sinon lié par e-mail
# (INES ne transmet que des e-mails vérifiés), sinon créé sans mot de passe utilisable.
_sso_ready = False


def _ensure_sso_column():
    global _sso_ready
    if not _sso_ready:
        db.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS ines_sub VARCHAR(64)")
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_ines_sub_key ON users (ines_sub)")
        _sso_ready = True


def _user_from_ines(info):
    _ensure_sso_column()
    user = db.fetch("SELECT * FROM users WHERE ines_sub = ?", [info["sub"]])
    if user:
        return user
    user = _find_user(info["email"])
    if user:
        db.execute("UPDATE users SET ines_sub = ? WHERE id = ?", [info["sub"], user["id"]])
        return user
    db.execute("INSERT INTO users (email, password, role, ines_sub) VALUES (?, ?, ?, ?)",
               [info["email"], _hash(secrets.token_urlsafe(32)), "user", info["sub"]])
    ines.push_lead(info.get("name") or info["email"], info["email"], "inscription", "Compte créé via INES (compte WAO)")
    return _find_user(info["email"])


def ines_start(request):
    if not ines_sso.enabled():
        return redirect("/connexion")
    return redirect(ines_sso.authorize_url(request.session, config.APP_URL.rstrip("/") + "/auth/ines/callback"))


async def ines_callback(request):
    try:
        info, _ = await run_in_threadpool(ines_sso.fetch_identity, request.session, request.query_params)
    except ines_sso.SSOError as e:
        request.session["login_error"] = str(e)
        return redirect("/connexion")
    _login_session(request, await run_in_threadpool(_user_from_ines, info))
    return redirect("/admin/dashboard")


# ---------------------------------------------------------------- mot de passe oublié
# Le lien envoyé par e-mail porte un jeton aléatoire ; seule son empreinte SHA-256 est en base.
# Il est valable RESET_TTL_MINUTES et ne sert qu'une fois.
RESET_TTL_MINUTES = 60
RESET_SENT = ("Si un compte existe avec cette adresse, un lien de réinitialisation vient de vous être "
              "envoyé. Il est valable 1 heure.")
_reset_ready = False


def _ensure_reset_table():
    global _reset_ready
    if not _reset_ready:
        db.execute("CREATE TABLE IF NOT EXISTS password_resets (token_hash VARCHAR(64) PRIMARY KEY, "
                   "user_id INTEGER NOT NULL, expires_at TIMESTAMP NOT NULL, used_at TIMESTAMP NULL)")
        _reset_ready = True


def _token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _create_reset(user_id):
    _ensure_reset_table()
    token = secrets.token_urlsafe(32)
    db.execute("DELETE FROM password_resets WHERE user_id = ? OR expires_at < LOCALTIMESTAMP", [user_id])
    db.execute("INSERT INTO password_resets (token_hash, user_id, expires_at) VALUES "
               f"(?, ?, LOCALTIMESTAMP + INTERVAL '{RESET_TTL_MINUTES} minutes')", [_token_hash(token), user_id])
    return token


def _find_reset(token):
    if not token or len(token) > 100:
        return None
    _ensure_reset_table()
    return db.fetch("SELECT * FROM password_resets WHERE token_hash = ? AND used_at IS NULL "
                    "AND expires_at > LOCALTIMESTAMP", [_token_hash(token)])


def _apply_reset(reset, password):
    db.execute("UPDATE users SET password = ? WHERE id = ?", [_hash(password), reset["user_id"]])
    db.execute("UPDATE password_resets SET used_at = LOCALTIMESTAMP WHERE token_hash = ?", [reset["token_hash"]])
    db.execute("DELETE FROM password_resets WHERE user_id = ? AND used_at IS NULL", [reset["user_id"]])


def reset_email_template(link):
    content = (email.p("Vous avez demandé à changer le mot de passe de votre compte DIGITA.")
               + email.button("Choisir un nouveau mot de passe", link)
               + email.box("Ce lien est valable <strong>1 heure</strong> et ne fonctionne qu'une seule fois. "
                           "Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail : "
                           "votre mot de passe reste inchangé."))
    return email.layout("Réinitialisation de votre mot de passe", content, "Lien valable 1 heure.")


def show_forgot(request):
    resp = render_view(request, "auth/forgot", {
        "title": "Mot de passe oublié | DIGITA", "metaRobots": "noindex, follow",
        "error": request.session.get("forgot_error"), "success": request.session.get("forgot_success"),
    })
    request.session.pop("forgot_error", None)
    request.session.pop("forgot_success", None)
    return resp


async def forgot(request):
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "reset")

    mail = php.trim(form.get("email", ""))
    if not security.valid_email(mail):
        request.session["forgot_error"] = "Adresse email invalide."
        return redirect("/mot-de-passe-oublie")

    user = await run_in_threadpool(_find_user, mail)
    if user:
        token = await run_in_threadpool(_create_reset, user["id"])
        link = f"{config.APP_URL.rstrip('/')}/reinitialiser-mot-de-passe?token={token}"
        await run_in_threadpool(email.send, user["email"], "Réinitialisation de votre mot de passe",
                                reset_email_template(link), "mot-de-passe")
    # Même réponse que le compte existe ou non, pour ne pas révéler les adresses inscrites.
    request.session["forgot_success"] = RESET_SENT
    return redirect("/mot-de-passe-oublie")


async def show_reset(request):
    token = request.query_params.get("token", "")
    valid = await run_in_threadpool(_find_reset, token) is not None
    resp = render_view(request, "auth/reset", {
        "title": "Nouveau mot de passe | DIGITA", "metaRobots": "noindex, nofollow",
        "token": token, "valid": valid, "error": request.session.get("reset_error"),
    })
    request.session.pop("reset_error", None)
    return resp


async def reset(request):
    form = await request.form()
    security.check_csrf(request, form)
    security.check_rate(request, "reset")

    token = form.get("token", "")
    password = form.get("password", "")
    password2 = form.get("password2", "")
    record = await run_in_threadpool(_find_reset, token)

    error = None
    if record is None:
        error = "Ce lien n'est plus valable. Demandez-en un nouveau."
    elif password != password2:
        error = "Les mots de passe ne correspondent pas."
    elif php.strlen(password) < 8:
        error = "Le mot de passe doit contenir au moins 8 caractères."
    if error:
        request.session["reset_error"] = error
        return redirect(f"/reinitialiser-mot-de-passe?token={token}" if record else "/mot-de-passe-oublie")

    await run_in_threadpool(_apply_reset, record, password)
    request.session["login_success"] = "Mot de passe modifié. Vous pouvez vous connecter."
    return redirect("/connexion")
