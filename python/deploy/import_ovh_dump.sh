#!/bin/bash
# Importe un export MySQL d'OVH (phpMyAdmin → Exporter → SQL) dans la base PostgreSQL « digita »
# du VPS INES, puis vérifie que chaque table contient exactement les mêmes lignes.
#
#   bash python/deploy/import_ovh_dump.sh /chemin/export_ovh.sql [--drop]
#
# Démarre un MySQL temporaire (supprimé à la fin) sur le réseau d'INES ; n'écrit rien sur OVH.
set -euo pipefail
DUMP="$(realpath "${1:?Usage : import_ovh_dump.sh export.sql [--drop]}")"
DROP="${2:-}"
cd "$(dirname "$0")"
set -a; source .env; set +a
NET="${INES_NETWORK:-ines_ines-network}"
TMP=digita-mysql-import

cleanup() { docker rm -f "$TMP" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "▶ MySQL temporaire…"
docker run -d --name "$TMP" --network "$NET" -e MYSQL_ROOT_PASSWORD=import -e MYSQL_DATABASE=digita mysql:8.0 \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci >/dev/null
until docker exec "$TMP" mysql -uroot -pimport -e "SELECT 1" digita >/dev/null 2>&1; do sleep 2; done

echo "▶ Import de $(basename "$DUMP")…"
docker exec -i "$TMP" mysql -uroot -pimport --default-character-set=utf8mb4 digita < "$DUMP"

MYSQL_URL="mysql+pymysql://root:import@$TMP/digita?charset=utf8mb4"
run() {
  docker run --rm --network "$NET" -v "$(realpath ../..)":/src -w /src/python --user root \
    python:3.13-slim sh -c "pip install -q -r requirements-dev.txt && python tools/$*"
}
echo "▶ Copie vers PostgreSQL…"
run migrate_mysql_to_pg.py --mysql "$MYSQL_URL" --pg "$DATABASE_URL" $DROP
echo "▶ Vérification ligne à ligne…"
run verify_migration.py --mysql "$MYSQL_URL" --pg "$DATABASE_URL"
echo "✅ Import terminé."
