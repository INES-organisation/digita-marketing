from starlette.responses import RedirectResponse

from ..render import render_page

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
