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
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse, PlainTextResponse, Response

from . import config
from .routes import ROUTES
from .security import Abort

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, session_cookie="DIGITASESSID",
                   https_only=config.APP_ENV == "production", same_site="lax")

log = logging.getLogger("digita")

PUBLIC = config.PUBLIC_DIR.resolve()


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


@app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD"])
async def dispatch(request: Request, full_path: str):
    # Chemin brut (non décodé), comme parse_url($_SERVER['REQUEST_URI']) en PHP.
    uri = request.scope.get("raw_path", b"").decode("latin-1").split("?")[0] or request.url.path
    if uri.startswith("/digita-marketing"):
        uri = uri[len("/digita-marketing"):]
    uri = uri or "/"

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
        return PlainTextResponse("Une erreur est survenue. Veuillez réessayer plus tard.",
                                 status_code=500, media_type="text/html")
    return resp if isinstance(resp, Response) else Response(resp)
