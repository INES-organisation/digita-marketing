import hashlib
import hmac
import json
import time

from digita.services import stripe


def _sign(payload, secret, ts=None):
    ts = str(ts or int(time.time()))
    sig = hmac.new(secret.encode(), ts.encode() + b"." + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_flatten_matches_stripe_encoding():
    assert stripe._flatten({"line_items": [{"price_data": {"currency": "eur"}, "quantity": 1}],
                            "metadata": {"user_id": None, "order_id": "7"}}) == [
        ("line_items[0][price_data][currency]", "eur"), ("line_items[0][quantity]", "1"),
        ("metadata[order_id]", "7")]


def test_webhook_requires_secret(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    assert stripe.handle_webhook(b"{}", "") == {"success": False, "error": "Webhook secret non configuré"}


def test_webhook_signature(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    payload = json.dumps({"type": "customer.created", "data": {"object": {}}}).encode()
    assert stripe.handle_webhook(payload, _sign(payload, "whsec_test")) == {
        "success": True, "message": "Événement ignoré: customer.created"}
    assert stripe.handle_webhook(payload, _sign(payload, "autre"))["error"] == "Signature invalide"
    old = _sign(payload, "whsec_test", int(time.time()) - 3600)
    assert stripe.handle_webhook(payload, old)["error"] == "Signature invalide"
    assert stripe.handle_webhook(b"pas du json", _sign(b"pas du json", "whsec_test"))["error"] == "Payload invalide"
