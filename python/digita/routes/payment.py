"""Paiement, commandes et factures (PaymentController.php)."""
import json

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import php
from ..models import formation as Formation
from ..models import invoice as Invoice
from ..models import order as Order
from ..render import base_context, render_view
from ..services import stripe
from .common import not_found, redirect

CSS = ["/assets/css/formations.css"]


def _json(payload, status=200):
    return Response(php.json_encode(payload), status_code=status, media_type="application/json")


def _find_formation(formation_id):
    # Formation::find() hérité de Model : SELECT * FROM formations WHERE id = ?
    from .. import db
    from ..models import key
    return db.fetch("SELECT * FROM formations WHERE id = ?", [key(formation_id)])


def _formation_of(order):
    for item in Order.get_order_items(order["id"]):
        if item.get("product_type") == "formation":
            return _find_formation(item["product_id"])
    return None


def checkout(request, formation_id):
    if "user_id" not in request.session:
        request.session["redirect_after_login"] = "/formations/checkout/" + formation_id
        return redirect("/connexion")
    f = _find_formation(formation_id)
    if not f:
        return not_found(request, formationId=formation_id, formation=f)
    user_id = request.session["user_id"]
    if Order.has_user_purchased_formation(user_id, formation_id):
        request.session["info_message"] = "Vous avez déjà acheté cette formation."
        return redirect("/formations/" + f["slug"] + "/learn")
    if php.floatval(f["price"]) <= 0:
        if not Formation.is_enrolled(user_id, php.num(formation_id)):
            Formation.enroll(user_id, formation_id)
        request.session["success_message"] = "Vous êtes inscrit à la formation !"
        return redirect("/formations/" + f["slug"] + "/learn")

    promo, discount, final = None, 0, php.floatval(f["price"])
    if php.t(request.query_params.get("promo")):
        promo = Order.validate_promo_code(request.query_params["promo"])
        if promo:
            discount = Order.calculate_discount(promo, final)
            final = max(0, final - php.floatval(discount))
    return render_view(request, "payment/checkout-content", {
        "title": "Paiement - " + php.strval(f["title"]) + " | Digita Marketing",
        "extraCss": CSS, "formation": f, "promoCode": promo, "discount": discount, "finalPrice": final,
        "stripePublicKey": stripe.public_key(), "stripeConfigured": stripe.is_configured(),
    })


async def process_checkout(request, formation_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    form = await request.form()
    return await run_in_threadpool(_process_checkout, request, formation_id, form)


def _process_checkout(request, formation_id, form):
    f = _find_formation(formation_id)
    if not f:
        return Response(b"", status_code=404, media_type="text/html")
    promo = Order.validate_promo_code(form["promo_code"]) if php.t(form.get("promo_code")) else None
    session = request.session
    order_id = Order.create_formation_order(session["user_id"], f, promo, session.get("user_email"))
    order = Order.find(order_id)
    if php.floatval(order["amount"]) <= 0:
        Order.fulfill_order(order_id, "free_promo", None)
        Invoice.create_from_order(order)
        session["success_message"] = "Formation offerte ! Vous êtes inscrit."
        return redirect("/formations/" + f["slug"] + "/learn")
    if not stripe.is_configured():
        session["error_message"] = ("Le paiement Stripe n'est pas encore configuré. "
                                    "Contactez-nous pour finaliser votre inscription.")
        return redirect("/formations/" + f["slug"])
    try:
        base = base_context(request)["base_url"]
        checkout_session = stripe.create_formation_checkout(
            f, order_id, base + "/paiement/succes", base + "/paiement/annulation?order_id=" + order_id,
            session.get("user_id"), session.get("user_email"))
        return redirect(checkout_session["url"])
    except stripe.StripeError as e:
        Order.update_status(order_id, "cancelled")
        session["error_message"] = "Erreur lors de la création du paiement : " + str(e)
        return redirect("/formations/checkout/" + formation_id)


def success(request):
    if "user_id" not in request.session:
        return redirect("/connexion")
    session_id = request.query_params.get("session_id")
    order = formation = None
    if php.t(session_id) and stripe.is_configured():
        result = stripe.verify_session(session_id)
        if result["success"]:
            order = Order.get_by_stripe_session(session_id)
            if order and order["status"] != "paid":
                Order.fulfill_order(order["id"], session_id, result["payment_intent"])
                Invoice.create_from_order(Order.find(order["id"]))
                order = Order.find(order["id"])
            if order:
                formation = _formation_of(order)
    return render_view(request, "payment/success-content", {
        "title": "Paiement réussi | Digita Marketing", "extraCss": CSS, "order": order, "formation": formation,
    })


def cancel(request):
    order_id = request.query_params.get("order_id")
    order = formation = None
    if php.t(order_id):
        order = Order.find(order_id)
        if order and order["status"] == "pending":
            Order.update_status(order_id, "cancelled")
        if order:
            formation = _formation_of(order)
    return render_view(request, "payment/cancel-content", {
        "title": "Paiement annulé | Digita Marketing", "extraCss": CSS, "order": order, "formation": formation,
    })


async def webhook(request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    result = await run_in_threadpool(stripe.handle_webhook, payload, sig)
    return _json(result, 200 if result["success"] else 400)


async def validate_promo(request):
    form = await request.form()
    q = request.query_params
    code = form["code"] if "code" in form else q.get("code", "")
    formation_id = form["formation_id"] if "formation_id" in form else q.get("formation_id", 0)
    if php.empty(code):
        return _json({"valid": False, "message": "Code promo requis"})
    return _json(await run_in_threadpool(_validate_promo, code, formation_id))


def _validate_promo(code, formation_id):
    promo = Order.validate_promo_code(code)
    if not promo:
        return {"valid": False, "message": "Code promo invalide ou expiré"}
    f = _find_formation(formation_id)
    discount = final = 0
    if f:
        discount = Order.calculate_discount(promo, php.floatval(f["price"]))
        final = max(0, php.floatval(f["price"]) - php.floatval(discount))
    value = promo["discount_value"]
    return {
        "valid": True, "discount_type": promo["discount_type"], "discount_value": value,
        "discount": discount, "final_price": final,
        "message": ("-" + php.strval(value) + "% appliqué !") if promo["discount_type"] == "percent"
        else ("-" + php.number_format(value, 2) + "€ appliqué !"),
    }


def my_orders(request):
    if "user_id" not in request.session:
        return redirect("/connexion")
    return render_view(request, "payment/my-orders-content", {
        "title": "Mes commandes | Digita Marketing", "extraCss": CSS,
        "orders": Order.get_user_orders(request.session["user_id"]),
    })


def order_detail(request, order_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    order = Order.get_full_order(order_id)
    if not order or not php.loose_eq(order["user_id"], request.session["user_id"]):
        return not_found(request, orderId=order_id, order=order)
    return render_view(request, "payment/order-detail-content", {
        "title": "Commande #" + order_id + " | Digita Marketing", "extraCss": CSS,
        "order": order, "invoice": Invoice.get_by_order_id(order_id),
    })


def invoice(request, invoice_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    inv = Invoice.get_full_invoice(invoice_id)
    if not inv or not php.loose_eq(inv["user_id"], request.session["user_id"]):
        return not_found(request, invoiceId=invoice_id, invoice=inv)
    return render_view(request, "payment/invoice-content", {
        "title": "Facture " + php.strval(inv["invoice_number"]) + " | Digita Marketing", "extraCss": CSS,
        "invoice": inv,
    })
