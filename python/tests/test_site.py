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


def test_inner_pages_use_horizontal_menu_and_services_bar():
    c = _client()
    for path in ("/contact", "/connexion", "/inscription", "/page-qui-n-existe-pas"):
        r = c.get(path)
        assert "navbar-site fixed-top" in r.text and 'class="sidebar-onglet-sidebar"' in r.text, path
        assert 'id="sidebar-agence"' in r.text and 'class="footer-premium"' in r.text, path
        assert 'class="sidebar-premium"' not in r.text, path
        assert 'href="/#hero-premium"' in r.text, path
    r = c.get("/page-qui-n-existe-pas")
    assert r.status_code == 404 and "Page non trouvée" in r.text and "noindex" in r.text
    assert 'aria-current="page"' in c.get("/contact").text


def test_home_uses_vertical_menu_anchored_on_sections():
    r = _client().get("/")
    assert 'class="sidebar-premium"' in r.text and 'class="footer-premium"' in r.text
    assert "navbar-site" not in r.text and "sidebar-onglet-sidebar" not in r.text
    for anchor in ("#enjeux", "#ecosysteme", "#collaboration", "#methode", "#realisations", "#hero-premium"):
        assert f'href="{anchor}"' in r.text, anchor
    assert 'id="realisations"' in r.text and "https://lp48.digita.buzz" in r.text
    for category in ("Sites web et landing", "Réseaux sociaux", "Publicité", "Automatisation", "Agents IA"):
        assert category in r.text, category
    for offer in ("Site vitrine offert", "590 €/mois", "490 €/mois", "890 € par scénario", "1 490 € + usage"):
        assert offer in r.text, offer
    for case in ("TTC France", "TTC Sales", "TatooModel", "Lurel"):
        assert case in r.text, case
    assert "Connexion" in r.text and "data-theme-toggle" in r.text and "Diagnostic gratuit" in r.text


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
