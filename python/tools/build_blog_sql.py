"""Génère le fichier SQL qui ajoute les articles de database/blog/ en brouillon.

Chaque article = une entrée de database/blog/articles.json + son corps HTML dans
database/blog/<slug>.html. Le HTML est mis sur une seule ligne : le gabarit de l'article
transforme les lignes vides en paragraphes, et tools/apply_sql.py coupe aux « ; » de fin de ligne.
Les articles existants (même slug) ne sont pas modifiés ; on les publie depuis l'admin.

    python tools/build_blog_sql.py <fichier.sql>
    python tools/apply_sql.py <url SQLAlchemy> <fichier.sql>
"""
import json
import re
import sys
from pathlib import Path

BLOG = Path(__file__).resolve().parents[2] / "database" / "blog"
IMAGES = "/assets/images/blog/"


def sql(value):
    return "'" + str(value).replace("'", "''") + "'"


def one_line(html):
    return re.sub(r"\s*\n\s*", " ", html).strip()


def statement(a):
    content = one_line((BLOG / f"{a['slug']}.html").read_text(encoding="utf-8"))
    image = IMAGES + a["slug"] + ".webp"
    cols = {
        "title": sql(a["title"]), "slug": sql(a["slug"]),
        "category_id": f"(SELECT id FROM service_categories WHERE slug = {sql(a['category'])})",
        "service_name": sql(a["service_name"]), "excerpt": sql(a["excerpt"]), "content": sql(content),
        "meta_title": sql(a["meta_title"]), "meta_description": sql(a["meta_description"]),
        "meta_keywords": sql(a["meta_keywords"]), "featured_image": sql(image), "image_url": sql(image),
        "status": "'draft'", "created_at": "NOW()", "updated_at": "NOW()",
    }
    return (f"INSERT INTO blog_articles ({', '.join(cols)})\nVALUES ({', '.join(cols.values())})\n"
            "ON CONFLICT (slug) DO NOTHING;\n")


def main(out):
    articles = json.loads((BLOG / "articles.json").read_text(encoding="utf-8"))
    for a in articles:
        assert len(a["meta_title"]) <= 60 and len(a["meta_description"]) <= 160, a["slug"]
    header = ("-- Articles du blog en brouillon, générés par python/tools/build_blog_sql.py depuis database/blog/.\n"
              "-- Ne pas modifier à la main : éditer les fichiers sources puis régénérer.\n")
    Path(out).write_text(header + "\n".join(statement(a) for a in articles), encoding="utf-8")
    print(f"{len(articles)} articles -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
