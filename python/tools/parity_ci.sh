#!/bin/bash
# Test de parité complet PHP ↔ Python (utilisé par la CI, rejouable en local).
#
# Pré-requis : MySQL sur $MYSQL_HOST (root/$MYSQL_PWD), PostgreSQL sur $PG_URL, php, le venv.
#   MYSQL_HOST=127.0.0.1 MYSQL_PWD=root PG_URL=postgresql+psycopg2://ines:ines@127.0.0.1/digita \
#     bash python/tools/parity_ci.sh
#
# 1. importe database/production_data_full.sql + migrations dans MySQL (« digita » et « digita_pristine »)
# 2. copie digita_pristine vers PostgreSQL et vérifie les données ligne à ligne
# 3. lance le site PHP (copie avec tri déterministe, voir plus bas) et le site Python
# 4. aspire toutes les pages publiques des deux côtés et compare le HTML
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PY="$ROOT/python/.venv/bin/python"
WORK="${WORK:-$(mktemp -d)}"
: "${MYSQL_HOST:=127.0.0.1}" "${MYSQL_PWD:=root}" "${PG_URL:?PG_URL requis}"
export MYSQL_PWD
MY="mysql -h $MYSQL_HOST -uroot --default-character-set=utf8mb4"

echo "▶ Base MySQL de référence"
for db in digita digita_pristine; do
  $MY -e "DROP DATABASE IF EXISTS $db; CREATE DATABASE $db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
  $MY $db < "$ROOT/database/production_data_full.sql"
  for f in "$ROOT"/database/sprint{2,3,4,5}_migration.sql "$ROOT"/database/migrations/*.sql; do
    $MY --force $db < "$f" >/dev/null 2>&1 || true
  done
  # La production a une colonne users.username (cf. database/production_data.sql) absente de l'export.
  $MY $db -e "ALTER TABLE users ADD COLUMN username VARCHAR(50) NULL AFTER id; UPDATE users SET username = SUBSTRING_INDEX(email, '@', 1)"
  # sprint3_migration.sql échoue en bloc sur order_items (product_name existe déjà) : product_type,
  # utilisé par les commandes, n'est donc pas créé. On l'ajoute comme le prévoyait la migration.
  $MY $db -e "ALTER TABLE order_items ADD COLUMN product_type ENUM('formation','pack','consulting','subscription') DEFAULT 'formation' AFTER product_id"
done

echo "▶ Migration vers PostgreSQL"
"$PY" "$ROOT/python/tools/migrate_mysql_to_pg.py" --drop --mysql "mysql+pymysql://root:$MYSQL_PWD@$MYSQL_HOST/digita_pristine?charset=utf8mb4" --pg "$PG_URL" | tail -1
"$PY" "$ROOT/python/tools/verify_migration.py" --mysql "mysql+pymysql://root:$MYSQL_PWD@$MYSQL_HOST/digita_pristine?charset=utf8mb4" --pg "$PG_URL" | grep -v "=0 pg=0"

echo "▶ Site PHP de référence"
# Copie du PHP où seuls les tris ambigus (égalités de date, RAND()) reçoivent un départage par id,
# exactement comme la version Python en mode DIGITA_DETERMINISTIC=1.
REF="$WORK/ref"
rm -rf "$REF" && mkdir -p "$REF"
cp -r "$ROOT"/{app,config,includes,public,templates} "$REF/"
mkdir -p "$REF/logs" "$REF/cache"
printf "APP_ENV=development\nAPP_DEBUG=false\nAPP_URL=http://127.0.0.1:8081\nDB_HOST=%s\nDB_NAME=digita\nDB_USER=root\nDB_PASS=%s\n" "$MYSQL_HOST" "$MYSQL_PWD" > "$REF/.env"
sed -i -E "s/ORDER BY a\.(published_at|views|created_at) DESC/ORDER BY a.\1 DESC, a.id DESC/; s/ORDER BY RAND\(\)/ORDER BY a.id/; s/ORDER BY c\.name'/ORDER BY c.name, c.id'/" "$REF/app/Models/Article.php"
sed -i -E "s/ORDER BY f\.created_at DESC/ORDER BY f.created_at DESC, f.id DESC/; s/ORDER BY f\.enrolled_count DESC, f\.rating DESC/ORDER BY f.enrolled_count DESC, f.rating DESC, f.id DESC/; s/ORDER BY RAND\(\)/ORDER BY f.id/; s/ORDER BY c\.name'/ORDER BY c.name, c.id'/; s/ORDER BY order_num'/ORDER BY order_num, id'/; s/ORDER BY fr\.created_at DESC/ORDER BY fr.created_at DESC, fr.id DESC/" "$REF/app/Models/Formation.php"
# Formation::find() n'existe pas : tout le module de paiement PHP plante (« Call to undefined method »).
# La version Python le corrige ; la référence reçoit la même méthode pour comparer le reste du parcours.
sed -i -E 's/^    public function getById\(\$id\) \{$/    public function find($id) { return $this->db->fetch("SELECT * FROM formations WHERE id = ?", [$id]); }\n\n    public function getById($id) {/' "$REF/app/Models/Formation.php"
grep -q "public function find" "$REF/app/Models/Formation.php"
sed -i -E "s/ORDER BY o\.created_at DESC/ORDER BY o.created_at DESC, o.id DESC/" "$REF/app/Models/Order.php"
sed -i -E "s/ORDER BY cp\.updated_at DESC\"/ORDER BY cp.updated_at DESC, cp.id DESC\"/; s/ORDER BY pm\.created_at ASC\"/ORDER BY pm.created_at ASC, pm.id\"/; s/ORDER BY pf\.created_at DESC\"/ORDER BY pf.created_at DESC, pf.id DESC\"/; s/ORDER BY sort_order ASC\"/ORDER BY sort_order ASC, id\"/; s/ORDER BY psh\.created_at DESC\"/ORDER BY psh.created_at DESC, psh.id DESC\"/" "$REF/app/Models/Project.php"
sed -i -E "s/ORDER BY updated_at DESC LIMIT 1/ORDER BY updated_at DESC, id DESC LIMIT 1/" "$REF/app/Services/ContextManager.php"
cat > "$WORK/router.php" <<'PHP'
<?php
$p = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if ($p !== '/' && is_file($_SERVER['DOCUMENT_ROOT'] . $p)) return false;
require $_SERVER['DOCUMENT_ROOT'] . '/index.php';
PHP
(cd "$REF/public" && php -S 127.0.0.1:8081 "$WORK/router.php" > "$WORK/php.log" 2>&1 &)
(cd "$ROOT/python" && DIGITA_DETERMINISTIC=1 DIGITA_AUDIT_ALLOW_PRIVATE=1 APP_ENV=development DATABASE_URL="$PG_URL" \
  .venv/bin/uvicorn digita.main:app --port 8000 > "$WORK/py.log" 2>&1 &)
sleep 4
trap 'pkill -f "php -S 127.0.0.1:8081" || true; pkill -f "uvicorn digita.main:app --port 8000" || true' EXIT

echo "▶ Aspiration et comparaison"
"$PY" "$ROOT/python/tools/parity.py" urls --db "mysql+pymysql://root:$MYSQL_PWD@$MYSQL_HOST/digita?charset=utf8mb4" > "$WORK/urls.txt"
"$PY" "$ROOT/python/tools/parity.py" snap http://127.0.0.1:8081 "$WORK/urls.txt" "$WORK/php"
"$PY" "$ROOT/python/tools/parity.py" snap http://127.0.0.1:8000 "$WORK/urls.txt" "$WORK/py"
# /portfolio et /equipe : templates absents côté PHP (erreur), écart connu et voulu.
rm -f "$WORK"/php/portfolio-*.html "$WORK"/php/equipe-*.html "$WORK"/py/portfolio-*.html "$WORK"/py/equipe-*.html
"$PY" "$ROOT/python/tools/parity.py" diff "$WORK/php" "$WORK/py"

echo "▶ Formulaires et espaces connectés"
"$PY" "$ROOT/python/tools/apply_sql.py" "mysql+pymysql://root:$MYSQL_PWD@$MYSQL_HOST/digita?charset=utf8mb4" "$ROOT/python/tools/fixtures_forms.sql"
"$PY" "$ROOT/python/tools/apply_sql.py" "$PG_URL" "$ROOT/python/tools/fixtures_forms.sql"
"$PY" "$ROOT/python/tools/post_parity.py" http://127.0.0.1:8081 http://127.0.0.1:8000
