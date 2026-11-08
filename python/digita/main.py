"""Application FastAPI : reproduit le routeur PHP (public/index.php + includes/Router.php).

Ordre de résolution identique au PHP : fichier statique existant dans public/,
puis route exacte, puis routes à paramètres dans l'ordre de déclaration, sinon 404.
"""
import inspect
import logging
import re
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import HTMLResponse, FileResponse, PlainTextResponse, RedirectResponse, Response

from . import config
from .routes import ROUTES
from .routes.common import not_found
from .security import Abort
from .sessions import SessionMiddleware

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
app.add_middleware(SessionMiddleware, https_only=config.APP_ENV == "production")

log = logging.getLogger("digita")

PUBLIC = config.PUBLIC_DIR.resolve()

# Pages de vente sur sous-domaine (vhost : deploy/nginx-digita.conf) : `/` sert la page, les fichiers
# statiques et le chatbot restent sur place, tout autre lien repart vers le site principal.
LANDING_HOSTS = {"agent24-7.digita.buzz": "/agent24-7"}
LANDING_API = "/api/chatbot/"


def _compile(path):
    return re.compile("^" + re.sub(r":\w+", "([^/]+)", path) + "$")


EXACT = {}
DYNAMIC = []
for method, path, handler in ROUTES:
    # Comme $this->routes[$method][$path] = $callback : une redéclaration remplace
    # la précédente mais garde sa position d'origine.
    key = (method, path)
    EXACT[key] = handler
    if ":" in path and all(k != key for k, _ in DYNAMIC):
        DYNAMIC.append((key, _compile(path)))


def static_file(path):
    if path in ("", "/") or path.endswith(".php"):
        return None
    try:
        target = (PUBLIC / path.lstrip("/")).resolve()
    except (OSError, ValueError):
        return None
    if PUBLIC not in target.parents or not target.is_file():
        return None
    if any(part.startswith(".") for part in target.relative_to(PUBLIC).parts):
        return None
    return target


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


# Page d'erreur autonome (sans gabarit ni base : l'erreur vient peut-être de là), aux couleurs du site.
ERROR_500 = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Erreur momentanée | DIGITA</title><style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#050505;color:#d1d5db;font-family:system-ui,-apple-system,sans-serif;padding:16px}
main{max-width:520px;text-align:center}h1{color:#fff;font-size:1.8rem;margin:1.2rem 0 .8rem}p{line-height:1.6}
a{display:inline-block;margin:.4rem;padding:.8rem 1.4rem;border-radius:50px;text-decoration:none;font-weight:700}
.p{background:linear-gradient(135deg,#d4af37,#f4d03f);color:#050505}.g{border:1px solid #25d366;color:#25d366}
img{width:150px;height:auto}</style></head><body><main>
<img src="/assets/images/logo-480.webp" alt="DIGITA" width="150" height="35">
<h1>Un souci technique momentané</h1>
<p>La page n'a pas pu s'afficher. Réessayez dans quelques instants ; si cela persiste, écrivez-nous, nous corrigeons au plus vite.</p>
<p><a class="p" href="/">Retour à l'accueil</a><a class="g" href="https://wa.me/262693487817">WhatsApp</a></p>
<p style="font-size:.85rem">06 93 48 78 17 · contact@digita.buzz</p></main></body></html>"""


@app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD"])
async def dispatch(request: Request, full_path: str):
    # Chemin brut (non décodé), comme parse_url($_SERVER['REQUEST_URI']) en PHP.
    uri = request.scope.get("raw_path", b"").decode("latin-1").split("?")[0] or request.url.path
    if uri.startswith("/digita-marketing"):
        uri = uri[len("/digita-marketing"):]
    uri = uri or "/"

    landing = LANDING_HOSTS.get(request.headers.get("host", "").split(":")[0].lower())
    if landing:
        if uri == "/":
            uri = landing
        elif not uri.startswith(LANDING_API) and not static_file(uri):
            query = f"?{request.url.query}" if request.url.query else ""
            return RedirectResponse(f"https://digita.buzz{uri}{query}", status_code=302)

    if request.method in ("GET", "HEAD"):
        f = static_file(uri)
        if f:
            return FileResponse(f)

    method = "GET" if request.method == "HEAD" else request.method
    handler = EXACT.get((method, uri))
    args = ()
    if handler is None:
        for key, rx in DYNAMIC:
            if key[0] != method:
                continue
            m = rx.match(uri)
            if m:
                handler, args = EXACT[key], m.groups()
                break
    if handler is None:
        if method == "GET":
            return await run_in_threadpool(not_found, request)
        return PlainTextResponse("Page non trouvée", status_code=404, media_type="text/html")

    try:
        if inspect.iscoroutinefunction(handler):
            resp = await handler(request, *args)
        else:
            # Les vues font des requêtes SQL bloquantes : pool de threads.
            resp = await run_in_threadpool(handler, request, *args)
    except Abort as stop:
        resp = stop.response
    except Exception:  # noqa: BLE001 — customExceptionHandler PHP : message générique
        log.exception("Erreur sur %s %s", request.method, uri)
        return HTMLResponse(ERROR_500, status_code=500)
    return resp if isinstance(resp, Response) else Response(resp)
