"""« Se connecter avec INES » : aller-retour complet côté DIGITA (INES simulé)."""
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from starlette.testclient import TestClient

from digita import sessions
from digita.main import app
from digita.routes import auth
from digita.services import ines_sso


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    store = {}
    monkeypatch.setattr(sessions, "_load", lambda sid: store.get(sid))
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: store.__setitem__(sid, data))
    monkeypatch.setenv("INES_OIDC_CLIENT_ID", "digita")
    monkeypatch.setenv("INES_OIDC_CLIENT_SECRET", "secret")
    calls = []

    def post(url, **kw):
        calls.append(kw)
        return httpx.Response(200, json={"access_token": "at"}, request=httpx.Request("POST", url))

    def get(url, **kw):
        return httpx.Response(200, json={"sub": "u1", "email": "Ana@Site.test", "email_verified": True},
                              request=httpx.Request("GET", url))

    monkeypatch.setattr(ines_sso.httpx, "post", post)
    monkeypatch.setattr(ines_sso.httpx, "get", get)
    linked = []
    monkeypatch.setattr(auth, "_user_from_ines", lambda info: linked.append(info) or {"id": 7, "email": info["email"]})
    return calls, linked


def test_login_with_ines(setup):
    calls, linked = setup
    c = TestClient(app, base_url="https://digita.buzz")
    assert "/auth/ines" in c.get("/connexion").text
    r = c.get("/auth/ines", follow_redirects=False)
    q = parse_qs(urlsplit(r.headers["location"]).query)
    assert q["client_id"] == ["digita"] and q["code_challenge_method"] == ["S256"]

    bad = c.get("/auth/ines/callback", params={"code": "c", "state": "faux"}, follow_redirects=False)
    assert bad.headers["location"] == "/connexion"  # état refusé, demande consommée

    r = c.get("/auth/ines", follow_redirects=False)
    state = parse_qs(urlsplit(r.headers["location"]).query)["state"][0]
    r = c.get("/auth/ines/callback", params={"code": "c", "state": state}, follow_redirects=False)
    assert r.headers["location"] == "/admin/dashboard"
    assert linked[-1]["email"] == "ana@site.test" and calls[-1]["data"]["code_verifier"]


def test_unverified_email_refused(setup, monkeypatch):
    monkeypatch.setattr(ines_sso.httpx, "get", lambda url, **kw: httpx.Response(
        200, json={"sub": "u1", "email": "a@b.c", "email_verified": False}, request=httpx.Request("GET", url)))
    s = {}
    url = ines_sso.authorize_url(s, "https://digita.buzz/auth/ines/callback")
    state = parse_qs(urlsplit(url).query)["state"][0]
    with pytest.raises(ines_sso.SSOError):
        ines_sso.fetch_identity(s, {"code": "c", "state": state})
