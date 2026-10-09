"""Administration (AdminController, AdminArticleController, AdminFormationController,
AdminMediaController, AdminProjectController, AnalyticsController::index).

Chaque contrôleur PHP appelle requireAdmin() dans son constructeur : visiteur → /connexion,
compte non administrateur → accueil. Les vues sont rendues dans layouts/admin, qui inclut
la vue de contenu (Controller::viewWithLayout).
"""
import mimetypes
import os
import time as _time

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import config, php
from ..forms import php_post
from ..models import admin as Admin
from ..models import article as Article
from ..models import formation as Formation
from ..models import project as Project
from ..render import render_page
from ..services import webox
from .analytics import _require_admin
from .common import redirect

IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
# Le PHP garde l'extension envoyée par le navigateur ; on la limite au type annoncé pour qu'un
# fichier .html ou .svg ne puisse pas passer pour une image.
IMAGE_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
MEDIA_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
               "application/pdf", "video/mp4", "video/webm"]
MEDIA_EXT = IMAGE_EXT | {"svg", "pdf", "mp4", "webm"}


# ---------------------------------------------------------------- outils communs
def admin_only(fn):
    """requireAdmin() du constructeur, avant tout le reste."""
    if hasattr(fn, "__wrapped_admin__"):
        return fn

    async def wrapper(request, *args):
        denied = _require_admin(request)
        if denied:
            return denied
        files = {}
        post = {}
        if request.method == "POST":
            form = await request.form()
            post = php_post(form)
            for name, value in form.multi_items():
                if not isinstance(value, str):
                    files.setdefault(name, []).append((value.filename or "", value.content_type or "",
                                                       await value.read()))
        request.state.post = post
        request.state.files = files
        return await run_in_threadpool(fn, request, *args)

    wrapper.__wrapped_admin__ = True
    wrapper.__name__ = fn.__name__
    return wrapper


def _view(request, view, data):
    return render_page(request, "app/Views/layouts/admin.html", {**data, "contentView": view})


def _json(payload, status=200):
    return Response(php.json_encode(payload), status_code=status, media_type="application/json")


def _current_user(request):
    return Admin.find_user(request.session["user_id"]) if "user_id" in request.session else None


def _flash(request, kind, message):
    request.session[kind + "_message"] = message


def _db_error(exc):
    # Database::query : « Erreur d'exécution de la requête : » + message du pilote.
    orig = getattr(exc, "orig", exc)
    return "Erreur d'exécution de la requête : " + str(orig).strip().splitlines()[0]


def _uniqid(prefix=""):
    t = _time.time()
    return f"{prefix}{int(t):08x}{int((t % 1) * 1_000_000):05x}"


def _page(request):
    q = request.query_params
    return max(1, php.intval(q["page"])) if "page" in q else 1


def _get(request, name):
    return request.query_params.get(name)


def _store_image(upload, folder, prefix):
    """handleImageUpload() des contrôleurs articles et formations."""
    name, ctype, content = upload
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ctype not in IMAGE_TYPES or len(content) > 5 * 1024 * 1024 or ext.lower() not in IMAGE_EXT:
        return None
    target = config.PUBLIC_DIR / "uploads" / folder
    target.mkdir(parents=True, exist_ok=True)
    filename = _uniqid(prefix) + "." + ext
    (target / filename).write_bytes(content)
    return f"/uploads/{folder}/{filename}"


def _upload(request, field):
    items = request.state.files.get(field) or []
    item = items[-1] if items else None
    return item if item and item[0] else None  # UPLOAD_ERR_NO_FILE sinon


# ---------------------------------------------------------------- AdminController
@admin_only
def dashboard(request):
    contact = Admin.contact_stats()
    newsletter = Admin.newsletter_stats()
    project_stats = Admin.project_stats()
    stats = {
        "contacts": {k: contact[k] for k in ("total", "new", "today", "this_week", "this_month")},
        "newsletters": {k: newsletter[k] for k in ("total", "active", "today", "this_week", "this_month")},
        "users": Admin.user_stats(),
        "articles": Article.get_stats(),
        "formations": Formation.get_formation_stats(),
        "projects": project_stats,
        "conversion_rate": php.php_round(newsletter["active"] / contact["total"] * 100, 1)
        if contact["total"] > 0 else 0,
    }
    return _view(request, "admin/dashboard", {
        "pageTitle": "Dashboard",
        "stats": stats,
        "projectStats": project_stats,
        "recentContacts": Admin.contacts(5),
        "recentNewsletters": Admin.recent_newsletters(5),
        "newMessages": Admin.new_contacts(),
        "currentUser": _current_user(request),
    })


