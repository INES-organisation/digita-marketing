"""Tri des articles d'origine → SQL (09/11/2026).

Lit database/blog/tri-articles-origine.csv (slug, sujet, action, cible) :
- fusion : redirection 301 vers le nouvel article (slug_redirects), article archivé ;
- retirer : article archivé, sa page répond 410 (routes/blog.py) ;
- reecrire : rien pour l'instant, l'article reste en ligne jusqu'à sa réécriture.
Seuls les anciens articles (content_type NULL) publiés sont touchés ; rien n'est supprimé de la base.

Usage, depuis python/ : python tools/build_tri_sql.py ../database/migrations/<date>_blog_tri_articles_origine.sql
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLUG = re.compile(r"^[a-z0-9-]+$")


def build(rows):
    redirects = [(r["slug"], r["cible"].removeprefix("/blog/")) for r in rows if r["action"] == "fusion"]
    archived = [r["slug"] for r in rows if r["action"] in ("fusion", "retirer")]
    for s in archived + [n for _, n in redirects]:
        assert SLUG.match(s), s
    pairs = ",\n".join(f"('{o}', '{n}')" for o, n in redirects)
    slugs = ",\n".join(f"'{s}'" for s in archived)
    return f"""-- Tri des articles d'origine (09/11/2026), généré par python/tools/build_tri_sql.py
-- {len(redirects)} redirections 301, {len(archived) - len(redirects)} articles retirés (410). Rien n'est supprimé :
-- les articles passent en statut 'archived' (retour possible avec status = 'published').
BEGIN;
-- Les anciennes adresses qui menaient à un article fusionné mènent directement à sa cible.
UPDATE slug_redirects SET new_slug = t.new_slug FROM (VALUES
{pairs}
) AS t(old_slug, new_slug) WHERE slug_redirects.kind = 'article' AND slug_redirects.new_slug = t.old_slug;
INSERT INTO slug_redirects (kind, old_slug, new_slug) SELECT 'article', old_slug, new_slug FROM (VALUES
{pairs}
) AS t(old_slug, new_slug)
ON CONFLICT (kind, old_slug) DO UPDATE SET new_slug = EXCLUDED.new_slug;
UPDATE blog_articles SET status = 'archived', updated_at = NOW()
WHERE status = 'published' AND content_type IS NULL AND slug IN (
{slugs}
);
COMMIT;
"""


if __name__ == "__main__":
    rows = list(csv.DictReader(open(ROOT / "database/blog/tri-articles-origine.csv", encoding="utf-8")))
    Path(sys.argv[1]).write_text(build(rows), encoding="utf-8")
