from digita.services import stripe


class _Resp:
    def __init__(self, data, status=200):
        self.data, self.status_code, self.content = data, status, b"x"

    def json(self):
        return self.data


def test_checkout_goes_through_ines_with_order_amount(monkeypatch):
    calls, saved = [], []
    monkeypatch.setenv("INES_API_KEY", "ines_pro_sk_x")
    monkeypatch.setattr(stripe.httpx, "request",
                        lambda m, url, json, headers, timeout: calls.append((m, url, json)) or _Resp({"id": "cs_1", "url": "u"}))
    monkeypatch.setattr(stripe.Order, "set_stripe_session", lambda oid, sid: saved.append((oid, sid)))
    f = {"id": 3, "title": "SEO", "description": "", "price": "100.00", "image": ""}
    stripe.create_formation_checkout(f, "9", 80, "https://d/ok", "https://d/ko", 4, "a@b.fr")
    method, url, body = calls[0]
    assert url == "http://ines-backend:8000/api/v1/external/stripe/checkout-sessions" and body["site"] == "digita"
    params = body["params"]
    assert params["line_items"][0]["price_data"]["unit_amount"] == 8000  # promo déduite, pas le prix plein
    assert "payment_method_types" not in params and params["client_reference_id"] == "9"
    assert saved == [("9", "cs_1")]


def test_complete_fulfills_paid_order_once(monkeypatch):
    orders = {"7": {"id": "7", "status": "pending", "customer_email": "a@b.fr"}}
    done, mails = [], []
    monkeypatch.setattr(stripe, "verify_session", lambda sid: {"success": True, "payment_intent": "pi"})
    monkeypatch.setattr(stripe.Order, "get_by_stripe_session", lambda sid: orders["7"])
    monkeypatch.setattr(stripe.Order, "find", lambda oid: orders[oid])
    monkeypatch.setattr(stripe.Order, "fulfill_order",
                        lambda oid, sid, pi: done.append(oid) or orders[oid].update(status="paid"))
    monkeypatch.setattr(stripe.Invoice, "create_from_order", lambda o: None)
    monkeypatch.setattr(stripe.email, "send_order_confirmation", lambda to, oid: mails.append(to))
    monkeypatch.setattr(stripe.Shop, "order_products", lambda oid: [])
    assert stripe.complete("cs_1")["status"] == "paid"
    stripe.complete("cs_1")  # déjà payée : rien de plus
    assert done == ["7"] and mails == ["a@b.fr"]


def test_complete_delivers_shop_order(monkeypatch):
    from digita import boutique

    orders = {"8": {"id": "8", "status": "pending", "customer_email": "c@d.fr", "user_id": 5, "amount": "29.00"}}
    sent, leads = [], []
    monkeypatch.setattr(stripe, "verify_session", lambda sid: {"success": True, "payment_intent": "pi"})
    monkeypatch.setattr(stripe.Order, "get_by_stripe_session", lambda sid: orders["8"])
    monkeypatch.setattr(stripe.Order, "find", lambda oid: orders[oid])
    monkeypatch.setattr(stripe.Order, "fulfill_order", lambda oid, sid, pi: orders[oid].update(status="paid"))
    monkeypatch.setattr(stripe.Invoice, "create_from_order", lambda o: None)
    monkeypatch.setattr(stripe.Shop, "order_products", lambda oid: [boutique.product("pack-commerce")])
    monkeypatch.setattr(stripe.Shop, "issue_downloads", lambda oid, uid: [{"token": "t1", "file_name": "pack-commerce.md"}])
    monkeypatch.setattr(stripe.email, "send_shop_delivery", lambda to, oid, products, links: sent.append((to, links)))
    monkeypatch.setattr(stripe.email, "send_order_confirmation", lambda *a: (_ for _ in ()).throw(AssertionError("formation")))
    monkeypatch.setattr(stripe.ines, "push_lead", lambda *a, **k: leads.append((a, k)))
    stripe.complete("cs_2")
    assert sent == [("c@d.fr", [{"token": "t1", "file_name": "pack-commerce.md"}])]
    assert leads and "boutique:pack-commerce" in leads[0][1]["tags"]


def test_shop_delivery_email_has_download_buttons():
    from digita import boutique
    from digita.services import email

    html = email.shop_delivery_template("8", [boutique.product("pack-commerce"), boutique.product("devis-ia")],
                                        [{"token": "abc", "file_name": "pack-commerce.md"}])
    assert "/telecharger/abc" in html and "rendez-vous de lancement" in html and "Mes commandes" in html
