"""Coque commune des pages, formulaires de contact et de newsletter."""
import re

import pytest
from starlette.testclient import TestClient

from digita import db, sessions
from digita.main import app
from digita.routes import leads
from digita.services import email, ines


@pytest.fixture(autouse=True)
def memory_sessions(monkeypatch):
    """Sessions en mémoire : ces tests n'ont pas besoin de PostgreSQL."""
    store = {}
    monkeypatch.setattr(sessions, "_load", lambda sid: store.get(sid))
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: store.__setitem__(sid, data))


def _client():
    return TestClient(app, base_url="https://digita.buzz")


def _token(html):
    return re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)


def test_pages_share_navigation_and_footer():
    c = _client()
    # Accueil : barre latérale verticale ancrée sur les sections, logo vers le héros
    home = c.get("/").text
    assert 'class="sidebar-premium"' in home and 'class="navbar-top"' not in home
    assert 'href="#enjeux"' in home and 'href="#hero-premium"' in home and "Diagnostic gratuit" in home
    assert 'class="sidebar-onglet-sidebar"' not in home and 'class="footer-premium"' in home
    # Autres pages : menu horizontal, menu agence et barre de services à droite
    for path in ("/contact", "/connexion", "/inscription", "/page-qui-n-existe-pas"):
        r = c.get(path)
        assert 'class="navbar-top"' in r.text and 'class="sidebar-premium"' not in r.text, path
        assert 'id="sidebarAgence"' in r.text and 'class="sidebar-onglet-sidebar"' in r.text, path
        assert 'href="/#hero-premium"' in r.text and 'class="footer-premium"' in r.text, path
    r = c.get("/page-qui-n-existe-pas")
    assert r.status_code == 404 and "Page non trouvée" in r.text and "noindex" in r.text
    assert 'aria-current="page"' in c.get("/contact").text


def test_contact_form_is_saved_and_sent_to_ines(monkeypatch):
    saved, leads_sent = [], []
    monkeypatch.setattr(db, "execute", lambda sql, p=None: saved.append(p))
    monkeypatch.setattr(ines, "push_lead", lambda *a: leads_sent.append(a))
    monkeypatch.setattr(email, "send_new_contact_notification", lambda *a: True)
    c = _client()
    token = _token(c.get("/contact").text)

    assert c.post("/contact", data={"nom": "Ana", "email": "ana@example.com"}).status_code == 403  # sans jeton
    r = c.post("/contact", data={"_csrf_token": token, "nom": "Ana", "email": "pas-un-email", "message": "x"},
               follow_redirects=False)
    assert r.status_code == 302 and saved == []
    assert "adresse e-mail valide" in c.get("/contact").text

    r = c.post("/contact", data={"_csrf_token": token, "nom": "Ana", "email": "ana@example.com",
                                 "service": "ia", "message": "Bonjour"}, follow_redirects=False)
    assert r.status_code == 302
    assert saved[0][:2] == ["Ana", "ana@example.com"] and "Intelligence Artificielle" in saved[0][3]
    assert leads_sent[0][:3] == ("Ana", "ana@example.com", "contact")
    assert "bien été envoyé" in c.get("/contact").text


def test_newsletter_subscription(monkeypatch):
    saved = []
    monkeypatch.setattr(leads.db, "execute", lambda sql, p=None: saved.append(p))
    monkeypatch.setattr(ines, "push_lead", lambda *a: None)
    c = _client()
    token = _token(c.get("/contact").text)
    assert c.post("/newsletter/subscribe", data={"_csrf_token": token, "email": "x"}).json()["success"] is False
    r = c.post("/newsletter/subscribe", data={"_csrf_token": token, "email": "Abo@Example.com"})
    assert r.json()["success"] is True and saved == [["abo@example.com"]]
