"""Projets clients (ProjectController.php) : brief, devis, espace client, messagerie,
et le webhook Webox (AdminProjectController::webhookWebox, réservé aux admins comme en PHP)."""
import json
import logging
import re
import time

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import config, php, security
from ..forms import php_post
from ..models import project as Project
from ..render import render_view
from ..services import agents, ines
from .analytics import _require_admin
from .common import redirect

log = logging.getLogger("digita")

ALLOWED_EXT = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "xls", "xlsx", "zip", "txt"]


def _login(request, back):
    request.session["redirect_after_login"] = back
    return redirect("/connexion")


def brief_form(request):
    return render_view(request, "projects/brief-form-content", {
        "title": "Créer votre projet — Digita Marketing",
        "metaDescription": "Décrivez votre projet et recevez un devis automatique pour la création de votre "
                           "site web, e-commerce ou landing page.",
        "projectTypes": Project.TYPES,
    })


def _colors(raw):
    # array_filter(explode(',', …)) garde les clés : objet JSON si un trou apparaît.
    kept = {i: c for i, c in enumerate(php.explode(",", raw)) if php.t(c)}
    return list(kept.values()) if list(kept) == list(range(len(kept))) else {str(k): v for k, v in kept.items()}


async def submit_brief(request):
    if "user_id" not in request.session:
        return _login(request, "/projets/brief")
    post = php_post(await request.form())
    return await run_in_threadpool(_submit_brief, request, post)


def _submit_brief(request, post):
    user_id = request.session["user_id"]
    project_type = post.get("project_type", "")
    title = php.trim(post.get("title", ""))
    brief = php.trim(post.get("brief", ""))
    if php.empty(project_type) or php.empty(title) or php.empty(brief):
        request.session["error_message"] = "Veuillez remplir tous les champs obligatoires."
        return redirect("/projets/brief")

    brief_data = {
        "business_name": php.trim(post.get("business_name", "")),
        "business_type": php.trim(post.get("business_type", "")),
        "target_audience": php.trim(post.get("target_audience", "")),
        "style": post.get("style", "modern"),
        "colors": _colors(post.get("colors", "")),
        "pages": php.intval(post.get("pages", 5)),
        "features": post.get("features", []),
        "content_tone": post.get("content_tone", "professionnel"),
        "existing_url": php.trim(post.get("existing_url", "")),
        "competitors": php.trim(post.get("competitors", "")),
        "deadline": post.get("deadline", ""),
        "budget": post.get("budget", ""),
        "urgent": not php.empty(post.get("urgent")),
    }
    project_id = Project.create_from_brief(user_id, {
        "project_type": project_type,
        "title": title,
        "brief": brief,
        "brief_data": brief_data,
        "price": Project.calculate_quote(project_type, brief_data),
        "estimated_days": Project.ESTIMATED_DAYS.get(project_type, 7),
        "priority": "high" if brief_data["urgent"] else "normal",
    })
    if project_id:
        ines.push_lead(brief_data["business_name"] or title, request.session.get("user_email"), "projet",
                       f"Brief projet #{project_id} ({project_type}) : {title}\n{brief}")
        request.session["success_message"] = ("Votre projet a été soumis avec succès ! "
                                               "Notre équipe va l'examiner rapidement.")
        return redirect("/espace-client/projet/" + project_id)
    request.session["error_message"] = "Erreur lors de la création du projet."
    return redirect("/projets/brief")


async def ajax_quote(request):
    post = php_post(await request.form())
    q = request.query_params

    def pick(name, default):
        return post[name] if name in post else q[name] if name in q else default

    project_type = pick("project_type", "website")
    brief_data = {
        "pages": php.intval(pick("pages", 5)),
        "multilingual": not php.empty(pick("multilingual", False)),
        "urgent": not php.empty(pick("urgent", False)),
    }
    price = Project.calculate_quote(project_type, brief_data)
    return Response(php.json_encode({
        "success": True,
        "price": price,
        "formatted": php.number_format(price, 2, ",", " ") + " €",
    }), media_type="application/json")


def dashboard(request):
    if "user_id" not in request.session:
        return _login(request, "/espace-client")
    user_id = request.session["user_id"]
    projects = Project.get_client_projects(user_id)
    context = agents.get_context(security.session_id(request), user_id)
    return render_view(request, "projects/client-dashboard-content", {
        "title": "Espace Client — Digita Marketing",
        "projects": projects,
        "activeProjects": [p for p in projects if p["status"] not in ("completed", "cancelled", "draft")],
        "completedProjects": [p for p in projects if p["status"] == "completed"],
        "unreadMessages": Project.count_unread_for_client(user_id),
        "clientContext": context,
        "maturityScore": agents.calculate_maturity_score(context, projects),
        "statuses": Project.STATUSES,
        "types": Project.TYPES,
    })


