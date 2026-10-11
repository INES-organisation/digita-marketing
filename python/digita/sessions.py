"""Sessions côté serveur, comme les sessions PHP (fichiers) : le cookie ne porte qu'un identifiant.

Les données (panier de résultats de quiz, messages, jeton CSRF…) restent en base, table
`web_sessions`, et n'alourdissent pas le cookie. Les sessions inactives depuis plus de
24 heures sont supprimées.
"""
import json
import secrets

from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection

from . import db

COOKIE = "DIGITASESSID"
MAX_IDLE_HOURS = 24
_ready = False


def _ensure_table():
    global _ready
    if not _ready:
        db.execute("CREATE TABLE IF NOT EXISTS web_sessions (id VARCHAR(64) PRIMARY KEY, data TEXT NOT NULL, "
                   "updated_at TIMESTAMP NOT NULL DEFAULT LOCALTIMESTAMP)")
        _ready = True


def _load(sid):
    _ensure_table()
    row = db.fetch("SELECT data FROM web_sessions WHERE id = ? "
                   f"AND updated_at > LOCALTIMESTAMP - INTERVAL '{MAX_IDLE_HOURS} hours'", [sid])
    return json.loads(row["data"]) if row else None


def _save(sid, data, touch_only):
    _ensure_table()
    if touch_only:
        db.execute("UPDATE web_sessions SET updated_at = LOCALTIMESTAMP WHERE id = ?", [sid])
        return
    db.execute("INSERT INTO web_sessions (id, data) VALUES (?, ?) ON CONFLICT (id) DO UPDATE "
               "SET data = EXCLUDED.data, updated_at = LOCALTIMESTAMP", [sid, json.dumps(data, default=str)])
    if secrets.randbelow(100) == 0:
        db.execute(f"DELETE FROM web_sessions WHERE updated_at < LOCALTIMESTAMP - INTERVAL '{MAX_IDLE_HOURS} hours'")


class SessionMiddleware:
    def __init__(self, app, https_only=False):
        self.app = app
        self.secure = "; secure" if https_only else ""

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        conn = HTTPConnection(scope)
        sid = conn.cookies.get(COOKIE, "")
        data = None
        if len(sid) == 64 and all(c in "0123456789abcdef" for c in sid):
            data = await run_in_threadpool(_load, sid)
        is_new = data is None
        if is_new:
            sid, data = secrets.token_hex(32), {}
        scope["session"] = data
        scope["session_id"] = sid
        before = json.dumps(data, sort_keys=True, default=str)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                after = json.dumps(scope["session"], sort_keys=True, default=str)
                # session_id() utilisé (chatbot, analytics) : la session doit exister même vide.
                changed = after != before or (is_new and scope.get("session_id_used", False))
                if changed or not is_new:
                    await run_in_threadpool(_save, sid, scope["session"], not changed)
                if changed and is_new:
                    headers = MutableHeaders(scope=message)
                    headers.append("Set-Cookie", f"{COOKIE}={sid}; path=/; HttpOnly; SameSite=Lax{self.secure}")
            await send(message)

        await self.app(scope, receive, send_wrapper)
