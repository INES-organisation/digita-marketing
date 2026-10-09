from starlette.responses import HTMLResponse, RedirectResponse

from ..render import render_page

NOT_PORTED = ("Cette fonctionnalité est en cours de migration vers la nouvelle version du site. "
              "Contactez-nous via <a href=\"/contact\">la page contact</a>.")


def not_ported(request, *args):
    """Route PHP pas encore convertie (liste dans docs/migrations/SUIVI_CONVERSION_PYTHON.md)."""
    return HTMLResponse(NOT_PORTED, status_code=501)


def redirect(url):
    # header('Location: …') sans code explicite → 302 en PHP
    return RedirectResponse(url, status_code=302)


def not_found(request, **ctx):
    """require Views/errors/404.php avec le statut 404 (variables du contrôleur visibles)."""
    return render_page(request, "app/Views/errors/404.html", ctx, status=404)


def page_param(request):
    try:
        return max(1, int(request.query_params.get("page", "1")))
    except ValueError:
        return 1