@admin_only
def contacts(request):
    return _view(request, "admin/contacts", {
        "pageTitle": "Messages de contact",
        "contacts": Admin.contacts(),
        "stats": Admin.contact_stats(),
        "currentUser": _current_user(request),
    })


def _contact_status(status):
    @admin_only
    def mark(request):
        Admin.set_contact_status(request.query_params["id"], status)
        return redirect("/admin/contacts")

    async def route(request):
        # La route PHP ne crée le contrôleur (et ne vérifie l'accès) que si ?id= est fourni.
        if php.empty(request.query_params.get("id")):
            return Response(b"", media_type="text/html")
        return await mark(request)

    return route


contact_read = _contact_status("read")
contact_replied = _contact_status("replied")


@admin_only
def newsletters(request):
    return _view(request, "admin/newsletters", {
        "pageTitle": "Abonnés newsletter",
        "newsletters": Admin.newsletters(),
        "stats": Admin.newsletter_stats(),
        "currentUser": _current_user(request),
    })


def fputcsv(row):
    """fputcsv() : guillemets autour des champs contenant , " espace tabulation ou saut de ligne."""
    out = []
    for v in row:
        s = php.strval(v)
        if any(c in s for c in ',"\n\r\t ') or "\\" in s:
            s = '"' + s.replace('"', '""') + '"'
        out.append(s)
    return ",".join(out) + "\n"


