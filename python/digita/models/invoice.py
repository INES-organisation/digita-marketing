"""Factures (équivalent de app/Models/Invoice.php)."""
from .. import db, php
from . import key


def create_from_order(order):
    amount_ht = php.floatval(order["amount"])
    tax_amount = php.php_round(amount_ht * 0 / 100, 2)
    number = order.get("invoice_number") if order.get("invoice_number") is not None else generate_number()
    billing_name = order.get("billing_name") if order.get("billing_name") is not None else order.get("customer_email")
    row = db.fetch(
        """INSERT INTO invoices (order_id, user_id, invoice_number, amount_ht, tax_rate, tax_amount, amount_ttc,
                                 billing_name, billing_email, billing_address, status, paid_at)
           VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 'paid', ?) RETURNING id""",
        [order["id"], order["user_id"], number, amount_ht, tax_amount, amount_ht + tax_amount,
         billing_name, order.get("customer_email"), order.get("billing_address"), php.date("Y-m-d H:i:s")])
    return str(row["id"])


def get_full_invoice(invoice_id):
    inv = db.fetch("""SELECT i.*, o.currency, o.discount_amount, o.promo_code_id
                      FROM invoices i JOIN orders o ON i.order_id = o.id WHERE i.id = ?""", [key(invoice_id)])
    if not inv:
        return None
    inv["items"] = db.fetch_all("SELECT * FROM order_items WHERE order_id = ? ORDER BY id", [inv["order_id"]])
    return inv


def get_by_order_id(order_id):
    return db.fetch("SELECT * FROM invoices WHERE order_id = ? ORDER BY id LIMIT 1", [key(order_id)])


def generate_number():
    ym = php.date("Ym")
    n = db.fetch("SELECT COUNT(*) as count FROM invoices WHERE invoice_number LIKE ?", [f"FA-{ym}-%"])["count"]
    return "FA-%s-%04d" % (ym, (n or 0) + 1)
