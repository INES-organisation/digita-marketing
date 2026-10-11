"""Vérifie que chaque table PostgreSQL contient exactement les mêmes lignes que MySQL.

    python tools/verify_migration.py --mysql mysql+pymysql://… --pg postgresql+psycopg2://…
"""
import argparse
import datetime
import decimal
import hashlib
import json
import sys

import sqlalchemy as sa


def canon(v):
    if v is None:
        return "∅"
    if isinstance(v, datetime.datetime):
        return v.isoformat(" ")
    if isinstance(v, (datetime.date, datetime.time)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return format(v, "f")
    if isinstance(v, (bytes, memoryview)):
        return bytes(v).hex()
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, (dict, list)):
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    return str(v)


def digest(conn, table, cols, pk, json_cols=()):
    order = ", ".join(pk or cols)
    h = hashlib.sha256()
    n = 0
    for row in conn.execute(sa.text(f"SELECT {', '.join(cols)} FROM {table} ORDER BY {order}")):
        # Côté MySQL une colonne JSON arrive en texte, côté PostgreSQL (jsonb) en objet.
        row = [json.loads(v) if c in json_cols and isinstance(v, str) else v for c, v in zip(cols, row)]
        h.update("\x1f".join(canon(v) for v in row).encode())
        h.update(b"\x1e")
        n += 1
    return n, h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mysql", required=True)
    p.add_argument("--pg", required=True)
    a = p.parse_args()
    my, pg = sa.create_engine(a.mysql), sa.create_engine(a.pg)
    insp = sa.inspect(my)
    ok = True
    with my.connect() as cm, pg.connect() as cp:
        for t in sorted(insp.get_table_names()):
            cols = [c["name"] for c in insp.get_columns(t)]
            json_cols = {c["name"] for c in insp.get_columns(t) if isinstance(c["type"], sa.JSON)}
            pk = insp.get_pk_constraint(t).get("constrained_columns", [])
            a_n, a_h = digest(cm, t, cols, pk, json_cols)
            b_n, b_h = digest(cp, t, cols, pk, json_cols)
            same = (a_n, a_h) == (b_n, b_h)
            ok &= same
            print(f"{'OK ' if same else 'KO '} {t}: mysql={a_n} pg={b_n}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
