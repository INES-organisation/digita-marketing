"""Requêtes de l'administration : Contact.php, Newsletter.php, User.php, statistiques de Project.php
et des tableaux d'AnalyticsController.php."""
from .. import db, php
from . import key

# Semaine commençant le dimanche, comme YEARWEEK() de MySQL (mode 0).
_WEEK = "({c}::date - EXTRACT(DOW FROM {c})::int)"
TODAY = "created_at::date = CURRENT_DATE"
THIS_WEEK = _WEEK.format(c="created_at") + " = " + _WEEK.format(c="CURRENT_DATE")
THIS_MONTH = ("EXTRACT(MONTH FROM created_at) = EXTRACT(MONTH FROM NOW()) "
              "AND EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM NOW())")


def count(table, where=None, params=()):
    sql = f"SELECT COUNT(*) as count FROM {table}" + (f" WHERE {where}" if where else "")
    return db.fetch(sql, list(params))["count"]


def find_user(user_id):
    return db.fetch("SELECT * FROM users WHERE id = ?", [key(user_id)])


def user_stats():
    return {"total": count("users"), "admins": count("users", "role = ?", ["admin"]),
            "users": count("users", "role = ?", ["user"])}


# ---------------------------------------------------------------- contacts
def contact_stats():
    t = "contact_messages"
    return {
        "total": count(t), "new": count(t, "status = ?", ["new"]), "read": count(t, "status = ?", ["read"]),
        "replied": count(t, "status = ?", ["replied"]), "today": count(t, TODAY),
        "this_week": count(t, THIS_WEEK), "this_month": count(t, THIS_MONTH),
    }


def contacts(limit=None):
    sql = "SELECT * FROM contact_messages ORDER BY created_at DESC NULLS LAST, id DESC"
    return db.fetch_all(sql + (f" LIMIT {int(limit)}" if limit else ""))


def new_contacts():
    return db.fetch_all("SELECT * FROM contact_messages WHERE status = ? ORDER BY id", ["new"])


def set_contact_status(contact_id, status):
    db.execute("UPDATE contact_messages SET status = ? WHERE id = ?", [status, key(contact_id)])


# ---------------------------------------------------------------- newsletter
def newsletter_stats():
    t = "newsletters"
    return {
        "total": count(t), "active": count(t, "status = ?", ["active"]),
        "inactive": count(t, "status = ?", ["inactive"]), "today": count(t, TODAY),
        "this_week": count(t, THIS_WEEK), "this_month": count(t, THIS_MONTH),
    }


def newsletters():
    return db.fetch_all("SELECT * FROM newsletters ORDER BY created_at DESC NULLS LAST, id DESC")


def recent_newsletters(limit):
    return db.fetch_all("SELECT * FROM newsletters WHERE status = 'active' "
                        "ORDER BY created_at DESC NULLS LAST, id DESC LIMIT ?", [int(limit)])


def active_newsletters():
    return db.fetch_all("SELECT * FROM newsletters WHERE status = ? ORDER BY id", ["active"])


# ---------------------------------------------------------------- projets
def project_stats():
    t = "client_projects"
    revenue = db.fetch("SELECT COALESCE(SUM(price), 0) as total_revenue FROM client_projects "
                       "WHERE status = 'completed' AND paid = 1")
    monthly = db.fetch("SELECT COALESCE(SUM(price), 0) as monthly FROM client_projects WHERE status = 'completed' "
                       "AND paid = 1 AND EXTRACT(MONTH FROM completed_at) = EXTRACT(MONTH FROM NOW()) "
                       "AND EXTRACT(YEAR FROM completed_at) = EXTRACT(YEAR FROM NOW())")
    avg = db.fetch("SELECT AVG(delivered_at::date - created_at::date) as avg_days FROM client_projects "
                   "WHERE delivered_at IS NOT NULL")
    return {
        "total": count(t), "active": count(t, "status NOT IN ('completed', 'cancelled', 'draft')"),
        "completed": count(t, "status = 'completed'"), "pending": count(t, "status = 'pending'"),
        "total_revenue": php.coalesce(revenue["total_revenue"], 0),
        "monthly_revenue": php.coalesce(monthly["monthly"], 0),
        "avg_delivery_days": php.php_round(php.coalesce(avg["avg_days"], 0), 1),
    }


# ---------------------------------------------------------------- analytics (AnalyticsController::index)
def _avg(expr, scale):
    # MySQL : AVG() d'un entier a 4 décimales, d'un DECIMAL(10,2) en a 6.
    return f"ROUND(AVG({expr})::numeric, {scale})"


