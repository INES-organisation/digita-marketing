"""Paiement Stripe des formations, par les services d'INES.

Les clés Stripe ne vivent que dans INES (/admin/integrations) : Digita crée et relit ses
sessions Checkout via /api/v1/external/stripe/… avec sa clé API INES. La commande est validée
au retour sur /paiement/succes, et chaque nuit par cron.reconcile_orders pour un visiteur qui
aurait fermé l'onglet avant ce retour (le webhook Stripe arrive à INES, qui l'ignore).
"""
import logging

import httpx

from .. import php
from ..models import invoice as Invoice
from ..models import order as Order
from . import email, ines

log = logging.getLogger("digita.stripe")


class StripeError(Exception):
    pass


def is_configured():
    if not ines.enabled():
        return False
    try:
        r = httpx.get(ines._url("/api/v1/external/stripe/config"), headers=ines._headers(), timeout=5)
        return r.status_code == 200 and bool(r.json().get("configured"))
    except httpx.HTTPError:
        return False


def _call(method, path, json=None):
    try:
        r = httpx.request(method, ines._url("/api/v1/external/stripe" + path), json=json,
                          headers=ines._headers(), timeout=30)
    except httpx.HTTPError as e:
        raise StripeError(str(e)) from e
    body = r.json() if r.content else {}
    if r.status_code >= 400:
        raise StripeError(body.get("detail") or f"HTTP {r.status_code}")
    return body


def create_formation_checkout(formation, order_id, amount, success_url, cancel_url, user_id, user_email):
    description = php.mb_strimwidth(php.strip_tags(formation.get("description") or ""), 0, 200, "...")
    product = {"name": formation["title"], "images": [formation["image"]] if php.t(formation.get("image")) else []}
    if description:
        product["description"] = description  # Stripe refuse une description vide
    session = _call("POST", "/checkout-sessions", {"site": "digita", "params": {
        "line_items": [{
            "price_data": {"currency": "eur", "product_data": product,
                           "unit_amount": int(php.php_round(php.floatval(amount) * 100))},  # promo déduite
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
        "client_reference_id": str(order_id),
        "customer_email": user_email,
        "metadata": {"order_id": order_id, "formation_id": formation["id"], "user_id": user_id},
    }})
    Order.set_stripe_session(order_id, session["id"])
    return session


def verify_session(session_id):
    try:
        s = _call("GET", f"/checkout-sessions/{session_id}")
    except StripeError as e:
        return {"success": False, "error": str(e)}
    return {"success": s.get("payment_status") == "paid", "order_id": s.get("client_reference_id"),
            "amount": (s.get("amount_total") or 0) / 100, "currency": s.get("currency"),
            "customer_email": s.get("customer_email"), "payment_intent": s.get("payment_intent")}


def complete(session_id):
    """Valide la commande d'une session payée (une seule fois) : inscription, facture, e-mail.
    Renvoie la commande, ou None si la session n'est pas payée ou inconnue."""
    result = verify_session(session_id)
    order = Order.get_by_stripe_session(session_id) if result["success"] else None
    if not order:
        return None
    if order["status"] != "paid":
        Order.fulfill_order(order["id"], session_id, result["payment_intent"])
        Invoice.create_from_order(Order.find(order["id"]))
        if php.t(order.get("customer_email")):
            try:
                email.send_order_confirmation(order["customer_email"], order["id"])
            except Exception as e:  # noqa: BLE001
                log.error("Erreur envoi email confirmation: %s", e)
    return Order.find(order["id"])
