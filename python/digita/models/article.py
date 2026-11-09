"""Articles du blog (équivalent de app/Models/Article.php)."""
import math
import re

from .. import db, php, redirects
from . import key, like_ci, rand_order, sort_by_name

SELECT = """SELECT a.*, c.name as category_name, c.slug as category_slug{icon}
            FROM blog_articles a
            LEFT JOIN service_categories c ON a.category_id = c.id"""


def _select(icon=True):
    return SELECT.format(icon=", c.icon as category_icon" if icon else "")


def get_all_published(limit=None, offset=0, content_type=None):
    sql, params = _select() + " WHERE a.status = 'published'", []
    if content_type:
        sql += " AND a.content_type = ?"
        params.append(content_type)
    # Les articles classés (nouveaux) passent avant les articles d'origine, non classés.
    sql += " ORDER BY (a.content_type IS NULL), a.published_at DESC NULLS LAST, a.id DESC"
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return db.fetch_all(sql, params)


def get_by_slug(slug):
    article = db.fetch(_select() + " WHERE a.slug = ? AND a.status = 'published'", [slug])
    if article:
        increment_views(article["id"])
    return article


def is_retired(slug):
    """Article retiré du blog (statut « archived ») : la page répond 410 au lieu de 404."""
    return bool(db.fetch("SELECT 1 FROM blog_articles WHERE slug = ? AND status = 'archived'", [slug]))


def get_by_category(category_slug, limit=None, offset=0):
    sql = (_select() + " WHERE c.slug = ? AND a.status = 'published'"
           " ORDER BY (a.content_type IS NULL), a.published_at DESC NULLS LAST, a.id DESC")
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return db.fetch_all(sql, [category_slug])


def search(query, limit=20):
    q = f"%{query}%"
    return db.fetch_all(
        _select(icon=False)
        + f" WHERE ({like_ci('a.title')} OR {like_ci('a.content')} OR {like_ci('a.service_name')})"
          " AND a.status = 'published' ORDER BY a.published_at DESC NULLS LAST, a.id DESC LIMIT ?",
        [q, q, q, limit],
    )


def get_popular(limit=5):
    return db.fetch_all(_select(icon=False) + " WHERE a.status = 'published' ORDER BY a.views DESC NULLS LAST, a.id DESC LIMIT ?", [limit])


def get_recent(limit=5):
    return db.fetch_all(_select(icon=False) + " WHERE a.status = 'published' ORDER BY a.published_at DESC NULLS LAST, a.id DESC LIMIT ?", [limit])


def get_related(article_id, category_id, limit=3):
    return db.fetch_all(
        _select(icon=False) + f" WHERE a.id != ? AND a.category_id = ? AND a.status = 'published' ORDER BY (a.content_type IS NULL), {rand_order('a')} LIMIT ?",
        [article_id, category_id, limit],
    )


def increment_views(article_id):
    # Sans toucher updated_at : il donne le <lastmod> du sitemap, et chaque visite (robots compris)
    # le remettait à la date du jour sur les 472 articles (05/11/2026), date que Google cesse de croire.
    db.execute("UPDATE blog_articles SET views = views + 1 WHERE id = ?", [article_id])


def count(category_slug=None, content_type=None):
    if content_type:
        return db.fetch("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'published' AND content_type = ?",
                        [content_type])["total"]
    if category_slug:
        return db.fetch(
            """SELECT COUNT(*) as total FROM blog_articles a
               LEFT JOIN service_categories c ON a.category_id = c.id
               WHERE c.slug = ? AND a.status = 'published'""", [category_slug])["total"]
    return db.fetch("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'published'")["total"]


def type_counts():
    """{type: nombre d'articles publiés} pour les filtres de /blog."""
    rows = db.fetch_all("SELECT content_type, COUNT(*) as total FROM blog_articles "
                        "WHERE status = 'published' AND content_type IS NOT NULL GROUP BY content_type")
    return {r["content_type"]: r["total"] for r in rows}


def get_categories():
    rows = db.fetch_all(
        """SELECT c.*, COUNT(a.id) as article_count
           FROM service_categories c
           LEFT JOIN blog_articles a ON c.id = a.category_id AND a.status = 'published'
           GROUP BY c.id
           HAVING COUNT(a.id) > 0
           ORDER BY c.id""")
    return sort_by_name(rows)


# ------------------------------------------------------------- SEO couche 3
def estimate_reading_time(content):
    words = php.str_word_count(php.strip_tags(content))
    return max(1, math.ceil(words / 200))


