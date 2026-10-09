from digita.routes.chatbot import fallback_reply
from digita.services import ai


def test_calculate_roi_matches_php():
    # Valeurs relevées sur AIService::calculateROI (PHP 8.3)
    assert ai.calculate_roi({"budget": "1000", "cpc": "1.3"}) == {
        "budget": 1000.0, "clicks": 769.0, "conversions": 15.0, "revenue": 1500.0, "profit": 450.0,
        "roi": -55.0, "cpa": 66.67, "roas": 1.5}
    assert ai.calculate_roi({"budget": "0"}) == {"error": "Budget et CPC doivent être supérieurs à 0"}


def test_valid_url():
    assert ai.valid_url("https://example.com/a?b=1")
    assert not ai.valid_url("pas une url")
    assert not ai.valid_url("http://")
    assert not ai.valid_url("example.com")


def test_audit_refuses_internal_addresses(monkeypatch):
    monkeypatch.delenv("DIGITA_AUDIT_ALLOW_PRIVATE", raising=False)
    assert not ai._public_host("127.0.0.1")
    assert not ai._public_host("10.0.0.5")
    res = ai.audit_seo("http://127.0.0.1:1/")
    assert res["error"] == "Impossible d'accéder à l'URL (HTTP 0)"


def test_fallback_reply():
    assert fallback_reply("Quel TARIF ?").startswith("Nos tarifs")
    assert fallback_reply("Coût").startswith("Nos tarifs")
    assert fallback_reply("rien").startswith("Merci pour votre message")
