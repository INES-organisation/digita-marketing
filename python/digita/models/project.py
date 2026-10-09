"""Projets clients (équivalent de app/Models/Project.php et ProjectMessage.php, partie client)."""
from .. import db, php
from . import key

STATUSES = {
    "draft": "Brouillon", "pending": "En attente", "generating": "Génération IA", "review": "En révision",
    "revision": "Corrections", "approved": "Approuvé", "delivered": "Livré", "completed": "Terminé",
    "cancelled": "Annulé",
}
TYPES = {
    "website": "Site vitrine", "ecommerce": "E-commerce", "landing": "Landing page",
    "app": "Application web", "seo": "Audit SEO", "marketing": "Stratégie marketing",
}
BASE_PRICES = {"website": 500, "ecommerce": 1200, "landing": 200, "app": 2000, "seo": 300, "marketing": 400}
ESTIMATED_DAYS = {"website": 7, "ecommerce": 14, "landing": 3, "app": 21, "seo": 5, "marketing": 7}


def calculate_quote(project_type, brief):
    price = BASE_PRICES.get(project_type, 500)
    pages = php.intval(brief.get("pages") if brief.get("pages") is not None else 5)
    if pages > 5:
        price += (pages - 5) * 50
    if not php.empty(brief.get("multilingual")):
        price *= 1.3
    if not php.empty(brief.get("urgent")):
        price *= 1.5
    return php.php_round(price, 2)


def create_from_brief(client_id, data):
    row = db.fetch(
        """INSERT INTO client_projects (client_id, project_type, title, brief, brief_data, status, priority,
                                        price, estimated_days)
           VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?) RETURNING id""",
        [client_id, data["project_type"], data["title"], data["brief"],
         php.json_encode(data.get("brief_data") or [], 256), data.get("priority") or "normal",
         data.get("price") or 0, data.get("estimated_days") or 7])
    project_id = str(row["id"])
    _add_status_history(project_id, None, "pending", client_id, "Projet créé depuis le formulaire de brief")
    return project_id


def _add_status_history(project_id, old, new, changed_by, note=None):
    db.execute("INSERT INTO project_status_history (project_id, old_status, new_status, changed_by, note) "
               "VALUES (?, ?, ?, ?, ?)", [project_id, old, new, changed_by, note])


def get_client_projects(client_id):
    return db.fetch_all(
        """SELECT cp.*, (SELECT COUNT(*) FROM project_messages pm WHERE pm.project_id = cp.id
                         AND pm.is_read = 0 AND pm.is_admin = 1) as unread_messages
           FROM client_projects cp WHERE cp.client_id = ?
           ORDER BY cp.updated_at DESC NULLS LAST, cp.id DESC""", [client_id])


def get_full_project(project_id):
    pid = key(project_id)
    project = db.fetch("""SELECT cp.*, u.email as client_email, u.username as client_name
                          FROM client_projects cp JOIN users u ON cp.client_id = u.id WHERE cp.id = ?""", [pid])
    if not project:
        return None
    project["messages"] = db.fetch_all(
        """SELECT pm.*, u.email as user_email, u.username as user_name FROM project_messages pm
           JOIN users u ON pm.user_id = u.id WHERE pm.project_id = ?
           ORDER BY pm.created_at ASC NULLS FIRST, pm.id""", [pid])
    project["files"] = db.fetch_all(
        """SELECT pf.*, u.username as uploaded_by FROM project_files pf JOIN users u ON pf.user_id = u.id
           WHERE pf.project_id = ? ORDER BY pf.created_at DESC NULLS LAST, pf.id DESC""", [pid])
    project["tasks"] = db.fetch_all(
        "SELECT * FROM project_tasks WHERE project_id = ? ORDER BY sort_order ASC NULLS FIRST, id", [pid])
    project["history"] = db.fetch_all(
        """SELECT psh.*, u.username as changed_by_name FROM project_status_history psh
           JOIN users u ON psh.changed_by = u.id WHERE psh.project_id = ?
           ORDER BY psh.created_at DESC NULLS LAST, psh.id DESC""", [pid])
    return project


def belongs_to_client(project_id, client_id):
    return bool(db.fetch("SELECT id FROM client_projects WHERE id = ? AND client_id = ?",
                         [key(project_id), client_id]))


def add_message(project_id, user_id, message, is_admin=False, attachment=None):
    db.execute("INSERT INTO project_messages (project_id, user_id, message, is_admin, attachment) "
               "VALUES (?, ?, ?, ?, ?)", [key(project_id), user_id, message, 1 if is_admin else 0, attachment])


def mark_messages_read(project_id, is_admin):
    db.execute("UPDATE project_messages SET is_read = 1 WHERE project_id = ? AND is_admin = ? AND is_read = 0",
               [key(project_id), 0 if is_admin else 1])


def add_file(project_id, user_id, data):
    db.execute("""INSERT INTO project_files (project_id, user_id, filename, filepath, filetype, filesize, description)
                  VALUES (?, ?, ?, ?, ?, ?, ?)""",
               [key(project_id), user_id, data["filename"], data["filepath"], data.get("filetype"),
                data.get("filesize") or 0, data.get("description")])


def count_unread_for_client(client_id):
    return db.fetch("""SELECT COUNT(*) as total FROM project_messages pm JOIN client_projects cp
                       ON pm.project_id = cp.id WHERE cp.client_id = ? AND pm.is_admin = 1 AND pm.is_read = 0""",
                    [client_id])["total"]


def find_by_webox_id(webox_project_id):
    return db.fetch("SELECT * FROM client_projects WHERE webox_project_id = ?", [webox_project_id])


def update(project_id, data):
    # Model::update : colonnes fournies par le code, jamais par l'utilisateur.
    sets = ", ".join(f"{c} = ?" for c in data)
    db.execute(f"UPDATE client_projects SET {sets} WHERE id = ?", [*data.values(), key(project_id)])


def update_status(project_id, new_status, changed_by, note=None):
    project = db.fetch("SELECT * FROM client_projects WHERE id = ?", [key(project_id)])
    if not project:
        return False
    data = {"status": new_status}
    stamp = {"generating": "started_at", "delivered": "delivered_at", "completed": "completed_at"}.get(new_status)
    if stamp:
        data[stamp] = php.date("Y-m-d H:i:s")
    update(project_id, data)
    _add_status_history(project_id, project["status"], new_status, changed_by, note)
    return True
