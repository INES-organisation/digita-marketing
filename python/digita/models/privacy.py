"""Droits RGPD (accès, export, effacement) et durées de conservation de la politique de confidentialité.

Les factures et commandes sont conservées 10 ans (obligation comptable, art. L123-22 du Code de commerce) :
l'effacement les détache du compte (user_id à NULL) sans les supprimer.
"""
from sqlalchemy import text

from .. import db

# (table, colonne e-mail) : données rattachées à une adresse, sans compte
BY_EMAIL = [("contact_messages", "email"), ("newsletters", "email"), ("newsletter_subscribers", "email"),
            ("lead_qualifications", "email"), ("appointments", "email"), ("blog_comments", "author_email"),
            ("email_logs", "email_to")]
# Tables rattachées au compte (user_id) que la suppression du compte n'efface pas d'elle-même
BY_USER = ["chatbot_conversations", "client_context", "conversions", "page_views", "tool_usage", "password_resets",
           "shop_downloads", "appointments", "blog_comments", "email_logs"]
# Effacées par la suppression du compte (clés étrangères ON DELETE CASCADE), listées pour l'export
CASCADE = ["formation_enrollments", "formation_reviews", "certificates", "lesson_completions", "quiz_attempts",
           "client_projects", "project_messages", "project_files"]
KEPT = [("orders", "customer_email"), ("invoices", "billing_email")]

RETENTION = [  # (table, colonne de date, durée) : politique de confidentialité, section 6
    ("contact_messages", "created_at", "3 years"), ("appointments", "created_at", "3 years"),
    ("lead_qualifications", "created_at", "3 years"), ("chatbot_conversations", "updated_at", "3 years"),
    ("email_logs", "sent_at", "3 years"), ("page_views", "created_at", "12 months"),
    ("tool_usage", "created_at", "12 months"), ("conversions", "created_at", "12 months"),
]


def _user(email):
    return db.fetch("SELECT id, email, username, role, created_at FROM users WHERE LOWER(email) = LOWER(?)", [email])


def export(email):
    """Toutes les données liées à une adresse e-mail : {table: [lignes]} (sans mots de passe)."""
    data, user = {}, _user(email)
    if user:
        data["users"] = [user]
    for table, col in BY_EMAIL + KEPT:
        rows = db.fetch_all(f"SELECT * FROM {table} WHERE LOWER({col}) = LOWER(?)", [email])
        if rows:
            data[table] = rows
    if user:
        for table in BY_USER + CASCADE:
            col = "client_id" if table == "client_projects" else "user_id"
            rows = db.fetch_all(f"SELECT * FROM {table} WHERE {col} = ?", [user["id"]])
            if rows:
                data.setdefault(table, [])
                data[table] += [r for r in rows if r not in data[table]]
        conv = db.fetch_all("SELECT m.* FROM chatbot_messages m JOIN chatbot_conversations c ON c.id = m.conversation_id "
                            "WHERE c.user_id = ? ORDER BY m.id", [user["id"]])
        if conv:
            data["chatbot_messages"] = conv
    for rows in data.values():
        for r in rows:
            r.pop("password", None)
    return data


def erase(email):
    """Efface tout ce qui concerne l'adresse (en une transaction), sauf commandes et factures, détachées du
    compte et conservées 10 ans. Renvoie {table: lignes supprimées}."""
    user = _user(email)
    done = {}
    with db.engine.begin() as c:
        def run(label, sql, **p):
            n = c.execute(text(sql), p).rowcount
            if n:
                done[label] = done.get(label, 0) + n
        if user:
            uid = user["id"]
            run("chatbot_messages", "DELETE FROM chatbot_messages WHERE conversation_id IN "
                "(SELECT id FROM chatbot_conversations WHERE user_id = :u)", u=uid)
            for table in BY_USER:
                run(table, f"DELETE FROM {table} WHERE user_id = :u", u=uid)
            run("orders (détachées)", "UPDATE orders SET user_id = NULL WHERE user_id = :u", u=uid)
            run("invoices (détachées)", "UPDATE invoices SET user_id = NULL WHERE user_id = :u", u=uid)
            run("users", "DELETE FROM users WHERE id = :u", u=uid)  # + formations, avis, projets (cascade)
        for table, col in BY_EMAIL:
            run(table, f"DELETE FROM {table} WHERE LOWER({col}) = LOWER(:e)", e=email)
    return done


def purge_expired():
    """Supprime ce qui a dépassé la durée de conservation annoncée. Renvoie {table: lignes supprimées}."""
    done = {}
    with db.engine.begin() as c:
        c.execute(text("DELETE FROM chatbot_messages WHERE conversation_id IN (SELECT id FROM chatbot_conversations "
                       "WHERE updated_at < NOW() - INTERVAL '3 years')"))
        for table, col, age in RETENTION:
            n = c.execute(text(f"DELETE FROM {table} WHERE {col} < NOW() - INTERVAL '{age}'")).rowcount
            if n:
                done[table] = n
        c.execute(text("DELETE FROM password_resets WHERE expires_at < NOW()"))
    # Comptes sans connexion depuis 3 ans et sans commande : effacés comme sur demande
    for u in db.fetch_all("SELECT email FROM users u WHERE role <> 'admin' "
                          "AND COALESCE(last_login_at, created_at) < NOW() - INTERVAL '3 years' "
                          "AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)"):
        erase(u["email"])
        done["users (inactifs)"] = done.get("users (inactifs)", 0) + 1
    return done
