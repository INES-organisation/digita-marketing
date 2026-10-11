"""Rendu Jinja2 avec la sémantique des vues PHP (ViewHelper::render, require_once…)."""
from jinja2 import ChainableUndefined, Environment, FileSystemLoader
from starlette.responses import HTMLResponse

from . import config, php
from .csrf import csrf_field

env = Environment(
    loader=FileSystemLoader(str(config.ROOT / "python" / "digita" / "templates")),
    autoescape=False,          # PHP n'échappe que via htmlspecialchars() → h()
    undefined=ChainableUndefined,
    finalize=php.finalize,     # echo PHP : null → '', true → '1', 2.0 → '2'
    keep_trailing_newline=True,
    extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols"],
)
env.globals.update(php.GLOBALS)
env.globals["const"] = lambda name: config.CONSTANTS.get(name, name)
env.globals["defined"] = lambda name: name in config.CONSTANTS


def base_context(request):
    included = set()

    def once(path):
        if path in included:
            return False
        included.add(path)
        return True

    forwarded_https = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
    server = {
        "REQUEST_METHOD": request.method,
        "REQUEST_URI": request.url.path + (("?" + request.url.query) if request.url.query else ""),
        "HTTP_HOST": request.headers.get("host", "digita.buzz"),
    }
    if forwarded_https:
        server["HTTPS"] = "on"
    session = request.session if "session" in request.scope else {}
    return {
        "once": once,
        "_SERVER": server,
        "_GET": dict(request.query_params),
        "_SESSION": session,
        "CsrfMiddleware_field": lambda: csrf_field(session),
        "base_url": ("https" if forwarded_https else "http") + "://" + server["HTTP_HOST"],
    }


def render_string(request, template, data=None, ctx=None):
    ctx = ctx or base_context(request)
    return env.get_template(template).render({**ctx, **(data or {})})


def render_view(request, view, data=None, layout="main", status=200):
    """Équivalent de ViewHelper::render($view, $data, $layout)."""
    ctx = base_context(request)
    data = dict(data or {})
    # En PHP la vue et le layout partagent les mêmes variables : celles définies par la
    # vue (ex. $title) sont visibles du layout. make_module() expose ces variables.
    module = env.get_template(f"app/Views/{view}.html").make_module({**ctx, **data})
    exported = {k: v for k, v in vars(module).items() if not k.startswith("_")}
    html = render_string(request, f"app/Views/layouts/{layout}.html", {**data, **exported, "content_": str(module)}, ctx)
    return HTMLResponse(html, status_code=status)


def render_page(request, template, data=None, status=200):
    """Template autonome (équivalent d'un require direct d'un fichier PHP)."""
    return HTMLResponse(render_string(request, template, data), status_code=status)