def show(request, project_id):
    if "user_id" not in request.session:
        return _login(request, "/espace-client/projet/" + project_id)
    if not Project.belongs_to_client(project_id, request.session["user_id"]):
        request.session["error_message"] = "Projet introuvable."
        return redirect("/espace-client")
    project = Project.get_full_project(project_id)
    if not project:
        return redirect("/espace-client")
    Project.mark_messages_read(project_id, False)
    return render_view(request, "projects/client-project-content", {
        "title": php.strval(project["title"]) + " — Espace Client",
        "project": project,
        "statuses": Project.STATUSES,
        "types": Project.TYPES,
    })


async def send_message(request, project_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    form = await request.form()
    upload = form.get("attachment")
    data = None
    if upload is not None and not isinstance(upload, str) and upload.filename:
        data = (upload.filename, await upload.read())
    return await run_in_threadpool(_send_message, request, project_id, php_post(form), data)


def _send_message(request, project_id, post, upload):
    user_id = request.session["user_id"]
    if not Project.belongs_to_client(project_id, user_id):
        request.session["error_message"] = "Projet introuvable."
        return redirect("/espace-client")
    message = php.trim(post.get("message", ""))
    if php.empty(message):
        request.session["error_message"] = "Le message ne peut pas être vide."
        return redirect("/espace-client/projet/" + project_id)
    attachment = _store_upload(project_id, user_id, *upload) if upload else None
    Project.add_message(project_id, user_id, message, False, attachment)
    request.session["success_message"] = "Message envoyé."
    return redirect("/espace-client/projet/" + project_id + "#messages")


def _store_upload(project_id, user_id, name, content):
    upload_dir = config.PUBLIC_DIR / "uploads" / "projects" / project_id
    # Le PHP crée le dossier avant de valider le fichier ; on attend qu'il soit accepté.
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT or len(content) > 10 * 1024 * 1024:
        return None
    # Le nom vient de l'URL : on refuse tout ce qui sortirait du dossier uploads/projects.
    if not re.fullmatch(r"[^/\\]+", project_id) or project_id in (".", ".."):
        return None
    filename = f"{int(time.time())}_" + re.sub(r"[^a-zA-Z0-9._-]", "", name)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(content)
    public_path = f"/uploads/projects/{project_id}/{filename}"
    Project.add_file(project_id, user_id, {
        "filename": name, "filepath": public_path, "filetype": ext, "filesize": len(content),
    })
    return public_path


async def webhook_webox(request):
    denied = _require_admin(request)
    if denied:
        return denied
    try:
        payload = json.loads(await request.body())
    except ValueError:
        payload = None
    if php.empty(payload):
        return Response(php.json_encode({"error": "Payload vide"}), status_code=400, media_type="text/html")
    result = await run_in_threadpool(_handle_webox, payload if isinstance(payload, dict) else {})
    return Response(php.json_encode({"success": result}), status_code=200 if result else 400,
                    media_type="text/html")


def _handle_webox(payload):
    """WeboxBridge::handleWebhook."""
    event = payload.get("event", "")
    data = payload.get("data") or {}
    if not isinstance(data, dict):
        data = {}
    if event not in ("website.generated", "website.deployed", "website.error"):
        log.warning("WeboxBridge: événement webhook inconnu: %s", event)
        return False
    webox_id = data.get("project_id", "")
    if php.empty(webox_id):
        return False
    project = Project.find_by_webox_id(webox_id)
    if not project:
        if event == "website.generated":
            log.warning("WeboxBridge: projet non trouvé pour webox_id: %s", webox_id)
        return False
    pid, client = project["id"], project["client_id"]
    if event == "website.generated":
        url = data.get("preview_url", "")
        Project.update(pid, {"preview_url": url})
        Project.update_status(pid, "review", client, "Site généré par Webox IA — en attente de révision")
        Project.add_message(pid, client, "Votre site a été généré ! Vous pouvez le prévisualiser ici : "
                            + php.strval(url), True)
    elif event == "website.deployed":
        url = data.get("production_url", "")
        Project.update(pid, {"production_url": url})
        Project.update_status(pid, "delivered", client, "Site déployé en production")
        Project.add_message(pid, client, "Votre site est en ligne ! URL : " + php.strval(url), True)
    else:
        error = data.get("error", "Erreur inconnue")
        Project.update_status(pid, "pending", client, "Erreur Webox: " + php.strval(error))
        log.error("WeboxBridge erreur projet #%s: %s", pid, error)
    return True
