"""Accès base de données : même interface que la classe Database PHP (fetch/fetchAll)."""
import datetime as dt
import re

from sqlalchemy import create_engine, text

from . import config

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=5)


def _php_value(v):
    # PDO renvoie les dates sous forme de chaîne « Y-m-d H:i:s » : on garde ce format.
    if isinstance(v, dt.datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, dt.date):
        return v.strftime("%Y-%m-%d")
    return v


def _prepare(sql, params):
    """Remplace les « ? » positionnels par des paramètres nommés SQLAlchemy."""
    params = list(params or [])
    names = {}
    i = 0

    def repl(_m):
        nonlocal i
        key = f"p{i}"
        names[key] = params[i]
        i += 1
        return f":{key}"

    sql = re.sub(r"\?", repl, sql)
    return text(sql), names


def query(sql, params=None):
    stmt, binds = _prepare(sql, params)
    with engine.begin() as c:
        res = c.execute(stmt, binds)
        if res.returns_rows:
            return [{k: _php_value(v) for k, v in r.items()} for r in res.mappings()]
        return res.rowcount


def fetch_all(sql, params=None):
    return query(sql, params)


def fetch(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    return query(sql, params)
