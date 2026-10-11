"""E-mails et anciennes tâches cron, désormais pris en charge par INES."""
import asyncio

from starlette.requests import Request

from digita import db
from digita.models import article, formation
from digita.routes import automation
from digita.services import email, ines


def _request(path, headers=None, query=b""):
    return Request({"type": "http", "method": "POST", "path": path, "query_string": query,
                    "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]})


def test_email_goes_through_ines_only_with_key(monkeypatch):
    calls = []
    monkeypatch.setattr(ines, "send_email", lambda *a: calls.append(a) or True)
    monkeypatch.delenv("INES_API_KEY", raising=False)
    assert email.send("a@example.com", "Sujet", "<p>x</p>") is False and calls == []
    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_test")
    monkeypatch.setenv("MAIL_FROM", "noreply@digita.buzz")
    assert email.send("a@example.com", "Sujet", "<p>x</p>") is True
    assert calls == [("a@example.com", "Sujet", "<p>x</p>", "Digita Marketing", "noreply@digita.buzz")]


def test_cron_requires_ines_token_and_newsletter_unsubscribes(monkeypatch):
    monkeypatch.setenv("PROJECT_CRON_TOKEN", "secret-partage")
    sent = []
    monkeypatch.setattr(db, "fetch_all", lambda sql, p=None: [{"email": "Abo@Example.com"}])
    monkeypatch.setattr(article, "get_all_published", lambda n=None: [{"title": "A<b>", "excerpt": "x", "slug": "a"}])
    monkeypatch.setattr(formation, "get_all_published", lambda n=None: [{"title": "F", "description": "<p>d</p>", "slug": "f"}])
    monkeypatch.setattr(email, "send", lambda to, subject, html: sent.append((to, html)) or True)

    assert asyncio.run(automation.newsletter(_request("/internal/cron/newsletter"))).status_code == 403
    bad = {"Authorization": "Bearer faux"}
    assert asyncio.run(automation.newsletter(_request("/internal/cron/newsletter", bad))).status_code == 403
    ok = asyncio.run(automation.newsletter(_request("/internal/cron/newsletter",
                                                    {"Authorization": "Bearer secret-partage"})))
    assert ok.status_code == 200 and b'"sent":1' in ok.body
    to, html = sent[0]
    assert to == "Abo@Example.com" and "A&lt;b&gt;" in html and "/blog/a" in html
    sig = automation.unsubscribe_sig("abo@example.com")
    assert "sig=" + sig in html

    updates = []
    monkeypatch.setattr(db, "execute", lambda sql, p=None: updates.append(p))
    good = _request("/newsletter/unsubscribe", query=f"email=Abo%40Example.com&sig={sig}".encode())
    assert asyncio.run(automation.unsubscribe(good)).status_code == 200 and updates == [["abo@example.com"]]
    forged = _request("/newsletter/unsubscribe", query=b"email=autre%40example.com&sig=" + sig.encode())
    assert asyncio.run(automation.unsubscribe(forged)).status_code == 400 and len(updates) == 1


def test_sitemap_is_built_from_published_content(monkeypatch):
    monkeypatch.setattr(automation.config, "APP_URL", "https://digita.buzz")
    monkeypatch.setattr(article, "get_all_published", lambda n=None: [{"slug": "seo", "updated_at": "2026-09-01 10:00:00"}])
    monkeypatch.setattr(article, "get_categories", lambda: [{"slug": "ia"}])
    monkeypatch.setattr(formation, "get_all_published", lambda n=None: [{"slug": "ads", "updated_at": None, "created_at": "2026-05-02"}])
    monkeypatch.setattr(formation, "get_categories", lambda: [])
    xml = automation.sitemap_xml()
    assert "<loc>https://digita.buzz/blog/seo</loc>" in xml and "<lastmod>2026-09-01</lastmod>" in xml
    assert "<loc>https://digita.buzz/formations/ads</loc>" in xml and "<lastmod>2026-05-02</lastmod>" in xml
    assert "https://digita.buzz/blog/categorie/ia" in xml and "localhost" not in xml
