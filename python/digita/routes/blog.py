"""Blog (équivalent de BlogController.php)."""
import math

from ..models import article as Article
from ..models import formation as Formation
from ..render import render_page, render_view
from .common import not_found, page_param, redirect
from .. import db, php


def index(request):
    page = page_param(request)
    per_page = 12
    total = Article.count()
    return render_view(request, "blog/index-content", {
        "title": "Blog - Actualités & Conseils | Digita Marketing",
        "metaDescription": "Découvrez nos articles sur le marketing digital, l'automatisation, l'IA et les stratégies de croissance. Conseils d'experts pour développer votre activité.",
        "metaKeywords": "blog marketing digital, conseils SEO, automatisation, intelligence artificielle, stratégie digitale",
        "extraCss": ["/assets/css/blog-layout.css"],
        "totalArticles": total,
        "articles": Article.get_all_published(per_page, (page - 1) * per_page),
        "popularArticles": Article.get_popular(5),
        "recentArticles": Article.get_recent(5),
        "categories": Article.get_categories(),
        "currentPage": page,
        "totalPages": float(math.ceil(total / per_page)),
    })


def show(request, slug):
    article = Article.get_by_slug(slug)
    if not article:
        return not_found(request, slug=slug, article=article)
    related = Article.get_related(article["id"], article["category_id"], 3)
    popular = Article.get_popular(5)
    related_formation = None
    if php.t(article.get("category_id")):
        rows = Formation.get_related(0, article["category_id"], 1)
        related_formation = rows[0] if rows else None

    content = article.get("content") or ""
    reading_time = Article.estimate_reading_time(content)
    toc = Article.generate_table_of_contents(content)
    article["content"] = toc["content"]
    faq = Article.extract_faq(article["content"] or "")

    from ..render import base_context
    base = base_context(request)["base_url"]
    crumbs = [{"name": "Accueil", "url": base + "/"}, {"name": "Blog", "url": base + "/blog"}]
    if php.t(article.get("category_name")):
        crumbs.append({"name": article["category_name"], "url": base + "/blog/categorie/" + php.strval(article["category_slug"])})
    crumbs.append({"name": article["title"], "url": base + "/blog/" + article["slug"]})

    desc = (article.get("meta_description") or "") or php.mb_strimwidth(php.strip_tags(article["content"]), 0, 155, "...")
    title = (article.get("meta_title") or "") or article["title"]
    return render_view(request, "blog/show-content", {
        "title": title + " | Digita Marketing",
        "metaDescription": desc,
        "metaKeywords": article.get("meta_keywords") or "",
        "ogType": "article",
        "ogTitle": title,
        "ogDescription": desc,
        "ogImage": article["featured_image"] if php.t(article.get("featured_image")) else None,
        "schemaType": "article",
        "schemaData": article,
        "breadcrumbs": crumbs,
        "extraCss": ["/assets/css/blog-layout.css"],
        "article": article,
        "readingTime": reading_time,
        "tableOfContents": toc["toc"],
        "faqSchema": faq,
        "relatedFormation": related_formation,
        "relatedArticles": related,
        "popularArticles": popular,
    })


def category(request, slug):
    page = page_param(request)
    per_page = 12
    articles = Article.get_by_category(slug, per_page)
    total = Article.count(slug)
    categories = Article.get_categories()
    cat = db.fetch("SELECT * FROM service_categories WHERE slug = ?", [slug])
    if not cat:
        return not_found(request, categorySlug=slug, articles=articles, categories=categories)
    return render_view(request, "blog/category-content", {
        "title": cat["name"] + " - Blog Digita Marketing",
        "extraCss": ["/assets/css/blog-layout.css"],
        "category": cat,
        "articles": articles,
        "totalArticles": total,
        "page": page,
        "totalPages": float(math.ceil(total / per_page)),
        "categories": categories,
    })


def search(request):
    query = php.trim(request.query_params.get("q", ""))
    if php.empty(query):
        return redirect("/blog")
    return render_page(request, "app/Views/blog/search.html", {
        "query": query,
        "articles": Article.search(query, 50),
        "categories": Article.get_categories(),
        "popularArticles": Article.get_popular(5),
    })
