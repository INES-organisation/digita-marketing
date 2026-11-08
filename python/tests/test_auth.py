from digita.routes.auth import _hash, _verify

# Généré par PHP : password_hash('motdepasse1', PASSWORD_DEFAULT)
PHP_HASH = "$2y$10$ELIrjTmxGkY5wsYLw5d.nelB165saIJ/7IhCuniRLeD5v4HqRDA5y"


def test_verify_php_hash():
    assert _verify("motdepasse1", PHP_HASH)
    assert not _verify("motdepasse2", PHP_HASH)


def test_hash_keeps_php_prefix():
    h = _hash("motdepasse1")
    assert h.startswith("$2y$10$")
    assert _verify("motdepasse1", h)


def test_verify_invalid_hash():
    assert not _verify("x", "pas-un-hash")


def test_change_password_requires_current_password(monkeypatch):
    from starlette.testclient import TestClient
    from digita import db, sessions
    from digita.main import app
    from digita.routes import auth as auth_routes

    store = {"d" * 64: {"user_id": 7, "user_email": "a@b.fr", "user_role": "user"}}
    monkeypatch.setattr(sessions, "_load", lambda k: store.get(k))
    monkeypatch.setattr(sessions, "_save", lambda k, data, touch: store.__setitem__(k, data))
    user = {"id": 7, "email": "a@b.fr", "password": auth_routes._hash("ancien-mdp"), "ines_sub": None}
    updates = []
    monkeypatch.setattr(db, "fetch", lambda sql, params=None: user if "FROM users" in sql else None)
    monkeypatch.setattr(db, "execute", lambda sql, params=None: updates.append(params))
    c = TestClient(app, base_url="https://digita.buzz")
    assert c.get("/mon-compte/mot-de-passe", follow_redirects=False).headers["location"] == "/connexion"
    c.cookies.set(sessions.COOKIE, "d" * 64)
    page = c.get("/mon-compte/mot-de-passe").text
    assert "Changer mon mot de passe" in page and "a@b.fr" in page
    import re
    token = re.search(r'name="_csrf_token" value="([^"]+)"', page).group(1)
    r = c.post("/mon-compte/mot-de-passe", data={"_csrf_token": token, "current": "faux", "password": "nouveau-mdp", "password2": "nouveau-mdp"})
    assert not updates and "incorrect" in r.text
    r = c.post("/mon-compte/mot-de-passe", data={"_csrf_token": token, "current": "ancien-mdp", "password": "nouveau-mdp", "password2": "nouveau-mdp"})
    assert updates and auth_routes._verify("nouveau-mdp", updates[0][0]) and "a été modifié" in r.text


def test_login_returns_to_the_page_that_asked_for_it(monkeypatch):
    from starlette.testclient import TestClient
    from digita import sessions
    from digita.main import app
    from digita.routes import auth as auth_routes

    store = {"f" * 64: {"redirect_after_login": "/boutique/commander/pack-commerce"}}
    monkeypatch.setattr(sessions, "_load", lambda k: store.get(k))
    monkeypatch.setattr(sessions, "_save", lambda k, data, touch: store.__setitem__(k, data))
    user = {"id": 9, "email": "c@d.fr", "password": auth_routes._hash("motdepasse"), "role": "user"}
    monkeypatch.setattr(auth_routes, "_find_user", lambda mail: user)
    monkeypatch.setattr(auth_routes.db, "execute", lambda *a, **k: None)
    c = TestClient(app, base_url="https://digita.buzz")
    c.cookies.set(sessions.COOKIE, "f" * 64)
    import re
    token = re.search(r'name="_csrf_token" value="([^"]+)"', c.get("/connexion").text).group(1)
    r = c.post("/connexion", data={"_csrf_token": token, "email": "c@d.fr", "password": "motdepasse"}, follow_redirects=False)
    assert r.headers["location"] == "/boutique/commander/pack-commerce"
    # déjà connecté, sans page mémorisée : un client va dans son espace (plus vers l'admin)
    assert c.get("/connexion", follow_redirects=False).headers["location"] == "/espace-client"