def analytics(date_from):
    f = [date_from]
    one = lambda sql, params=None: db.fetch(sql, params)  # noqa: E731
    traffic = {
        "total_views": one("SELECT COUNT(*) as total FROM page_views WHERE created_at >= ?", f)["total"],
        "unique_sessions": one("SELECT COUNT(DISTINCT session_id) as total FROM page_views WHERE created_at >= ?",
                               f)["total"],
        "top_pages": db.fetch_all("SELECT page_url, COUNT(*) as views FROM page_views WHERE created_at >= ? "
                                  "GROUP BY page_url ORDER BY views DESC, page_url LIMIT 10", f),
        "by_device": db.fetch_all("SELECT device_type, COUNT(*) as total FROM page_views WHERE created_at >= ? "
                                  "GROUP BY device_type ORDER BY device_type", f),
        "by_source": db.fetch_all("SELECT COALESCE(utm_source, 'direct') as source, COUNT(*) as total FROM page_views "
                                  "WHERE created_at >= ? GROUP BY 1 ORDER BY total DESC, source LIMIT 10", f),
        "daily": db.fetch_all("SELECT created_at::date as day, COUNT(*) as views FROM page_views "
                              "WHERE created_at >= ? GROUP BY 1 ORDER BY day ASC", f),
    }
    conversions = {
        "total": one("SELECT COUNT(*) as total FROM conversions WHERE created_at >= ?", f)["total"],
        "by_type": db.fetch_all("SELECT event_type, COUNT(*) as total, COALESCE(SUM(value), 0) as total_value "
                                "FROM conversions WHERE created_at >= ? GROUP BY event_type "
                                "ORDER BY total DESC, event_type", f),
        "by_source": db.fetch_all("SELECT COALESCE(source, 'direct') as source, COUNT(*) as total FROM conversions "
                                  "WHERE created_at >= ? GROUP BY 1 ORDER BY total DESC, source LIMIT 10", f),
        "daily": db.fetch_all("SELECT created_at::date as day, COUNT(*) as total FROM conversions "
                              "WHERE created_at >= ? GROUP BY 1 ORDER BY day ASC", f),
    }
    done = "FROM orders WHERE status = 'completed' AND created_at >= ?"
    revenue = {
        "total": one("SELECT COALESCE(SUM(total_amount), 0) as total " + done, f)["total"],
        "orders": one("SELECT COUNT(*) as total " + done, f)["total"],
        "avg_order": php.php_round(one(f"SELECT COALESCE({_avg('total_amount', 6)}, 0) as avg_amount " + done,
                                       f)["avg_amount"], 2),
        "monthly": db.fetch_all("SELECT to_char(created_at, 'YYYY-MM') as month, COALESCE(SUM(total_amount), 0) "
                                "as revenue, COUNT(*) as orders FROM orders WHERE status = 'completed' "
                                "GROUP BY 1 ORDER BY month DESC LIMIT 12"),
        "project_revenue": one("SELECT COALESCE(SUM(price), 0) as total FROM client_projects WHERE status = "
                               "'completed' AND paid = 1 AND completed_at >= ?", f)["total"],
    }
    # Table user_formations : lue telle quelle par le PHP (absente de l'export, la page échoue alors).
    enrol = one("SELECT COUNT(*) as total FROM user_formations")
    rate = one("SELECT COUNT(CASE WHEN progress = 100 THEN 1 END) as completed, COUNT(*) as total "
               "FROM user_formations")
    formations = {
        "total_enrollments": enrol["total"],
        "completion_rate": php.php_round(rate["completed"] / rate["total"] * 100, 1) if rate["total"] > 0 else 0,
        "top_formations": db.fetch_all(
            f"""SELECT f.title, COUNT(uf.id) as enrollments, {_avg('uf.progress', 4)} as avg_progress
                FROM formations f LEFT JOIN user_formations uf ON f.id = uf.formation_id
                GROUP BY f.id, f.title HAVING COUNT(uf.id) > 0 ORDER BY enrollments DESC, f.id LIMIT 10"""),
        "total_certificates": one("SELECT COUNT(*) as total FROM certificates")["total"],
    }
    tools = {
        "total": one("SELECT COUNT(*) as total FROM tool_usage WHERE created_at >= ?", f)["total"],
        "by_tool": db.fetch_all("SELECT tool_name, COUNT(*) as uses FROM tool_usage WHERE created_at >= ? "
                                "GROUP BY tool_name ORDER BY uses DESC, tool_name", f),
    }
    chatbot = {
        "conversations": one("SELECT COUNT(*) as total FROM chatbot_conversations WHERE created_at >= ?", f)["total"],
        "messages": one("SELECT COUNT(*) as total FROM chatbot_messages cm JOIN chatbot_conversations cc "
                        "ON cm.conversation_id = cc.id WHERE cc.created_at >= ?", f)["total"],
        "qualified": one("SELECT COUNT(*) as total FROM chatbot_conversations WHERE is_qualified = 1 "
                         "AND created_at >= ?", f)["total"],
    }
    avg_score = one(f"SELECT {_avg('score', 4)} as avg_score FROM lead_qualifications WHERE created_at >= ?", f)
    leads = {
        "total": one("SELECT COUNT(*) as total FROM lead_qualifications WHERE created_at >= ?", f)["total"],
        "by_status": db.fetch_all("SELECT status, COUNT(*) as total FROM lead_qualifications WHERE created_at >= ? "
                                  "GROUP BY status ORDER BY status", f),
        "avg_score": php.php_round(php.coalesce(avg_score["avg_score"], 0), 1),
        "appointments": one("SELECT COUNT(*) as total FROM appointments WHERE created_at >= ?", f)["total"],
    }
    return {"traffic": traffic, "conversions": conversions, "revenue": revenue, "formations": formations,
            "tools": tools, "chatbot": chatbot, "leads": leads}
