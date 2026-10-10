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
    def boom(*a, **k):
        raise httpx.ConnectError("INES arrêté")
    monkeypatch.setattr(ines.httpx, "post", boom)
    ines._post_lead({"tags": ["DIGITA", "audit"]})  # journalise seulement


def test_chat_uses_ines_gateway_when_configured(monkeypatch):
    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_x")
    calls = _capture(monkeypatch, {"text": "Bonjour !"})
    assert ai.chat([{"content": "Salut"}], "Tu es l'assistant DIGITA") == "Bonjour !"
    url, body, _ = calls[0]
    assert url.endswith("/api/v1/generate") and body["no_cache"] is True
    assert body["system"] == "Tu es l'assistant DIGITA"
    assert body["messages"] == [{"role": "user", "content": "Salut"}]
