"""Articles du blog (équivalent de app/Models/Article.php)."""
import math
import re

from .. import db, php
from . import key, like_ci, rand_order, sort_by_name

SELECT = """SELECT a.*, c.name as category_name, c.slug as category_slug{icon}
            FROM blog_articles a
            LEFT JOIN service_categories c ON a.category_id = c.id"""


def _select(icon=True):
    return SELECT.format(icon=", c.icon as category_icon" if icon else "")


def get_all_published(limit=None, offset=0):
    sql = _select() + " WHERE a.status = 'published' ORDER BY a.published_at DESC NULLS LAST, a.id DESC"
    if limit:
        sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"
    return db.fetch_all(sql)


def get_by_slug(slug):
    article = db.fetch(_select() + " WHERE a.slug = ? AND a.status = 'published'", [slug])
    if article:
        increment_views(article["id"])
    return article


def get_by_category(category_slug, limit=None):
    sql = _select() + " WHERE c.slug = ? AND a.status = 'published' ORDER BY a.published_at DESC NULLS LAST, a.id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
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
        _select(icon=False) + f" WHERE a.id != ? AND a.category_id = ? AND a.status = 'published' ORDER BY {rand_order('a')} LIMIT ?",
        [article_id, category_id, limit],
    )


def increment_views(article_id):
    # MySQL mettait updated_at à jour automatiquement (ON UPDATE CURRENT_TIMESTAMP).
    db.execute("UPDATE blog_articles SET views = views + 1, updated_at = NOW() WHERE id = ?", [article_id])


def count(category_slug=None):
    if category_slug:
        return db.fetch(
            """SELECT COUNT(*) as total FROM blog_articles a
               LEFT JOIN service_categories c ON a.category_id = c.id
               WHERE c.slug = ? AND a.status = 'published'""", [category_slug])["total"]
    return db.fetch("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'published'")["total"]


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


FAQ_RX = re.compile(r"<h[23][^>]*>([^<]*\?[^<]*)</h[23]>\s*<p>([^<]+(?:<[^/][^>]*>[^<]*</[^>]+>)*[^<]*)</p>", re.S | re.I)


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
                                      meta_description, meta_keywords, featured_image, status, published_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW()) RETURNING id""",
        [data["title"], data["slug"], data["content"], data.get("excerpt", ""),
         key(data["category_id"]) if php.t(data["category_id"]) else None, data.get("service_name", ""),
         data.get("meta_title", data["title"]), data.get("meta_description", ""), data.get("meta_keywords", ""),
         data.get("featured_image", ""), data.get("status", "draft"),
         php.date("Y-m-d H:i:s") if data["status"] == "published" else None])
    return str(row["id"])


def update(article_id, data):
    article = get_by_id(article_id)
    published_at = article["published_at"]
    if data["status"] == "published" and not php.t(published_at):
        published_at = php.date("Y-m-d H:i:s")
    db.execute(
        """UPDATE blog_articles SET title = ?, slug = ?, content = ?, excerpt = ?, category_id = ?, service_name = ?,
                  meta_title = ?, meta_description = ?, meta_keywords = ?, featured_image = ?,
                  status = ?, published_at = ?, updated_at = NOW() WHERE id = ?""",
        [data["title"], data["slug"], data["content"], data.get("excerpt", ""),
         key(data["category_id"]) if php.t(data["category_id"]) else None, data.get("service_name", ""),
         data.get("meta_title", data["title"]), data.get("meta_description", ""), data.get("meta_keywords", ""),
         php.coalesce(data.get("featured_image"), article.get("featured_image"), ""),
         data.get("status", "draft"), published_at, key(article_id)])
    return True


def delete(article_id):
    db.execute("DELETE FROM blog_articles WHERE id = ?", [key(article_id)])
    return True


def get_all_categories():
    rows = db.fetch_all("""SELECT c.*, COUNT(a.id) as article_count FROM service_categories c
                           LEFT JOIN blog_articles a ON c.id = a.category_id GROUP BY c.id ORDER BY c.id""")
    return sort_by_name(rows)


def generate_slug(title, exclude_id=None, table="blog_articles"):
    slug = php_slug(title)
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


_SLUG_CLASSES = [("àáâãäå", b"a"), ("èéêë", b"e"), ("ìíîï", b"i"), ("òóôõö", b"o"), ("ùúûü", b"u"), ("ç", b"c")]


def php_slug(title):
    """generateSlug() PHP : ses classes [àáâ…] sans /u portent sur les octets UTF-8, pas les lettres."""
    s = php.trim(title).encode("utf-8")
    s = bytes(c + 32 if 65 <= c <= 90 else c for c in s)  # strtolower : ASCII seulement
    for chars, rep in _SLUG_CLASSES:
        byteset = set(chars.encode("utf-8"))
        s = b"".join(rep if c in byteset else bytes([c]) for c in s)
    s = re.sub(rb"[^a-z0-9-]", b"-", s)
    s = re.sub(rb"-+", b"-", s)
    return s.strip(b"-").decode("ascii")


def get_stats():
    one = lambda sql: db.fetch(sql)["total"]  # noqa: E731
    return {
        "total": one("SELECT COUNT(*) as total FROM blog_articles"),
        "published": one("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'published'"),
        "draft": one("SELECT COUNT(*) as total FROM blog_articles WHERE status = 'draft'"),
        "total_views": one("SELECT COALESCE(SUM(views), 0) as total FROM blog_articles"),
    }
