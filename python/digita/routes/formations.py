"""Formations (équivalent de FormationController.php, partie publique)."""
import math

from .. import db, php
from ..models import formation as Formation
from ..render import base_context, render_page, render_view
from .common import not_found, page_param, redirect


def index(request):
    page = page_param(request)
    per_page = 12
    total = Formation.count()
    return render_view(request, "formations/index-content", {
        "title": "Formations - Marketing Digital | Digita",
        "extraCss": ["/assets/css/formations.css"],
        "totalFormations": total,
        "formations": Formation.get_all_published(per_page, (page - 1) * per_page),
        "popularFormations": Formation.get_popular(6),
        "categories": Formation.get_categories(),
        "page": page,
        "totalPages": float(math.ceil(total / per_page)),
    })


def _description(f):
    return f.get("meta_description") if f.get("meta_description") is not None else \
        php.mb_strimwidth(php.strip_tags(f.get("description") or ""), 0, 155, "...")


def show(request, slug):
    f = Formation.get_full_formation(slug)
    if not f:
        return not_found(request, slug=slug, formation=f)
    related = Formation.get_related(f["id"], f["category_id"], 3)
    session = request.session
    user_id = session.get("user_id")
    is_enrolled, progress, user_review = False, None, None
    if user_id is not None:
        is_enrolled = Formation.is_enrolled(user_id, f["id"])
        if is_enrolled:
            progress = Formation.get_progress(user_id, f["id"])
    reviews = Formation.get_reviews(f["id"])
    average = Formation.get_average_rating(f["id"])
    if user_id is not None:
        user_review = Formation.get_user_review(user_id, f["id"])
    base = base_context(request)["base_url"]
    title = f.get("meta_title") if f.get("meta_title") is not None else f["title"]
    return render_view(request, "formations/show-content", {
        "title": title + " | Formations Digita Marketing",
        "metaDescription": _description(f),
        "metaKeywords": f.get("meta_keywords") if f.get("meta_keywords") is not None else "",
        "ogType": "website",
        "ogTitle": title,
        "ogDescription": _description(f),
        "ogImage": f["image"] if php.t(f.get("image")) else None,
        "schemaType": "course",
        "schemaData": f,
        "breadcrumbs": [
            {"name": "Accueil", "url": base + "/"},
            {"name": "Formations", "url": base + "/formations"},
            {"name": f["title"], "url": base + "/formations/" + f["slug"]},
        ],
        "extraCss": ["/assets/css/formations.css"],
        "formation": f,
        "relatedFormations": related,
        "isEnrolled": is_enrolled,
        "progress": progress,
        "reviews": reviews,
        "averageRating": average,
        "userReview": user_review,
    })


def category(request, slug):
    page = page_param(request)
    per_page = 12
    formations = Formation.get_by_category(slug, per_page)
    total = Formation.count(slug)
    categories = Formation.get_categories()
    cat = db.fetch("SELECT * FROM service_categories WHERE slug = ?", [slug])
    if not cat:
        return not_found(request, categorySlug=slug, formations=formations, categories=categories)
    return render_view(request, "formations/category-content", {
        "title": cat["name"] + " - Formations Digita Marketing",
        "extraCss": ["/assets/css/formations.css"],
        "category": cat,
        "formations": formations,
        "categories": categories,
        "totalFormations": total,
        "page": page,
        "totalPages": float(math.ceil(total / per_page)),
    })


def search(request):
    query = php.trim(request.query_params.get("q", ""))
    if php.empty(query):
        return redirect("/formations")
    return render_page(request, "app/Views/formations/search.html", {
        "query": query,
        "formations": Formation.search(query, 50),
        "categories": Formation.get_categories(),
    })


def landing(request, slug):
    f = Formation.get_full_formation(slug)
    if not f:
        return not_found(request, slug=slug, formation=f)
    return render_view(request, "payment/landing-content", {
        "title": f["title"] + " — Formation | Digita Marketing",
        "metaDescription": _description(f),
        "extraCss": ["/assets/css/formations.css"],
        "formation": f,
        "reviews": Formation.get_reviews(f["id"]),
        "averageRating": Formation.get_average_rating(f["id"]),
    })


def verify_certificate(request):
    number = php.trim(request.query_params.get("number", ""))
    cert = None
    if not php.empty(number):
        cert = db.fetch(
            """SELECT c.*, u.username, u.email, f.title as formation_title, f.slug as formation_slug
               FROM certificates c JOIN users u ON c.user_id = u.id JOIN formations f ON c.formation_id = f.id
               WHERE c.certificate_number = ?""", [number])
    return render_view(request, "formations/verify-certificate-content", {
        "title": "Vérification de certificat - Digita Marketing",
        "certificate": cert,
        "searchNumber": number,
    })