@admin_only
def export_newsletters(request):
    body = fputcsv(["Email", "Date"]) + "".join(
        fputcsv([s["email"], s["created_at"]]) for s in Admin.active_newsletters())
    return Response(body, media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="newsletter_emails_{php.date("Y-m-d")}.csv"'})


@admin_only
def logout(request):
    request.session.clear()
    return redirect("/connexion")


@admin_only
def webhooks(request):
    return _view(request, "admin/webhooks", {
        "pageTitle": "Webhooks",
        "webhooks": {"contact_url": "", "contact_enabled": False, "newsletter_url": "",
                     "newsletter_enabled": False, "system_url": "", "system_enabled": False},
        "currentUser": request.session,
    })


@admin_only
def save_webhooks(request):
    return redirect("/admin/webhooks")


@admin_only
def test_webhook(request, _type):
    return _json({"success": True, "message": "Webhook de test envoyé"})


CAMPAIGNS = [
    {"id": 1, "name": "Newsletter Octobre 2025", "description": "Newsletter mensuelle avec les dernières actualités",
     "type": "newsletter", "recipients": 150, "sent": 150, "opened": 98, "clicked": 45, "open_rate": 65,
     "click_rate": 30, "status": "completed", "created_at": "2025-10-01 10:00:00"},
    {"id": 2, "name": "Promotion Spéciale", "description": "Offre limitée sur nos services", "type": "promotion",
     "recipients": 200, "sent": 200, "opened": 145, "clicked": 78, "open_rate": 72, "click_rate": 39,
     "status": "active", "created_at": "2025-10-15 14:30:00"},
    {"id": 3, "name": "Nouvelle Campagne", "description": "En cours de préparation", "type": "newsletter",
     "recipients": 0, "sent": 0, "opened": 0, "clicked": 0, "open_rate": 0, "click_rate": 0, "status": "draft",
     "created_at": "2025-10-25 09:00:00"},
]


@admin_only
def campaigns(request):
    # Données de démonstration écrites en dur dans le contrôleur PHP.
    return _view(request, "admin/campaigns", {
        "pageTitle": "Campagnes Marketing",
        "campaigns": [dict(c) for c in CAMPAIGNS],
        "stats": {"total": len(CAMPAIGNS), "active": sum(c["status"] == "active" for c in CAMPAIGNS),
                  "draft": sum(c["status"] == "draft" for c in CAMPAIGNS), "open_rate": 68},
        "currentUser": request.session,
    })


@admin_only
def new_campaign(request):
    return redirect("/admin/campaigns")


@admin_only
def delete_campaign(request, _id):
    return _json({"success": True, "message": "Campagne supprimée"})


# ---------------------------------------------------------------- articles
def _listing(request, model, view, title, plural, total_key):
    q = request.query_params
    page = _page(request)
    status, category, search = q.get("status"), q.get("category"), q.get("q")
    items = model.get_all(20, (page - 1) * 20, status, category, search)
    total = model.count_all(status, category, search)
    return _view(request, view, {
        "pageTitle": title,
        plural: items,
        "categories": model.get_all_categories(),
        "stats": model.get_stats() if model is Article else model.get_formation_stats(),
        "currentPage": page,
        "totalPages": php.ceil(total / 20),
        total_key: total,
        "filterStatus": status,
        "filterCategory": category,
        "filterSearch": search,
        "currentUser": _current_user(request),
    })


@admin_only
def articles(request):
    return _listing(request, Article, "admin/articles/index", "Gestion des articles", "articles", "totalArticles")


@admin_only
def article_new(request):
    return _view(request, "admin/articles/form", {
        "pageTitle": "Nouvel article", "categories": Article.get_all_categories(), "article": None,
        "currentUser": _current_user(request)})


def _article_form(post):
    return {
        "title": php.trim(post.get("title", "")),
        "content": post.get("content", ""),
        "excerpt": php.trim(post.get("excerpt", "")),
        "category_id": post.get("category_id"),
        "service_name": php.trim(post.get("service_name", "")),
        "meta_title": php.trim(post.get("meta_title", "")),
        "meta_description": php.trim(post.get("meta_description", "")),
        "meta_keywords": php.trim(post.get("meta_keywords", "")),
        "featured_image": php.trim(post.get("featured_image_url", "")),
        "status": post.get("status", "draft"),
    }


@admin_only
def article_store(request):
    data = _article_form(request.state.post)
    if php.empty(data["title"]):
        _flash(request, "error", "Le titre est obligatoire.")
        return redirect("/admin/articles/new")
    data["slug"] = Article.generate_slug(data["title"])
    try:
        new_id = Article.create(data)
    except Exception as exc:  # noqa: BLE001 — même message que le PHP
        _flash(request, "error", "Erreur lors de la création : " + _db_error(exc))
        return redirect("/admin/articles/new")
    _flash(request, "success", "Article créé avec succès.")
    return redirect("/admin/articles/edit/" + new_id)


@admin_only
def article_edit(request, article_id):
    article = Article.get_by_id(article_id)
    if not article:
        _flash(request, "error", "Article introuvable.")
        return redirect("/admin/articles")
    return _view(request, "admin/articles/form", {
        "pageTitle": "Modifier l'article", "categories": Article.get_all_categories(), "article": article,
        "currentUser": _current_user(request)})


@admin_only
def article_update(request, article_id):
    article = Article.get_by_id(article_id)
    if not article:
        _flash(request, "error", "Article introuvable.")
        return redirect("/admin/articles")
    data = _article_form(request.state.post)
    if php.empty(data["title"]):
        _flash(request, "error", "Le titre est obligatoire.")
        return redirect("/admin/articles/edit/" + article_id)
    data["slug"] = (Article.generate_slug(data["title"], article_id) if data["title"] != article["title"]
                    else article["slug"])
    upload = _upload(request, "featured_image")
    if upload:
        path = _store_image(upload, "articles", "article_")
        if path:
            data["featured_image"] = path
    else:
        data["featured_image"] = article["featured_image"]
    try:
        Article.update(article_id, data)
        _flash(request, "success", "Article mis à jour avec succès.")
    except Exception as exc:  # noqa: BLE001
        _flash(request, "error", "Erreur lors de la mise à jour : " + _db_error(exc))
    return redirect("/admin/articles/edit/" + article_id)


@admin_only
def article_delete(request, article_id):
    if not Article.get_by_id(article_id):
        _flash(request, "error", "Article introuvable.")
        return redirect("/admin/articles")
    try:
        Article.delete(article_id)
        _flash(request, "success", "Article supprimé avec succès.")
    except Exception as exc:  # noqa: BLE001
        _flash(request, "error", "Erreur lors de la suppression : " + _db_error(exc))
    return redirect("/admin/articles")


@admin_only
def article_upload_image(request):
    upload = _upload(request, "file")
    if not upload:
        return _json({"error": "Aucun fichier uploadé"})
    path = _store_image(upload, "articles", "article_")
    return _json({"location": path} if path else {"error": "Erreur lors de l'upload"})


# ---------------------------------------------------------------- formations
@admin_only
def formations(request):
    return _listing(request, Formation, "admin/formations/index", "Gestion des formations", "formations",
                    "totalFormations")


@admin_only
def formation_new(request):
    return _view(request, "admin/formations/form", {
        "pageTitle": "Nouvelle formation", "categories": Formation.get_all_categories(), "formation": None,
        "currentUser": _current_user(request)})


def _formation_form(post):
    return {
        "title": php.trim(post.get("title", "")),
        "description": post.get("description", ""),
        "category_id": post.get("category_id"),
        "service_name": php.trim(post.get("service_name", "")),
        "level": post.get("level", "debutant"),
        "duration": php.trim(post.get("duration", "")),
        "price": php.floatval(post.get("price", 0)),
        "image": php.trim(post.get("image_url", "")),
        "meta_title": php.trim(post.get("meta_title", "")),
        "meta_description": php.trim(post.get("meta_description", "")),
        "meta_keywords": php.trim(post.get("meta_keywords", "")),
        "status": post.get("status", "draft"),
    }


@admin_only
def formation_store(request):
    data = _formation_form(request.state.post)
    if php.empty(data["title"]):
        _flash(request, "error", "Le titre est obligatoire.")
        return redirect("/admin/formations/new")
    data["slug"] = Formation.generate_slug(data["title"])
    upload = _upload(request, "image_file")
    if upload:
        path = _store_image(upload, "formations", "formation_")
        if path:
            data["image"] = path
    try:
        new_id = Formation.create(data)
    except Exception as exc:  # noqa: BLE001
        _flash(request, "error", "Erreur lors de la création : " + _db_error(exc))
        return redirect("/admin/formations/new")
    _flash(request, "success", "Formation créée avec succès.")
    return redirect("/admin/formations/edit/" + new_id)


@admin_only
def formation_edit(request, formation_id):
    formation = Formation.get_full_formation_by_id(formation_id)
    if not formation:
        _flash(request, "error", "Formation introuvable.")
        return redirect("/admin/formations")
    return _view(request, "admin/formations/form", {
        "pageTitle": "Modifier la formation", "categories": Formation.get_all_categories(),
        "formation": formation, "currentUser": _current_user(request)})


@admin_only
def formation_update(request, formation_id):
    formation = Formation.get_by_id(formation_id)
    if not formation:
        _flash(request, "error", "Formation introuvable.")
        return redirect("/admin/formations")
    data = _formation_form(request.state.post)
    if php.empty(data["title"]):
        _flash(request, "error", "Le titre est obligatoire.")
        return redirect("/admin/formations/edit/" + formation_id)
    data["slug"] = (Formation.generate_slug(data["title"], formation_id) if data["title"] != formation["title"]
                    else formation["slug"])
    upload = _upload(request, "image_file")
    if upload:
        path = _store_image(upload, "formations", "formation_")
        if path:
            data["image"] = path
    else:
        data["image"] = php.coalesce(formation.get("image"), "")
    try:
        Formation.update(formation_id, data)
        _flash(request, "success", "Formation mise à jour avec succès.")
    except Exception as exc:  # noqa: BLE001
        _flash(request, "error", "Erreur lors de la mise à jour : " + _db_error(exc))
    return redirect("/admin/formations/edit/" + formation_id)


@admin_only
def formation_delete(request, formation_id):
    if not Formation.get_by_id(formation_id):
        _flash(request, "error", "Formation introuvable.")
        return redirect("/admin/formations")
    try:
        Formation.delete(formation_id)
        _flash(request, "success", "Formation supprimée avec succès.")
    except Exception as exc:  # noqa: BLE001
        _flash(request, "error", "Erreur lors de la suppression : " + _db_error(exc))
    return redirect("/admin/formations")


# ---------------------------------------------------------------- médias
def _media_dirs():
    up = config.PUBLIC_DIR / "uploads"
    return [(up / "media", "/uploads/media/"), (up / "articles", "/uploads/articles/"),
            (up / "formations", "/uploads/formations/")]


def _scan_media():
    files = []
    for folder, web in _media_dirs():
        if not folder.is_dir():
            continue
        for name in sorted(os.listdir(folder)):
            full = folder / name
            if not full.is_file():
                continue
            # mime_content_type() lit le contenu ; ici le type vient de l'extension.
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            kind = ("image" if mime.startswith("image/") else "video" if mime.startswith("video/")
                    else "pdf" if mime == "application/pdf" else "other")
            st = full.stat()
            files.append({
                "name": name, "url": web + name, "path": str(full), "size": st.st_size, "type": kind,
                "mime": mime, "extension": name.rsplit(".", 1)[-1].lower() if "." in name else "",
                "modified": int(st.st_mtime), "folder": folder.name,
            })
    return files


def _media_dir():
    d = config.PUBLIC_DIR / "uploads" / "media"
    d.mkdir(parents=True, exist_ok=True)
    return d


@admin_only
def media(request):
    _media_dir()
    files = sorted(_scan_media(), key=lambda f: -f["modified"])
    return _view(request, "admin/media/index", {
        "pageTitle": "Bibliothèque de médias",
        "files": files,
        "stats": {"total": len(files), "total_size": sum(f["size"] for f in files),
                  "images": sum(f["type"] == "image" for f in files)},
        "currentUser": _current_user(request),
    })


@admin_only
def media_upload(request):
    target = _media_dir()
    files = request.state.files.get("files[]") or request.state.files.get("files")
    if not files:
        return _json({"success": False, "error": "Aucun fichier envoyé"})
    uploaded, errors = [], []
    for name, ctype, content in files:
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if not name:
            errors.append(name + " : erreur d'upload")
        elif ctype not in MEDIA_TYPES or ext not in MEDIA_EXT:
            errors.append(f"{name} : type non autorisé ({ctype})")
        elif len(content) > 10 * 1024 * 1024:
            errors.append(name + " : fichier trop volumineux (max 10 Mo)")
        else:
            filename = php.date("Y-m-d_") + _uniqid() + "." + ext
            (target / filename).write_bytes(content)
            uploaded.append({"name": filename, "url": "/uploads/media/" + filename, "size": len(content),
                             "type": ctype})
    return _json({"success": len(uploaded) > 0, "uploaded": uploaded, "errors": errors})


@admin_only
def media_delete(request):
    target = _media_dir()
    filename = request.state.post.get("filename", "")
    if php.empty(filename):
        return _json({"success": False, "error": "Nom de fichier manquant"})
    filename = php.strval(filename).rstrip("/").rsplit("/", 1)[-1]  # basename()
    path = target / filename
    if not filename or not os.path.lexists(path):
        return _json({"success": False, "error": "Fichier introuvable"})
    try:
        path.unlink()
    except OSError:
        return _json({"success": False, "error": "Impossible de supprimer le fichier"})
    return _json({"success": True, "message": "Fichier supprimé"})


# ---------------------------------------------------------------- analytics
@admin_only
def analytics(request):
    period = request.query_params.get("period", "30")
    date_from = php.date("Y-m-d", php.strtotime(f"-{period} days"))
    data = Admin.analytics(date_from)
    return _view(request, "admin/analytics", {
        "pageTitle": "Analytics", "period": period, **data, "currentUser": _current_user(request)})


# ---------------------------------------------------------------- projets
@admin_only
def projects(request):
    q = request.query_params
    view = q.get("view", "kanban")
    status, ptype = q.get("status"), q.get("type")
    return _view(request, "admin/projects/index", {
        "pageTitle": "Projets Clients",
        "projects": Project.get_all_projects(status, ptype),
        "kanban": Project.get_projects_by_status() if view == "kanban" else [],
        "stats": Admin.project_stats(),
        "unreadMessages": Project.count_unread_for_admin(),
        "statuses": Project.STATUSES,
        "types": Project.TYPES,
        "currentView": view,
        "statusFilter": status,
        "typeFilter": ptype,
        "currentUser": _current_user(request),
    })


@admin_only
def project_show(request, project_id):
    project = Project.get_full_project(project_id)
    if not project:
        _flash(request, "error", "Projet introuvable.")
        return redirect("/admin/projects")
    Project.mark_messages_read(project_id, True)
    return _view(request, "admin/projects/show", {
        "pageTitle": f"Projet #{project_id} — " + php.strval(project["title"]),
        "project": project,
        "statuses": Project.STATUSES,
        "types": Project.TYPES,
        "weboxConnected": webox.health_check(),
        "currentUser": _current_user(request),
    })


@admin_only
def project_status(request, project_id):
    post = request.state.post
    status, note = post.get("status", ""), php.trim(post.get("note", ""))
    if php.empty(status) or not isinstance(status, str) or status not in Project.STATUSES:
        _flash(request, "error", "Statut invalide.")
        return redirect("/admin/projects/" + project_id)
    Project.update_status(project_id, status, request.session["user_id"], note if php.t(note) else None)
    _flash(request, "success", "Statut mis à jour : " + Project.STATUSES[status])
    return redirect("/admin/projects/" + project_id)


@admin_only
def project_message(request, project_id):
    message = php.trim(request.state.post.get("message", ""))
    if php.empty(message):
        _flash(request, "error", "Le message ne peut pas être vide.")
        return redirect("/admin/projects/" + project_id)
    Project.add_message(project_id, request.session["user_id"], message, True)
    _flash(request, "success", "Message envoyé au client.")
    return redirect("/admin/projects/" + project_id + "#messages")


@admin_only
def project_note(request, project_id):
    Project.update(project_id, {"admin_notes": php.trim(request.state.post.get("admin_notes", ""))})
    _flash(request, "success", "Notes mises à jour.")
    return redirect("/admin/projects/" + project_id)


@admin_only
def project_generate(request, project_id):
    project = Project.get_full_project(project_id)
    if not project:
        _flash(request, "error", "Projet introuvable.")
        return redirect("/admin/projects")
    brief = php.json_decode(php.coalesce(project.get("brief_data"), "{}"), True)
    brief = brief if isinstance(brief, dict) else {}
    brief["description"] = project["brief"]
    brief["project_type"] = project["project_type"]
    try:
        response = webox.create_website(brief)
        if isinstance(response, dict) and not php.empty(response.get("project_id")):
            Project.link_webox(project_id, response["project_id"], response.get("preview_url"))
            Project.update_status(project_id, "generating", request.session["user_id"],
                                  "Génération lancée via Webox IA")
            _flash(request, "success", "Génération lancée ! ID Webox : " + php.strval(response["project_id"]))
        else:
            _flash(request, "error", "Réponse Webox inattendue.")
    except webox.WeboxError as exc:
        _flash(request, "error", "Erreur Webox : " + str(exc))
    return redirect("/admin/projects/" + project_id)


@admin_only
def project_task(request, project_id):
    post = request.state.post
    title, description = php.trim(post.get("task_title", "")), php.trim(post.get("task_description", ""))
    if php.empty(title):
        _flash(request, "error", "Le titre de la tâche est requis.")
        return redirect("/admin/projects/" + project_id)
    Project.add_task(project_id, title, description if php.t(description) else None)
    _flash(request, "success", "Tâche ajoutée.")
    return redirect("/admin/projects/" + project_id + "#tasks")


@admin_only
def project_task_update(request):
    post = request.state.post
    task_id, status = post.get("task_id", 0), post.get("status", "")
    if php.empty(task_id) or not isinstance(status, str) or status not in ("todo", "in_progress", "done"):
        return _json({"success": False, "error": "Paramètres invalides"})
    Project.update_task_status(task_id, status)
    return _json({"success": True})


@admin_only
def project_price(request, project_id):
    price = php.floatval(request.state.post.get("price", 0))
    Project.update(project_id, {"price": price})
    _flash(request, "success", "Prix mis à jour : " + php.number_format(price, 2) + " €")
    return redirect("/admin/projects/" + project_id)

