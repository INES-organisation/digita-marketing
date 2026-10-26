import threading

import httpx

from digita.services import ai, ines


class _Resp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def _capture(monkeypatch, data=None):
    calls = []

    def post(url, json, headers, timeout):
        calls.append((url, json, headers))
        return _Resp(data or {})
    monkeypatch.setattr(ines.httpx, "post", post)
    return calls


def _join_threads():
    for t in threading.enumerate():
        if t is not threading.current_thread() and t.daemon:
            t.join(2)


def test_lead_goes_to_ines_crm_only_with_key(monkeypatch):
    calls = _capture(monkeypatch)
    monkeypatch.delenv("INES_API_KEY", raising=False)
    ines.push_lead("Jeanne", "j@example.com", "audit", "Demande")
    assert calls == []

    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_x")
    ines.push_lead("Jeanne", "j@example.com", "audit", "Demande")
    _join_threads()
    url, body, headers = calls[0]
    assert url == "http://ines-backend:8000/api/v1/contacts/ingest"
    assert body["tags"] == ["DIGITA", "audit"] and body["email"] == "j@example.com"
    assert headers["Authorization"] == "Bearer ines_pro_sk_x"


def test_ines_failure_never_breaks_the_form(monkeypatch):
    attempts = []

    def boom(*a, **k):
        attempts.append(1)
        raise httpx.ConnectError("INES arrêté")
    monkeypatch.setattr(ines.httpx, "post", boom)
    lead = {"name": "Jeanne", "email": "j@example.com", "tags": ["DIGITA", "audit"]}
    assert ines._post_lead(lead, delays=(0, 0, 0)) is False  # journalise seulement
    assert len(attempts) == 3  # nouvelles tentatives avant d'abandonner


def test_chat_uses_ines_gateway_when_configured(monkeypatch):
    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_x")
    calls = _capture(monkeypatch, {"text": "Bonjour !"})
    assert ai.chat([{"content": "Salut"}], "Tu es l'assistant DIGITA") == "Bonjour !"
    url, body, _ = calls[0]
    assert url.endswith("/api/v1/generate") and body["no_cache"] is True
    assert body["system"] == "Tu es l'assistant DIGITA"
    assert body["messages"] == [{"role": "user", "content": "Salut"}]


def test_prompt_only_call_sends_prompt_as_user_message(monkeypatch):
    # _route_intention appelle ai.chat([], prompt) : sans ce cas, INES recevait un message vide → 502.
    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_x")
    calls = _capture(monkeypatch, {"text": "projet"})
    assert ai.chat([], "Classe cette demande") == "projet"
    _, body, _ = calls[0]
    assert body["messages"] == [{"role": "user", "content": "Classe cette demande"}] and body["system"] is None


def test_lead_goes_through_ines_acquisition_agent(monkeypatch):
    """Avec `outreach`, le lead passe par l'agent 24/7 d'INES ; agent désactivé → fiche CRM simple."""
    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_x")
    calls = _capture(monkeypatch, {"status": "created"})
    ines._post_web_lead({"source": "digita.buzz — diagnostic", "outreach": True}, {"tags": ["DIGITA", "diagnostic"]})
    assert calls[0][0].endswith("/api/v1/acquisition/web/lead") and len(calls) == 1

    calls = _capture(monkeypatch, {"status": "disabled"})
    ines._post_web_lead({"source": "x"}, {"name": "A", "email": "a@example.com", "tags": ["DIGITA", "contact"]})
    assert [c[0].rsplit("/", 2)[-2:] for c in calls] == [["web", "lead"], ["contacts", "ingest"]]