def _slugify(text):
    text = php.strtolower(text.strip())
    for pat, rep in (("[àáâãäå]", "a"), ("[èéêë]", "e"), ("[ìíîï]", "i"), ("[òóôõö]", "o"), ("[ùúûü]", "u"), ("[ç]", "c")):
        text = re.sub(pat, rep, text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def generate_table_of_contents(content):
    matches = list(re.finditer(r"<(h[23])[^>]*>(.*?)</\1>", content, re.S | re.I))
    if len(matches) < 2:
        return {"toc": [], "content": content}
    items = []
    for m in matches:
        tag = m.group(1).lower()
        text = php.strip_tags(m.group(2))
        items.append({"tag": tag, "text": text, "slug": _slugify(text), "level": 2 if tag == "h2" else 3,
                      "start": m.start(), "end": m.end()})
    toc = [{"text": i["text"], "slug": i["slug"], "level": i["level"]} for i in items]
    out = content
    for i in reversed(items):
        rep = f'<{i["tag"]} id="{php.h(i["slug"])}">{i["text"]}</{i["tag"]}>'
        out = out[: i["start"]] + rep + out[i["end"]:]
    return {"toc": toc, "content": out}


# Questions en <h3> seulement : les <h2> en forme de question sont des sections, pas une FAQ.
FAQ_RX = re.compile(r"<h3[^>]*>([^<]*\?[^<]*)</h3>\s*<p>([^<]+(?:<[^/][^>]*>[^<]*</[^>]+>)*[^<]*)</p>", re.S | re.I)


def extract_faq(content):
    faq = []
    for m in FAQ_RX.finditer(content):
        q = php.strip_tags(m.group(1)).strip()
        a = php.strip_tags(m.group(2)).strip()
        if len(q) > 10 and len(a) > 20:
            faq.append({"question": q, "answer": php.mb_strimwidth(a, 0, 500, "...")})
    return faq


# ---------------------------------------------------------------- administration
def _admin_filters(status, category_id, search, alias="a", text_col="content"):
    sql, params = "", []
    if php.t(status):
        sql += f" AND {alias}.status = ?"
        params.append(status)
    if php.t(category_id):
        sql += f" AND {alias}.category_id = ?"
        params.append(key(category_id))
    if php.t(search):
        sql += f" AND ({like_ci(alias + '.title')} OR {like_ci(alias + '.' + text_col)})"
        params += [f"%{search}%", f"%{search}%"]
    return sql, params


def get_all(limit=None, offset=0, status=None, category_id=None, search=None):
    where, params = _admin_filters(status, category_id, search)
    sql = (_select(icon=False) + " WHERE 1=1" + where
           + " ORDER BY a.created_at DESC NULLS LAST, a.id DESC")
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return db.fetch_all(sql, params)


def count_all(status=None, category_id=None, search=None):
    where, params = _admin_filters(status, category_id, search)
    return db.fetch("SELECT COUNT(*) as total FROM blog_articles a WHERE 1=1" + where, params)["total"]


def get_by_id(article_id):
    return db.fetch(_select(icon=False) + " WHERE a.id = ?", [key(article_id)])


def create(data):
    row = db.fetch(
        """INSERT INTO blog_articles (title, slug, content, excerpt, category_id, service_name, meta_title,
                                      meta_description, meta_keywords, featured_image, status, published_at, content_type, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW()) RETURNING id""",
        [data["title"], data["slug"], data["content"], data.get("excerpt", ""),
         key(data["category_id"]) if php.t(data["category_id"]) else None, data.get("service_name", ""),
         data.get("meta_title", data["title"]), data.get("meta_description", ""), data.get("meta_keywords", ""),
         data.get("featured_image", ""), data.get("status", "draft"),
         php.date("Y-m-d H:i:s") if data["status"] == "published" else None, data.get("content_type") or None])
    return str(row["id"])


def update(article_id, data):
    article = get_by_id(article_id)
    published_at = article["published_at"]
    if data["status"] == "published" and not php.t(published_at):
        published_at = php.date("Y-m-d H:i:s")
    db.execute(
        """UPDATE blog_articles SET title = ?, slug = ?, content = ?, excerpt = ?, category_id = ?, service_name = ?,
                  meta_title = ?, meta_description = ?, meta_keywords = ?, featured_image = ?,
                  status = ?, published_at = ?, content_type = ?, updated_at = NOW() WHERE id = ?""",
        [data["title"], data["slug"], data["content"], data.get("excerpt", ""),
         key(data["category_id"]) if php.t(data["category_id"]) else None, data.get("service_name", ""),
         data.get("meta_title", data["title"]), data.get("meta_description", ""), data.get("meta_keywords", ""),
         php.coalesce(data.get("featured_image"), article.get("featured_image"), ""),
         data.get("status", "draft"), published_at, data.get("content_type") or None, key(article_id)])
    return True


def delete(article_id):
    db.execute("DELETE FROM blog_articles WHERE id = ?", [key(article_id)])
    return True


def get_all_categories():
    rows = db.fetch_all("""SELECT c.*, COUNT(a.id) as article_count FROM service_categories c
                           LEFT JOIN blog_articles a ON c.id = a.category_id GROUP BY c.id ORDER BY c.id""")
    return sort_by_name(rows)


def generate_slug(title, exclude_id=None, table="blog_articles"):
    slug = redirects.slugify(title)
    base, counter = slug, 1
    while True:
        sql, params = f"SELECT id FROM {table} WHERE slug = ?", [slug]
        if php.t(exclude_id):
            sql += " AND id != ?"
            params.append(key(exclude_id))
        if not db.fetch(sql, params):
            return slug
        slug = f"{base}-{counter}"
        counter += 1


def get_stats():
    one = lambda sql: db.fetch(sql)["total"]  # noqa: E731
    return {
        "total": one("SELECT COUNT(*) as total FROM blog_articles"),
        "published": one("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'published'"),
        "draft": one("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'draft'"),
        "total_views": one("SELECT COALESCE(SUM(views), 0) as total FROM blog_articles"),
    }
