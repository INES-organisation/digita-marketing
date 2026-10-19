"""Mot de passe oublié : demande du lien par e-mail puis choix du nouveau mot de passe."""
import re

import pytest
from starlette.testclient import TestClient

from digita import sessions
from digita.main import app
from digita.routes import auth
from digita.services import email


@pytest.fixture(autouse=True)
def memory_sessions(monkeypatch):
    store = {}
    monkeypatch.setattr(sessions, "_load", lambda sid: store.get(sid))
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: store.__setitem__(sid, data))


@pytest.fixture
def fake_store(monkeypatch):
    """Comptes et jetons en mémoire, e-mails capturés."""
    users = {"admin@example.com": {"id": 1, "email": "admin@example.com", "password": "old"}}
    resets, sent = {}, []

    def create(user_id):
        token = f"tok{len(resets)}"
        resets[token] = {"token_hash": token, "user_id": user_id}
        return token

    def apply(record, password):
        users["admin@example.com"]["password"] = password
        resets.pop(record["token_hash"])

    monkeypatch.setattr(auth, "_find_user", lambda mail: users.get(mail.lower()))
    monkeypatch.setattr(auth, "_create_reset", create)
    monkeypatch.setattr(auth, "_find_reset", lambda token: resets.get(token))
    monkeypatch.setattr(auth, "_apply_reset", apply)
    monkeypatch.setattr(email, "send", lambda *a: sent.append(a) or True)
    return users, resets, sent


def _token(html):
    return re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)


def test_login_page_links_to_forgot_password():
    c = TestClient(app, base_url="https://digita.buzz")
    assert 'href="/mot-de-passe-oublie"' in c.get("/connexion").text


def test_forgot_password_sends_link_only_for_existing_accounts(fake_store):
    users, resets, sent = fake_store
    c = TestClient(app, base_url="https://digita.buzz")
    csrf = _token(c.get("/mot-de-passe-oublie").text)

    r = c.post("/mot-de-passe-oublie", data={"_csrf_token": csrf, "email": "inconnu@example.com"})
    assert sent == [] and "Si un compte existe" in r.text

    c.post("/mot-de-passe-oublie", data={"_csrf_token": csrf, "email": "Admin@Example.com"})
    assert len(sent) == 1 and sent[0][0] == "admin@example.com"
    assert "https://digita.buzz/reinitialiser-mot-de-passe?token=tok0" in sent[0][2]


def test_reset_password_with_valid_token_then_link_is_used(fake_store):
    users, resets, sent = fake_store
    resets["tok9"] = {"token_hash": "tok9", "user_id": 1}
    c = TestClient(app, base_url="https://digita.buzz")

    assert "n'est plus valable" in c.get("/reinitialiser-mot-de-passe?token=faux").text
    page = c.get("/reinitialiser-mot-de-passe?token=tok9").text
    assert 'name="token" value="tok9"' in page
    csrf = _token(page)

    r = c.post("/reinitialiser-mot-de-passe", data={"_csrf_token": csrf, "token": "tok9",
                                                     "password": "court", "password2": "court"})
    assert users["admin@example.com"]["password"] == "old" and "au moins 8 caractères" in r.text

    r = c.post("/reinitialiser-mot-de-passe", data={"_csrf_token": csrf, "token": "tok9",
                                                     "password": "Nouveau-2026!", "password2": "Nouveau-2026!"},
               follow_redirects=False)
    assert r.headers["location"] == "/connexion"
    assert users["admin@example.com"]["password"] == "Nouveau-2026!" and "tok9" not in resets
    assert "Mot de passe modifié" in c.get("/connexion").text
