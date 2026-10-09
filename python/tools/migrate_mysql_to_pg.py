"""Copie la base MySQL de Digita (export OVH importé localement) vers PostgreSQL.

Recrée chaque table avec des types PostgreSQL équivalents, copie toutes les lignes,
recale les séquences d'auto-incrément et active l'extension `unaccent` (recherche
insensible aux accents, comme la collation utf8mb4_unicode_ci de MySQL).

Deux comportements MySQL sont conservés côté PostgreSQL :
- ENUM : une contrainte CHECK refuse les valeurs hors liste (comme le mode strict) ;
- ON UPDATE CURRENT_TIMESTAMP : un déclencheur met la colonne à jour quand la ligne change.

    python tools/migrate_mysql_to_pg.py \
        --mysql mysql+pymysql://root:root@127.0.0.1/digita \
        --pg postgresql+psycopg2://ines:ines@127.0.0.1/digita [--drop]

Le script n'écrit jamais dans MySQL. Avec --drop, les tables existantes côté
PostgreSQL sont supprimées avant la copie (à utiliser pour rejouer la migration).
"""
import argparse
import sys

import sqlalchemy as sa
from sqlalchemy.dialects import mysql, postgresql

BATCH = 500


def pg_type(col_type):
    """Traduit un type MySQL réfléchi en type SQLAlchemy générique."""
    t = col_type
    if isinstance(t, mysql.ENUM):
        return sa.String(max((len(e) for e in t.enums), default=32))
    if isinstance(t, mysql.SET):
        return sa.Text()
    if isinstance(t, (mysql.TINYINT,)):
        return sa.SmallInteger()
    if isinstance(t, (mysql.SMALLINT, mysql.MEDIUMINT)):
        return sa.Integer()
    if isinstance(t, mysql.BIGINT):
        return sa.BigInteger()
    if isinstance(t, (mysql.INTEGER,)):
        return sa.Integer()
    if isinstance(t, (mysql.DECIMAL, mysql.NUMERIC)):
        return sa.Numeric(t.precision, t.scale)
    if isinstance(t, (mysql.DOUBLE, mysql.FLOAT, mysql.REAL)):
        return sa.Float()
    if isinstance(t, (mysql.TINYTEXT, mysql.TEXT, mysql.MEDIUMTEXT, mysql.LONGTEXT)):
        return sa.Text()
    if isinstance(t, (mysql.VARCHAR, mysql.CHAR)):
        return sa.String(t.length)
    if isinstance(t, (mysql.TIMESTAMP, mysql.DATETIME)):
        return sa.DateTime()
    if isinstance(t, mysql.DATE):
        return sa.Date()
    if isinstance(t, mysql.TIME):
        return sa.Time()
    if isinstance(t, mysql.JSON):
        # jsonb normalise le texte comme MySQL (clés triées par longueur puis ordre, « ": " et ", »).
        return postgresql.JSONB()
    if isinstance(t, (mysql.BLOB, mysql.LONGBLOB, mysql.MEDIUMBLOB, mysql.TINYBLOB)):
        return sa.LargeBinary()
    if isinstance(t, mysql.BIT):
        return sa.Boolean()
    if isinstance(t, mysql.YEAR):
        return sa.SmallInteger()
    return t.as_generic()


def pg_default(col):
    d = col.get("default")
    if d is None:
        return None
    raw = str(d).strip()
    up = raw.upper()
    if "CURRENT_TIMESTAMP" in up:
        # MySQL garde la seconde, sans fraction : deux écritures dans la même seconde sont à égalité.
        return sa.text("date_trunc('second', LOCALTIMESTAMP)")
    if up == "NULL":
        return None
    return sa.text(raw if raw.startswith("'") else f"'{raw.strip(chr(39))}'")


def build_pg_metadata(my_engine):
    insp = sa.inspect(my_engine)
    md = sa.MetaData()
    for tname in insp.get_table_names():
        pk = insp.get_pk_constraint(tname).get("constrained_columns", [])
        cols = []
        for c in insp.get_columns(tname):
            cols.append(sa.Column(
                c["name"], pg_type(c["type"]),
                primary_key=c["name"] in pk,
                nullable=c["nullable"],
                server_default=pg_default(c),
                autoincrement=bool(c.get("autoincrement")) and c["name"] in pk,
            ))
        args = []
        for uc in insp.get_unique_constraints(tname):
            args.append(sa.UniqueConstraint(*uc["column_names"], name=f"{tname}_{uc['name']}"))
        for c in insp.get_columns(tname):
            if isinstance(c["type"], mysql.ENUM):
                values = ", ".join("'" + e.replace("'", "''") + "'" for e in c["type"].enums)
                args.append(sa.CheckConstraint(f'"{c["name"]}" IN ({values})', name=f"{tname}_{c['name']}_enum"))
        t = sa.Table(tname, md, *cols, *args)
        for ix in insp.get_indexes(tname):
            if ix.get("unique") and any(
                set(ix["column_names"]) == set(u["column_names"]) for u in insp.get_unique_constraints(tname)
            ):
                continue
            cols_ok = [c for c in ix["column_names"] if c]
            if cols_ok:
                sa.Index(f"{tname}_{ix['name']}", *[t.c[c] for c in cols_ok], unique=bool(ix.get("unique")))
    # Clés étrangères en second passage (toutes les tables existent alors dans md).
    for tname in insp.get_table_names():
        for fk in insp.get_foreign_keys(tname):
            if fk["referred_table"] not in md.tables:
                continue
            md.tables[tname].append_constraint(sa.ForeignKeyConstraint(
                fk["constrained_columns"],
                [f"{fk['referred_table']}.{c}" for c in fk["referred_columns"]],
                name=f"{tname}_{fk['name']}",
                ondelete=(fk.get("options") or {}).get("ondelete"),
            ))
    return md


