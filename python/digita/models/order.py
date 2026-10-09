"""Commandes et codes promo (équivalent de app/Models/Order.php)."""
from .. import db, php
from . import key


def find(order_id):
    return db.fetch("SELECT * FROM orders WHERE id = ?", [key(order_id)])


def get_user_orders(user_id, limit=20):
    return db.fetch_all(
        """SELECT o.*, string_agg(oi.product_name, ', ' ORDER BY oi.id) as items_summary,
                  COUNT(oi.id) as item_count
           FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id
           WHERE o.user_id = ? GROUP BY o.id
           ORDER BY o.created_at DESC NULLS LAST, o.id DESC LIMIT ?""", [user_id, limit])


def get_order_items(order_id):
    return db.fetch_all("SELECT oi.* FROM order_items oi WHERE oi.order_id = ? ORDER BY oi.id", [key(order_id)])


def get_full_order(order_id):
    order = find(order_id)
    if not order:
        return None
    order["items"] = get_order_items(order_id)
    return order


def get_by_stripe_session(session_id):
    return db.fetch("SELECT * FROM orders WHERE stripe_session_id = ? ORDER BY id LIMIT 1", [session_id])


def create_formation_order(user_id, formation, promo, user_email):
    amount = php.floatval(formation["price"])
    discount = 0
    promo_id = None
    if promo:
        discount = calculate_discount(promo, amount)
        promo_id = promo["id"]
        amount = max(0, amount - discount)
    row = db.fetch(
        """INSERT INTO orders (user_id, amount, currency, status, customer_email, invoice_number,
                               promo_code_id, discount_amount)
           VALUES (?, ?, 'EUR', 'pending', ?, ?, ?, ?) RETURNING id""",
        [user_id, amount, user_email, generate_invoice_number(), promo_id, discount])
    order_id = str(row["id"])  # lastInsertId()
    db.execute("""INSERT INTO order_items (order_id, product_id, product_type, product_name, quantity, price)
                  VALUES (?, ?, 'formation', ?, 1, ?)""", [order_id, formation["id"], formation["title"], formation["price"]])
    return order_id


def fulfill_order(order_id, stripe_session_id, payment_intent=None):
    db.execute("""UPDATE orders SET status = 'paid', stripe_session_id = ?, stripe_payment_intent = ?,
                  updated_at = NOW() WHERE id = ?""", [stripe_session_id, payment_intent, key(order_id)])
    order = find(order_id)
    for item in get_order_items(order_id):
        if item.get("product_type") == "formation" and php.t(order and order.get("user_id")):
            _enroll(order["user_id"], item["product_id"])
    if order and php.t(order.get("promo_code_id")):
        db.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?", [order["promo_code_id"]])
    return order


def _enroll(user_id, formation_id):
    if not db.fetch("SELECT id FROM formation_enrollments WHERE user_id = ? AND formation_id = ?", [user_id, formation_id]):
        db.execute("INSERT INTO formation_enrollments (user_id, formation_id, enrolled_at) "
                   "VALUES (?, ?, NOW())", [user_id, formation_id])
        db.execute("UPDATE formations SET enrolled_count = enrolled_count + 1 WHERE id = ?", [formation_id])


def update_status(order_id, status):
    db.execute("UPDATE orders SET status = ? WHERE id = ?", [status, key(order_id)])


def set_stripe_session(order_id, session_id):
    db.execute("UPDATE orders SET stripe_session_id = ? WHERE id = ?", [session_id, key(order_id)])


def has_user_purchased_formation(user_id, formation_id):
    return bool(db.fetch(
        """SELECT o.id FROM orders o JOIN order_items oi ON o.id = oi.order_id
           WHERE o.user_id = ? AND oi.product_id = ? AND oi.product_type = 'formation' AND o.status = 'paid'
           LIMIT 1""", [user_id, key(formation_id)]))


def validate_promo_code(code):
    # MySQL compare les codes sans tenir compte de la casse (collation *_ci).
    return db.fetch(
        """SELECT * FROM promo_codes WHERE LOWER(code) = LOWER(?) AND is_active = 1
           AND (max_uses IS NULL OR used_count < max_uses)
           AND (valid_from IS NULL OR valid_from <= LOCALTIMESTAMP)
           AND (valid_until IS NULL OR valid_until >= LOCALTIMESTAMP) ORDER BY id LIMIT 1""", [code])


def calculate_discount(promo, amount):
    if promo["discount_type"] == "percent":
        return php.php_round(amount * float(promo["discount_value"]) / 100, 2)
    # min() PHP entre la chaîne DECIMAL et le montant : la plus petite valeur, telle quelle.
    return promo["discount_value"] if float(promo["discount_value"]) <= amount else amount


def generate_invoice_number():
    ym = php.date("Ym")
    n = db.fetch("SELECT COUNT(*) as count FROM orders WHERE invoice_number LIKE ?", [f"DM-{ym}-%"])["count"]
    return "DM-%s-%04d" % (ym, (n or 0) + 1)
