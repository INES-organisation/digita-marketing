"""Formations (équivalent de app/Models/Formation.php, partie publique)."""
from .. import db, php
from . import key, like_ci, rand_order, sort_by_name


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


# ---------------------------------------------------------------- espace élève
def get_by_id(formation_id):
    return db.fetch(_select(icon=False) + " WHERE f.id = ?", [key(formation_id)])


def enroll(user_id, formation_id):
    try:
        db.execute("INSERT INTO formation_enrollments (user_id, formation_id) VALUES (?, ?)", [user_id, formation_id])
        db.execute("UPDATE formations SET enrolled_count = enrolled_count + 1 WHERE id = ?", [formation_id])
        return True
    except Exception:  # noqa: BLE001 — catch (Exception) PHP
        return False


def get_progress(user_id, formation_id):
    formation_id = key(formation_id)
    enrollment = db.fetch("SELECT * FROM formation_enrollments WHERE user_id = ? AND formation_id = ?",
                          [user_id, formation_id])
    if not enrollment:
        return None
    total = db.fetch("SELECT COUNT(*) as total FROM formation_lessons fl JOIN formation_modules fm "
                     "ON fl.module_id = fm.id WHERE fm.formation_id = ?", [formation_id])["total"]
    done = db.fetch("SELECT COUNT(*) as total FROM lesson_completions WHERE user_id = ? AND formation_id = ?",
                    [user_id, formation_id])["total"]
    enrollment["total_lessons"] = int(total)
    enrollment["completed_lessons"] = int(done)
    enrollment["percentage"] = php.php_round(done / total * 100) if total > 0 else 0
    return enrollment


def get_completed_lessons(user_id, formation_id):
    return [r["lesson_id"] for r in db.fetch_all(
        "SELECT lesson_id FROM lesson_completions WHERE user_id = ? AND formation_id = ? ORDER BY id",
        [user_id, key(formation_id)])]


def complete_lesson(user_id, lesson_id, formation_id):
    try:
        db.execute("INSERT INTO lesson_completions (user_id, lesson_id, formation_id) VALUES (?, ?, ?) "
                   "ON CONFLICT DO NOTHING", [user_id, lesson_id, formation_id])  # INSERT IGNORE
        progress = get_progress(user_id, formation_id)
        if progress:
            db.execute("UPDATE formation_enrollments SET progress = ? WHERE user_id = ? AND formation_id = ?",
                       [progress["percentage"], user_id, formation_id])
        return True
    except Exception:  # noqa: BLE001
        return False


def get_user_formations(user_id):
    formations = db.fetch_all(
        """SELECT f.*, fe.progress, fe.completed, fe.enrolled_at, fe.completed_at,
                  c.name as category_name, c.slug as category_slug
           FROM formations f
           JOIN formation_enrollments fe ON f.id = fe.formation_id
           LEFT JOIN service_categories c ON f.category_id = c.id
           WHERE fe.user_id = ?
           ORDER BY fe.enrolled_at DESC NULLS LAST, fe.id DESC""", [user_id])
    for f in formations:
        progress = get_progress(user_id, f["id"])
        if progress:
            f["percentage"] = progress["percentage"]
            f["total_lessons"] = progress["total_lessons"]
            f["completed_lessons"] = progress["completed_lessons"]
    return formations


def add_review(user_id, formation_id, data):
    try:
        db.execute(
            """INSERT INTO formation_reviews (user_id, formation_id, rating, title, comment)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (user_id, formation_id) DO UPDATE SET rating = EXCLUDED.rating,
               title = EXCLUDED.title, comment = EXCLUDED.comment, status = 'pending'""",
            [user_id, formation_id, data["rating"], data.get("title"), data.get("comment")])
        _update_average_rating(formation_id)
        return True
    except Exception:  # noqa: BLE001
        return False


