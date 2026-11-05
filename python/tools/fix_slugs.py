"""Corrige les adresses des articles et formations (05/11/2026), en une transaction.

- Slugs du PHP sans lettres accentuées (« stratgie-nft ») → slug du titre (« strategie-nft »).
- 90 articles en double (même titre, l'un à l'adresse cassée, l'autre à la bonne) : on garde le plus
  long, l'autre passe en « archived ». Toutes les anciennes adresses redirigent (301) vers la gardée.
- formations.article_slug suit les nouveaux slugs ; updated_at des articles repris de published_at
  (les visites l'avaient remis à la date du jour, voir models/article.increment_views).

    python tools/fix_slugs.py            # aperçu, rien n'est écrit
    python tools/fix_slugs.py --apply    # DATABASE_URL de l'environnement
"""
import collections
import os
import re
import sys

import sqlalchemy as sa

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from digita.redirects import slugify  # noqa: E402


def article_key(title):
    return slugify(re.sub(r"\s*:\s*guide complet\s*$", "", title, flags=re.I))


def plan(articles, formations):
    """→ (renames {table: [(id, old, new)]}, archived [id], redirects [(kind, old, new)])."""
    renames, archived, moves = {"blog_articles": [], "formations": []}, [], []
    groups = collections.defaultdict(list)
    for a in articles:
        groups[article_key(a["title"])].append(a)
    taken = {a["slug"] for a in articles}
    for key, rows in groups.items():
        rows.sort(key=lambda a: (-a["length"], a["id"]))
        keep, others = rows[0], rows[1:]
        archived += [a["id"] for a in others]
        group_slugs = {a["slug"] for a in rows}
        # Sans accent dans le titre, l'adresse n'a rien perdu (« ab-testing ») : on n'y touche pas.
        fix = len(rows) > 1 or not keep["title"].isascii()
        new = key if fix and key not in taken - group_slugs else keep["slug"]  # slug pris par un autre article
        if keep["slug"] != new:
            renames["blog_articles"].append((keep["id"], keep["slug"], new))
        moves += [("article", a["slug"], new) for a in rows if a["slug"] != new]
    taken = {f["slug"] for f in formations}
    for f in formations:
        new = slugify(f["title"])
        if new and new != f["slug"] and new not in taken and not f["title"].isascii():
            renames["formations"].append((f["id"], f["slug"], new))
            moves.append(("formation", f["slug"], new))
            taken.add(new)
    return renames, archived, moves


def main(apply):
    engine = sa.create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as c:
        articles = [dict(r._mapping) for r in c.execute(sa.text(
            "SELECT id, slug, title, length(coalesce(content, '')) AS length FROM blog_articles "
            "WHERE status = 'published'"))]
        formations = [dict(r._mapping) for r in c.execute(sa.text("SELECT id, slug, title FROM formations"))]
        renames, archived, moves = plan(articles, formations)
        print(f"articles : {len(renames['blog_articles'])} renommés, {len(archived)} doublons archivés ; "
              f"formations : {len(renames['formations'])} renommées ; {len(moves)} redirections")
        for kind, old, new in moves[:8]:
            print(f"  {kind:9} {old} → {new}")
        if not apply:
            print("Aperçu seulement : relancer avec --apply pour écrire.")
            return
        c.execute(sa.text(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "database",
                                            "migrations", "2026_11_05_slug_redirects.sql")).read()))
        for aid in archived:  # libère le bon slug, souvent porté par le doublon court
            c.execute(sa.text("UPDATE blog_articles SET status = 'archived', slug = slug || '-doublon-' || id "
                              "WHERE id = :id"), {"id": aid})
        for table, rows in renames.items():
            for rid, _old, new in rows:
                c.execute(sa.text(f"UPDATE {table} SET slug = :new WHERE id = :id"), {"new": new, "id": rid})
        for kind, old, new in moves:
            c.execute(sa.text("UPDATE slug_redirects SET new_slug = :new WHERE kind = :k AND new_slug = :old"),
                      {"new": new, "k": kind, "old": old})
            c.execute(sa.text("INSERT INTO slug_redirects (kind, old_slug, new_slug) VALUES (:k, :old, :new) "
                              "ON CONFLICT (kind, old_slug) DO UPDATE SET new_slug = EXCLUDED.new_slug"),
                      {"k": kind, "old": old, "new": new})
            if kind == "article":
                c.execute(sa.text("UPDATE formations SET article_slug = :new WHERE article_slug = :old"),
                          {"new": new, "old": old})
        c.execute(sa.text("UPDATE blog_articles SET updated_at = coalesce(published_at, created_at)"))
        print("Appliqué.")


if __name__ == "__main__":
    main("--apply" in sys.argv)
