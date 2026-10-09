"""Applique un fichier SQL simple (instructions séparées par « ; » en fin de ligne) à une base.

    python tools/apply_sql.py <url SQLAlchemy> <fichier.sql>
"""
import re
import sys

import sqlalchemy as sa

url, path = sys.argv[1], sys.argv[2]
sql = re.sub(r"^\s*--.*$", "", open(path, encoding="utf-8").read(), flags=re.M)
with sa.create_engine(url).begin() as c:
    for stmt in re.split(r";\s*$", sql, flags=re.M):
        if stmt.strip():
            c.exec_driver_sql(stmt)
print(f"{path} appliqué")
