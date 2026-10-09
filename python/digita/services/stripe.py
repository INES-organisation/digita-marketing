"""Stripe (équivalent de app/Services/StripeService.php), via l'API HTTP de Stripe.

Le PHP appelait le SDK stripe-php, qui n'était ni déclaré dans composer.json ni chargé :
avec une clé configurée, le paiement plantait. Ici les appels passent directement par
l'API REST (création et lecture de sessions Checkout, vérification de signature des webhooks).
"""
import hashlib
import hmac
import json
import logging
import os
import time

import httpx

from .. import db, php
from ..models import invoice as Invoice
from ..models import order as Order
from . import email

log = logging.getLogger("digita.stripe")
API = "https://api.stripe.com/v1"
TOLERANCE = 300


class StripeError(Exception):
    pass


def secret_key():
    return os.getenv("STRIPE_SECRET_KEY", "")


def public_key():
    return os.getenv("STRIPE_PUBLIC_KEY", "")


def is_configured():
    return bool(secret_key())


def _flatten(data, prefix=""):
    """Encodage « a[b][0][c]=… » attendu par l'API Stripe."""
    out = []
    items = data.items() if isinstance(data, dict) else enumerate(data)
    for k, v in items:
        name = f"{prefix}[{k}]" if prefix else str(k)
        if isinstance(v, (dict, list)):
            out.extend(_flatten(v, name))
        elif v is not None:
            out.append((name, php.strval(v)))
    return out


def _call(method, path, data=None):
    try:
        r = httpx.request(method, API + path, data=_flatten(data) if data else None,
                          auth=(secret_key(), ""), timeout=30)
    except httpx.HTTPError as e:
        raise StripeError(str(e)) from e
    body = r.json() if r.content else {}
    if r.status_code >= 400:
        raise StripeError((body.get("error") or {}).get("message") or f"HTTP {r.status_code}")
    return body


def create_formation_checkout(formation, order_id, success_url, cancel_url, user_id, user_email):
    if not is_configured():
        raise StripeError("Stripe non configuré. Veuillez renseigner STRIPE_SECRET_KEY dans .env")
    description = php.mb_strimwidth(php.strip_tags(formation.get("description") or ""), 0, 200, "...")
    product = {"name": formation["title"], "images": [formation["image"]] if php.t(formation.get("image")) else []}
    if description:
        product["description"] = description  # Stripe refuse une description vide
    session = _call("POST", "/checkout/sessions", {
        "payment_method_types": ["card"],
        "line_items": [{
            "price_data": {"currency": "eur", "product_data": product,
                           "unit_amount": int(php.php_round(php.floatval(formation["price"]) * 100))},
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "client_reference_id": str(order_id),
        "customer_email": user_email,
        "metadata": {"order_id": order_id, "formation_id": formation["id"], "user_id": user_id},
    })
    Order.set_stripe_session(order_id, session["id"])
    return session


def verify_session(session_id):
    if not is_configured():
        return {"success": False, "error": "Stripe non configuré"}
    try:
        s = _call("GET", f"/checkout/sessions/{session_id}")
    except StripeError as e:
        return {"success": False, "error": str(e)}
    return {"success": s.get("payment_status") == "paid", "order_id": s.get("client_reference_id"),
            "amount": (s.get("amount_total") or 0) / 100, "currency": s.get("currency"),
            "customer_email": s.get("customer_email"), "payment_intent": s.get("payment_intent")}


def _construct_event(payload, sig_header, secret):
    parts = [p.split("=", 1) for p in sig_header.split(",") if "=" in p]
    ts = next((v for k, v in parts if k == "t"), None)
    sigs = [v for k, v in parts if k == "v1"]
    if not ts or not sigs:
        raise PermissionError
    expected = hmac.new(secret.encode(), ts.encode() + b"." + payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, s) for s in sigs):
        raise PermissionError
    if abs(time.time() - int(ts)) > TOLERANCE:
        raise PermissionError
    try:
        return json.loads(payload)
    except ValueError as e:
        raise ValueError("payload") from e


def handle_webhook(payload, sig_header):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        return {"success": False, "error": "Webhook secret non configuré"}
    try:
        event = _construct_event(payload, sig_header, secret)
    except PermissionError:
        return {"success": False, "error": "Signature invalide"}
    except (ValueError, TypeError):
        return {"success": False, "error": "Payload invalide"}
    obj = (event.get("data") or {}).get("object") or {}
    kind = event.get("type")
    if kind == "checkout.session.completed":
        return _checkout_completed(obj)
    if kind == "payment_intent.payment_failed":
        for o in db.fetch_all("SELECT * FROM orders WHERE stripe_payment_intent = ? OR stripe_session_id LIKE ?",
                                    [obj.get("id"), "%" + php.strval(obj.get("id")) + "%"]):
            Order.update_status(o["id"], "cancelled")
        return {"success": True, "message": "Paiement échoué traité"}
    if kind == "charge.refunded":
        o = db.fetch("SELECT * FROM orders WHERE stripe_payment_intent = ? ORDER BY id LIMIT 1",
                           [obj.get("payment_intent")])
        if o:
            Order.update_status(o["id"], "refunded")
        return {"success": True, "message": "Remboursement traité"}
    return {"success": True, "message": "Événement ignoré: " + php.strval(kind)}


def _checkout_completed(session):
    order_id = session.get("client_reference_id")
    if not order_id:
        o = Order.get_by_stripe_session(session.get("id"))
        order_id = o["id"] if o else None
    if not order_id:
        return {"success": False, "error": "Commande introuvable"}
    order = Order.fulfill_order(order_id, session.get("id"), session.get("payment_intent"))
    if order:
        Invoice.create_from_order(order)
    if order and php.t(order.get("customer_email")):
        try:
            email.send_order_confirmation(order["customer_email"], order["id"])
        except Exception as e:  # noqa: BLE001
            log.error("Erreur envoi email confirmation: %s", e)
    return {"success": True, "order_id": order_id}
