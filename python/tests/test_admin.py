from digita import config, php, redirects
from digita.models import article
from digita.routes import admin


def test_slug_keeps_accented_letters():
    # Le PHP supprimait ou décomposait les accents (« stratgie », « a-tae-… ») : 236 adresses cassées.
    assert redirects.slugify(" Été à La Réunion : ça déçoit ? ") == "ete-a-la-reunion-ca-decoit"
    assert redirects.slugify("SEO & Ads 2024") == "seo-ads-2024"
    assert redirects.slugify("Twitter/X Ads") == "twitter-x-ads"


def test_fputcsv_quotes_like_php():
    assert admin.fputcsv(["Email", "Date"]) == "Email,Date\n"
    assert admin.fputcsv(["b,c@example.com", "2024-03-01 09:00:00"]) == '"b,c@example.com","2024-03-01 09:00:00"\n'
    assert admin.fputcsv(['a"b', None]) == '"a""b",\n'


def test_image_upload_checks_type_and_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PUBLIC_DIR", tmp_path)
    path = admin._store_image(("photo.JPG", "image/jpeg", b"\xff\xd8"), "articles", "article_")
    assert path.startswith("/uploads/articles/article_") and path.endswith(".JPG")
    assert (tmp_path / path.lstrip("/")).read_bytes() == b"\xff\xd8"
    # Le PHP acceptait x.php envoyé avec le type image/png.
    assert admin._store_image(("x.php", "image/png", b"<?php"), "articles", "article_") is None
    assert admin._store_image(("x.png", "text/html", b"<b>"), "articles", "article_") is None
    assert admin._store_image(("big.png", "image/png", b"0" * (5 * 1024 * 1024 + 1)), "articles", "a_") is None


def test_strict_and_loose_comparisons():
    assert php.same(0, False) is False and php.same(False, False)
    assert php.loose_eq("3", 3) and not php.loose_eq("abc", 0)
    assert php.to_array(None) == [] and php.to_array("x") == ["x"] and php.to_array(["a"]) == ["a"]


def test_old_article_and_formation_addresses_redirect_permanently(monkeypatch):
    from starlette.testclient import TestClient
    from digita.main import app
    from digita import sessions
    from digita.models import formation
    monkeypatch.setattr(sessions, "_load", lambda sid: None)
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: None)
    monkeypatch.setattr(article, "get_by_slug", lambda slug: None)
    monkeypatch.setattr(formation, "get_full_formation", lambda slug: None)
    table = {("article", "stratgie-nft"): "strategie-nft", ("formation", "formation-effets-spciaux"): "formation-effets-speciaux"}
    monkeypatch.setattr(redirects.db, "fetch", lambda sql, p: {"new_slug": table[tuple(p)]} if tuple(p) in table else None)
    c = TestClient(app, base_url="https://digita.buzz")
    r = c.get("/blog/stratgie-nft", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/blog/strategie-nft"
    r = c.get("/formations/formation-effets-spciaux", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/formations/formation-effets-speciaux"
    assert c.get("/blog/inconnu", follow_redirects=False).status_code == 404


def test_redirect_chains_are_shortened(monkeypatch):
    calls = []
    monkeypatch.setattr(redirects.db, "execute", lambda sql, p: calls.append((sql.split()[0], p)))
    redirects.record("article", "a", "a")
    assert calls == []
    redirects.record("article", "b", "c")
    assert [c[0] for c in calls] == ["DELETE", "UPDATE", "INSERT"]
    assert calls[1][1] == ["c", "article", "b"]  # x → b devient x → c


def test_admin_shop_page_lists_products_and_prompt_files(monkeypatch):
    from starlette.testclient import TestClient
    from digita import boutique, sessions
    from digita.main import app
    from digita.models import shop

    store = {"b" * 64: {"user_id": 1, "user_role": "admin"}, "c" * 64: {"user_id": 2, "user_role": "client"}}
    monkeypatch.setattr(sessions, "_load", lambda k: store.get(k))
    monkeypatch.setattr(sessions, "_save", lambda k, data, touch: store.__setitem__(k, data))
    monkeypatch.setattr(admin.Admin, "find_user", lambda uid: {"id": uid, "username": "anthony"})
    monkeypatch.setattr(shop, "sales_by_product", lambda: {"devis-ia": {"count": 2, "revenue": 1780.0}})
    monkeypatch.setattr(shop, "recent_orders", lambda: [])
    c = TestClient(app, base_url="https://digita.buzz")
    c.cookies.set(sessions.COOKIE, "c" * 64)
    assert c.get("/admin/boutique", follow_redirects=False).status_code == 302  # client : refusé
    c.cookies.set(sessions.COOKIE, "b" * 64)
    html = c.get("/admin/boutique").text
    for p in boutique.products().values():
        assert p["title"] in html
    assert "1 780,00 €" in html and "manquant" not in html
    page = c.get("/admin/boutique/fichier/pack-immobilier.md").text
    assert "Master prompt de contexte" in page
    dl = c.get("/admin/boutique/fichier/pack-immobilier.md?download=1")
    assert dl.status_code == 200 and "attachment" in dl.headers["content-disposition"]
    assert c.get("/admin/boutique/fichier/..%2F..%2Fconfig.py", follow_redirects=False).status_code == 302
