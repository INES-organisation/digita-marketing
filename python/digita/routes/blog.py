"""Blog (équivalent de BlogController.php)."""
import math

from ..models import article as Article
from ..models import formation as Formation
from ..render import render_view
from .common import moved, not_found, page_param, redirect
from .. import content_types, db, php, redirects

# Auteur affiché sous chaque article et dans les données structurées (BlogPosting).
AUTHOR = {
    "name": "Anthony Legros",
    "role": "Fondateur de DIGITA",
    "photo": "/assets/images/v2/fondateur-anthony-legros.webp",
    "url": "/a-propos",
    "bio": "J'aide les TPE et PME de La Réunion à gagner du temps et des clients grâce au web, "
           "aux réseaux sociaux et à l'automatisation. Je crée des sites, des contenus et des "
           "automatisations pour mes propres activités comme pour mes clients.",
}


def absolute(base, url):
    """URL absolue pour Open Graph et schema.org (les images d'articles sont stockées en /assets/...)."""
    return base + url if url and url.startswith("/") else url


def index(request):
    page = page_param(request)
    per_page = 12
    kind = request.query_params.get("type", "")
    ctype = content_types.get(kind)
    if kind and not ctype:
        return redirect("/blog")
    total = Article.count(content_type=kind if ctype else None)
    total_pages = max(1, math.ceil(total / per_page))
    if page > total_pages:
        return redirect("/blog" + (f"?type={kind}" if ctype else ""))
    title = ctype["plural"] + " — Blog" if ctype else "Blog Marketing Digital, IA & Automatisation"
    if page > 1:
        title += f" — page {page}"
    title += " | DIGITA"
    return render_view(request, "blog/index-content", {
        "title": title,
        "metaDescription": (f"{ctype['plural']} du blog DIGITA pour les TPE de La Réunion : {ctype['lead'][0].lower()}{ctype['lead'][1:]}"
                            if ctype else
                            "Conseils pratiques en marketing digital, IA et automatisation pour TPE/PME : gagner du temps, "
                            "trouver des clients et mieux suivre vos prospects."),
        "metaKeywords": "blog marketing digital, conseils SEO, automatisation, intelligence artificielle, stratégie digitale",
        "extraCss": ["/assets/css/blog-layout.css"],
        "totalArticles": total,
        "articles": Article.get_all_published(per_page, (page - 1) * per_page, kind if ctype else None),
        "categories": Article.get_categories(),
        "contentTypes": content_types.TYPES,
        "typeCounts": Article.type_counts(),
        "currentType": kind if ctype else "",
        "page": page,
        "totalPages": total_pages,
    })


def show(request, slug):
    article = Article.get_by_slug(slug)
    if not article:
        if new := redirects.target("article", slug):
            return moved("/blog/" + new)
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
        "title": title + " | DIGITA",
        "metaDescription": desc,
        "metaKeywords": article.get("meta_keywords") or "",
        "ogType": "article",
        "ogTitle": title,
        "ogDescription": desc,
        "ogImage": absolute(base, article["featured_image"]) if php.t(article.get("featured_image")) else None,
        "schemaType": "article",
        "schemaData": article,
        "breadcrumbs": crumbs,
        "extraCss": ["/assets/css/blog-layout.css"],
        "article": article,
        "contentType": content_types.get(article.get("content_type")),
        "readingTime": reading_time,
        "tableOfContents": toc["toc"],
        "faqSchema": faq,
        "relatedFormation": related_formation,
        "relatedArticles": related,
        "popularArticles": popular,
        "author": AUTHOR,
        "authorUrl": base + AUTHOR["url"],
        "authorPhoto": base + AUTHOR["photo"],
        "articleUrl": base + "/blog/" + article["slug"],
    })


def category(request, slug):
    page = page_param(request)
    per_page = 12
    articles = Article.get_by_category(slug, per_page, (page - 1) * per_page)
    total = Article.count(slug)
    categories = Article.get_categories()
    cat = db.fetch("SELECT * FROM service_categories WHERE slug = ?", [slug])
    if not cat:
        return not_found(request, categorySlug=slug, articles=articles, categories=categories)
    return render_view(request, "blog/category-content", {
        "title": cat["name"] + " — Blog | DIGITA",
        "metaDescription": category_meta("Articles", cat),
        "extraCss": ["/assets/css/blog-layout.css"],
        "category": cat,
        "articles": articles,
        "totalArticles": total,
        "page": page,
        "totalPages": float(math.ceil(total / per_page)),
        "categories": categories,
        "contentTypes": content_types.TYPES,
    })


def _category_description(kind, cat):
    """Meta d'une page catégorie : sa description si elle existe, sinon une phrase générique."""
    desc = php.strip_tags(cat.get("description") or "").strip()
    if desc:
        return php.mb_strimwidth(desc, 0, 155, "...")
    return f"{kind} {cat['name']} : conseils pratiques en marketing digital, IA et automatisation pour TPE/PME, par DIGITA."


def category_meta(kind, cat):
    """Blog et formations ont les mêmes catégories et leur description : la meta précise lequel."""
    lead = {"Articles": "Articles du blog DIGITA", "Formations": "Formations en ligne DIGITA"}[kind]
    desc = php.strip_tags(cat.get("description") or "").strip()
    if not desc:
        return _category_description(kind, cat)
    return php.mb_strimwidth(f"{lead} — {cat['name']} : {desc[0].lower() + desc[1:]}", 0, 158, "...")


def search(request):
    query = php.trim(request.query_params.get("q", ""))
    if php.empty(query):
        return redirect("/blog")
    return render_view(request, "blog/search", {
        "title": "Recherche « " + query + " » — Blog | DIGITA", "metaRobots": "noindex, follow",
        "extraCss": ["/assets/css/blog-layout.css"],
        "query": query,
        "articles": Article.search(query, 50),
        "categories": Article.get_categories(),
        "popularArticles": Article.get_popular(5),
        "contentTypes": content_types.TYPES,
    })