TOUCH_FUNCTION = """
CREATE OR REPLACE FUNCTION digita_on_update_timestamp() RETURNS trigger AS $$
DECLARE
    col text := TG_ARGV[0];
BEGIN
    -- Comme MySQL : seulement si la ligne change et que la colonne n'est pas fixée par la requête.
    IF to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD)
       AND to_jsonb(NEW) -> col IS NOT DISTINCT FROM to_jsonb(OLD) -> col THEN
        NEW := jsonb_populate_record(NEW, jsonb_build_object(col, date_trunc('second', LOCALTIMESTAMP)));
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql
"""


def on_update_columns(my_engine):
    with my_engine.connect() as c:
        return c.execute(sa.text(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND LOWER(extra) LIKE '%on update%'"
        )).all()


def create_triggers(pg_engine, columns):
    with pg_engine.begin() as c:
        c.execute(sa.text(TOUCH_FUNCTION))
        for table, column in columns:
            c.execute(sa.text(
                f'CREATE TRIGGER "{table}_{column}_on_update" BEFORE UPDATE ON "{table}" '
                f"FOR EACH ROW EXECUTE FUNCTION digita_on_update_timestamp('{column}')"
            ))


def copy_rows(my_engine, pg_engine, md):
    with my_engine.connect() as src, pg_engine.begin() as dst:
        for t in md.sorted_tables:
            res = src.execution_options(stream_results=True).execute(sa.text(f"SELECT * FROM `{t.name}`"))
            n = 0
            while rows := res.mappings().fetchmany(BATCH):
                dst.execute(t.insert(), [dict(r) for r in rows])
                n += len(rows)
            print(f"  {t.name}: {n} lignes")
        for t in md.sorted_tables:
            for c in t.primary_key.columns:
                if c.autoincrement is True and isinstance(c.type, sa.Integer):
                    dst.execute(sa.text(
                        f"SELECT setval(pg_get_serial_sequence('{t.name}', '{c.name}'), "
                        f"COALESCE((SELECT MAX({c.name}) FROM {t.name}), 0) + 1, false)"
                    ))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mysql", required=True)
    p.add_argument("--pg", required=True)
    p.add_argument("--drop", action="store_true")
    a = p.parse_args()

    my_engine = sa.create_engine(a.mysql)
    pg_engine = sa.create_engine(a.pg)
    md = build_pg_metadata(my_engine)

    with pg_engine.begin() as c:
        c.execute(sa.text("CREATE EXTENSION IF NOT EXISTS unaccent"))
        existing = set(sa.inspect(c).get_table_names())
    clash = existing & set(md.tables)
    if clash and not a.drop:
        sys.exit(f"Tables déjà présentes côté PostgreSQL : {sorted(clash)} (relancer avec --drop)")
    if a.drop:
        md.drop_all(pg_engine)
    # Clés étrangères posées après la copie : pas besoin de droits superutilisateur
    # (session_replication_role) pour désactiver leurs contrôles pendant le chargement.
    fks = [(t, fk) for t in md.sorted_tables for fk in list(t.foreign_key_constraints)]
    for t, fk in fks:
        t.constraints.discard(fk)
    md.create_all(pg_engine)
    print(f"{len(md.tables)} tables créées, copie des données…")
    copy_rows(my_engine, pg_engine, md)
    with pg_engine.begin() as c:
        for t, fk in fks:
            c.execute(sa.schema.AddConstraint(fk))
            t.append_constraint(fk)
    print(f"{len(fks)} clés étrangères ajoutées.")
    columns = on_update_columns(my_engine)
    create_triggers(pg_engine, columns)
    print(f"{len(columns)} colonnes ON UPDATE CURRENT_TIMESTAMP reproduites par déclencheur.")
    print("Migration terminée.")


if __name__ == "__main__":
    main()
