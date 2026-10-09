"""Connexion / inscription (AuthController.php)."""
import bcrypt
from starlette.concurrency import run_in_threadpool

from .. import db, php, security
from ..render import render_page
from .common import redirect


def _authenticated(request):
    return "user_id" in request.session


def show_login(request):
    if _authenticated(request):
        return redirect("/admin/dashboard")
    resp = render_page(request, "app/Views/auth/login.html", {
        "pageTitle": "Connexion - Digita Marketing",
        "error": request.session.get("login_error"),
    })
    request.session.pop("login_error", None)
    return resp


def show_register(request):
    if _authenticated(request):
        return redirect("/admin/dashboard")
    resp = render_page(request, "app/Views/auth/register.html", {
        "pageTitle": "Inscription - Digita Marketing",
        "error": request.session.get("register_error"),
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
