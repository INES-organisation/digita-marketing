"""Connexion / inscription (AuthController.php) — affichage des formulaires."""
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