def _update_average_rating(formation_id):
    avg = db.fetch("SELECT AVG(rating) as avg_rating FROM formation_reviews "
                   "WHERE formation_id = ? AND status = 'approved'", [formation_id])["avg_rating"]
    db.execute("UPDATE formations SET rating = ? WHERE id = ?",
               [php.php_round(avg, 2) if avg is not None else 0, formation_id])


# ---------------------------------------------------------------- administration
def get_all(limit=None, offset=0, status=None, category_id=None, search=None):
    from .article import _admin_filters
    where, params = _admin_filters(status, category_id, search, "f", "description")
    sql = _select(icon=False) + " WHERE 1=1" + where + " ORDER BY f.created_at DESC NULLS LAST, f.id DESC"
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return db.fetch_all(sql, params)


def count_all(status=None, category_id=None, search=None):
    from .article import _admin_filters
    where, params = _admin_filters(status, category_id, search, "f", "description")
    return db.fetch("SELECT COUNT(*) as total FROM formations f WHERE 1=1" + where, params)["total"]


def get_full_formation_by_id(formation_id):
    formation = get_by_id(formation_id)
    if not formation:
        return None
    modules = get_modules(formation["id"])
    for m in modules:
        m["lessons"] = get_lessons(m["id"])
    formation["modules"] = modules
    return formation


def _admin_values(data):
    return [data["title"], data["slug"], data.get("description", ""),
            key(data["category_id"]) if php.t(data["category_id"]) else None, data.get("service_name", ""),
            data.get("level", "debutant"), data.get("duration", ""), data.get("price", 0), data.get("image", ""),
            data.get("meta_title", data["title"]), data.get("meta_description", ""), data.get("meta_keywords", ""),
            data.get("status", "draft")]


def create(data):
    row = db.fetch(
        """INSERT INTO formations (title, slug, description, category_id, service_name, level, duration, price, image,
                                   meta_title, meta_description, meta_keywords, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW()) RETURNING id""", _admin_values(data))
    return str(row["id"])


def update(formation_id, data):
    db.execute(
        """UPDATE formations SET title = ?, slug = ?, description = ?, category_id = ?, service_name = ?,
                  level = ?, duration = ?, price = ?, image = ?, meta_title = ?, meta_description = ?,
                  meta_keywords = ?, status = ?, updated_at = NOW() WHERE id = ?""",
        _admin_values(data) + [key(formation_id)])
    return True


def delete(formation_id):
    fid = key(formation_id)
    for m in get_modules(fid):
        db.execute("DELETE FROM formation_lessons WHERE module_id = ?", [m["id"]])
    db.execute("DELETE FROM formation_modules WHERE formation_id = ?", [fid])
    db.execute("DELETE FROM formation_enrollments WHERE formation_id = ?", [fid])
    db.execute("DELETE FROM formations WHERE id = ?", [fid])
    return True


def get_all_categories():
    rows = db.fetch_all("""SELECT c.*, COUNT(f.id) as formation_count FROM service_categories c
                           LEFT JOIN formations f ON c.id = f.category_id GROUP BY c.id ORDER BY c.id""")
    return sort_by_name(rows)


def generate_slug(title, exclude_id=None):
    from .article import generate_slug as slug
    return slug(title, exclude_id, "formations")


def get_formation_stats():
    one = lambda sql: db.fetch(sql)["total"]  # noqa: E731
    return {
        "total": one("SELECT COUNT(*) as total FROM formations"),
        "published": one("SELECT COUNT(*) as total FROM formations WHERE status = 'published'"),
        "draft": one("SELECT COUNT(*) as total FROM formations WHERE status = 'draft'"),
        "total_enrolled": one("SELECT COALESCE(SUM(enrolled_count), 0) as total FROM formations"),
        "total_modules": one("SELECT COUNT(*) as total FROM formation_modules"),
        "total_lessons": one("SELECT COUNT(*) as total FROM formation_lessons"),
    }
