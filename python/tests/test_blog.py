"""Articles du blog : page article (auteur, données structurées, HTML) et articles de database/blog/."""
import json
import re
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from digita import sessions
from digita.main import app
from digita.models import article as Article
from digita.models import formation as Formation

ROOT = Path(__file__).resolve().parents[2]
BLOG = ROOT / "database" / "blog"
ARTICLES = json.loads((BLOG / "articles.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def memory_sessions(monkeypatch):
    store = {}
    monkeypatch.setattr(sessions, "_load", lambda sid: store.get(sid))
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: store.__setitem__(sid, data))


@pytest.fixture
def article_page(monkeypatch):
    meta = ARTICLES[0]
    row = {"id": 1, "slug": meta["slug"], "title": meta["title"], "excerpt": meta["excerpt"],
           "content": (BLOG / f"{meta['slug']}.html").read_text(encoding="utf-8"),
           "meta_title": meta["meta_title"], "meta_description": meta["meta_description"], "meta_keywords": "",
           "featured_image": "/assets/images/blog/x.webp", "image_url": "/assets/images/blog/x.webp",
           "category_id": 4, "category_name": "Création Web", "category_slug": "creation-web",
           "views": 0, "published_at": "2026-11-16 08:00:00", "created_at": "2026-11-08", "updated_at": "2026-11-08"}
    monkeypatch.setattr(Article, "get_by_slug", lambda slug: dict(row) if slug == row["slug"] else None)
    monkeypatch.setattr(Article, "get_related", lambda *a: [])
    monkeypatch.setattr(Article, "get_popular", lambda *a: [])
    monkeypatch.setattr(Formation, "get_related", lambda *a: [])
    return TestClient(app, base_url="https://digita.buzz").get("/blog/" + row["slug"]).text


def _json_ld(html):
    return {d["@type"]: d for d in (json.loads(b) for b in
            re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S))}


def test_article_page_shows_author_and_html_body(article_page):
    assert "fondateur-anthony-legros.webp" in article_page and "Anthony Legros" in article_page
    assert '<div class="en-bref">' in article_page and "&lt;div" not in article_page
    # Le HTML n'est pas repassé dans la conversion Markdown (qui enveloppait tout dans un <ul>)
    assert '<ul class="list-unstyled my-4">' not in article_page
    assert 'href="/diagnostic"' in article_page and 'og:image" content="https://digita.buzz/assets/images/blog/x.webp' in article_page


def test_article_structured_data(article_page):
    ld = _json_ld(article_page)
    post = ld["BlogPosting"]
    assert post["author"]["@type"] == "Person" and post["author"]["name"] == "Anthony Legros"
    assert post["headline"] == ARTICLES[0]["meta_title"] and post["image"].startswith("https://")
    questions = [q["name"] for q in ld["FAQPage"]["mainEntity"]]
    assert "Le nom de domaine m'appartient-il ?" in questions  # apostrophe intacte, pas &#039;
    assert not any(q.startswith("Landing, site vitrine") for q in questions)  # un <h2> n'est pas une FAQ


@pytest.mark.parametrize("meta", ARTICLES, ids=lambda m: m["slug"])
def test_article_sources(meta):
    html = (BLOG / f"{meta['slug']}.html").read_text(encoding="utf-8")
    assert len(meta["meta_title"]) <= 60 and len(meta["meta_description"]) <= 160
    assert (ROOT / "public" / "assets" / "images" / "blog" / f"{meta['slug']}.webp").exists()
    assert html.count("<h2>") >= 4 and 'class="article-sources"' in html and 'class="en-bref"' in html
    assert "\n\n" not in html  # le gabarit transformerait une ligne vide en paragraphe
    # Pas de références clients inventées : les exemples sont annoncés comme fictifs
    assert "nos clients" not in html.lower()
    assert all("fictif" in e for e in re.findall(r'<p class="encadre-titre">Exemple[^<]*', html))


def test_build_sql_inserts_drafts_on_one_line(tmp_path):
    sys.path.insert(0, str(ROOT / "python" / "tools"))
    import build_blog_sql
    out = tmp_path / "blog.sql"
    build_blog_sql.main(out)
    sql = out.read_text(encoding="utf-8")
    assert sql.count("INSERT INTO blog_articles") == len(ARTICLES) == sql.count("ON CONFLICT (slug) DO NOTHING;")
    assert "'published'" not in sql and sql.count("'draft'") == len(ARTICLES)
    # apply_sql.py coupe aux « ; » de fin de ligne : seules les fins d'instruction en ont
    assert len(re.findall(r";\s*$", sql, re.M)) == len(ARTICLES)


def test_category_and_search_pages_use_site_style(monkeypatch):
    from digita import db
    from digita.routes import blog as blog_routes

    art = {"slug": "page-facebook-piratee", "title": "Page Facebook piratée", "excerpt": "Que faire tout de suite.",
           "category_name": "Réseaux sociaux", "category_slug": "reseaux", "published_at": "2026-11-02 10:00:00", "views": 3}
    cats = [{"slug": "reseaux", "name": "Réseaux sociaux", "article_count": 1}]
    monkeypatch.setattr(blog_routes.Article, "get_by_category", lambda slug, n: [art])
    monkeypatch.setattr(blog_routes.Article, "count", lambda slug=None: 1)
    monkeypatch.setattr(blog_routes.Article, "get_categories", lambda: cats)
    monkeypatch.setattr(blog_routes.Article, "search", lambda q, n: [art] if q == "facebook" else [])
    monkeypatch.setattr(blog_routes.Article, "get_popular", lambda n: [art])
    monkeypatch.setattr(db, "fetch", lambda sql, params=None: {"slug": "reseaux", "name": "Réseaux sociaux", "description": ""}
                        if "service_categories" in sql else None)
    c = TestClient(app, base_url="https://digita.buzz")
    page = c.get("/blog/categorie/reseaux").text
    assert 'class="pg-hero"' in page and "Page Facebook piratée" in page and "02/11/2026" in page
    assert "bg-light" not in page.split('id="contenu"')[1].split("footer-premium")[0] and "1 article pour" in page
    found = c.get("/blog/search?q=facebook").text
    assert "Résultats pour « facebook »" in found and "1 article trouvé" in found
    empty = c.get("/blog/search?q=zzz").text
    assert "Aucun article ne correspond" in empty and "Les articles les plus lus" in empty
