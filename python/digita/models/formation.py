"""Formations (équivalent de app/Models/Formation.php, partie publique)."""
from .. import db
from . import like_ci, rand_order, sort_by_name


def _select(icon=True):
    return ("SELECT f.*, c.name as category_name, c.slug as category_slug"
            + (", c.icon as category_icon" if icon else "")
            + " FROM formations f LEFT JOIN service_categories c ON f.category_id = c.id")


ORDER = " ORDER BY f.created_at DESC NULLS LAST, f.id DESC"


def get_all_published(limit=None, offset=0):
    sql = _select() + " WHERE f.status = 'published'" + ORDER
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return db.fetch_all(sql)


def get_by_slug(slug):
    return db.fetch(_select() + " WHERE f.slug = ? AND f.status = 'published'", [slug])


def get_modules(formation_id):
    return db.fetch_all("SELECT * FROM formation_modules WHERE formation_id = ? ORDER BY order_num NULLS FIRST, id", [formation_id])


def get_lessons(module_id):
    return db.fetch_all("SELECT * FROM formation_lessons WHERE module_id = ? ORDER BY order_num NULLS FIRST, id", [module_id])


def get_full_formation(slug):
    formation = get_by_slug(slug)
    if not formation:
        return None
    modules = get_modules(formation["id"])
    for m in modules:
        m["lessons"] = get_lessons(m["id"])
    formation["modules"] = modules
    return formation


def get_by_category(category_slug, limit=None):
    sql = _select() + " WHERE c.slug = ? AND f.status = 'published'" + ORDER
    if limit:
        sql += f" LIMIT {int(limit)}"
    return db.fetch_all(sql, [category_slug])


def search(query, limit=20):
    q = f"%{query}%"
    return db.fetch_all(
        _select(icon=False)
        + f" WHERE ({like_ci('f.title')} OR {like_ci('f.description')} OR {like_ci('f.service_name')})"
          " AND f.status = 'published'" + ORDER + " LIMIT ?",
        [q, q, q, limit],
    )


def get_popular(limit=6):
    return db.fetch_all(
        _select(icon=False) + " WHERE f.status = 'published'"
        " ORDER BY f.enrolled_count DESC NULLS LAST, f.rating DESC NULLS LAST, f.id DESC LIMIT ?", [limit])


def get_recent(limit=6):
    return db.fetch_all(_select(icon=False) + " WHERE f.status = 'published'" + ORDER + " LIMIT ?", [limit])


def get_related(formation_id, category_id, limit=3):
    return db.fetch_all(
        _select(icon=False) + f" WHERE f.id != ? AND f.category_id = ? AND f.status = 'published' ORDER BY {rand_order('f')} LIMIT ?",
        [formation_id, category_id, limit])


def is_enrolled(user_id, formation_id):
    return bool(db.fetch("SELECT id FROM formation_enrollments WHERE user_id = ? AND formation_id = ?", [user_id, formation_id]))


def get_reviews(formation_id, limit=10):
    return db.fetch_all(
        """SELECT fr.*, u.username FROM formation_reviews fr JOIN users u ON fr.user_id = u.id
           WHERE fr.formation_id = ? AND fr.status = 'approved'
           ORDER BY fr.created_at DESC NULLS LAST, fr.id DESC LIMIT ?""", [formation_id, limit])


def get_user_review(user_id, formation_id):
    return db.fetch("SELECT * FROM formation_reviews WHERE user_id = ? AND formation_id = ?", [user_id, formation_id])


def get_average_rating(formation_id):
    return db.fetch(
        """SELECT COALESCE(AVG(rating), 0) as average, COUNT(*) as count
           FROM formation_reviews WHERE formation_id = ? AND status = 'approved'""", [formation_id])


def count(category_slug=None):
    if category_slug:
        return db.fetch(
            """SELECT COUNT(*) as total FROM formations f LEFT JOIN service_categories c ON f.category_id = c.id
               WHERE c.slug = ? AND f.status = 'published'""", [category_slug])["total"]
    return db.fetch("SELECT COUNT(*) as total FROM formations WHERE status = 'published'")["total"]


def get_categories():
    rows = db.fetch_all(
        """SELECT c.*, COUNT(f.id) as formation_count FROM service_categories c
           LEFT JOIN formations f ON c.id = f.category_id AND f.status = 'published'
           GROUP BY c.id HAVING COUNT(f.id) > 0 ORDER BY c.id""")
    return sort_by_name(rows)
