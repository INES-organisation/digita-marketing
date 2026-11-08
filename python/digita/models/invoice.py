"""Factures (équivalent de app/Models/Invoice.php), conformes depuis le 08/11/2026.

- Numéro attribué au paiement seulement (jamais à la création de la commande), par un compteur annuel :
  DM-2026-0001, DM-2026-0002… Le numéro est pris dans la même instruction SQL que l'insertion de la
  facture : si elle échoue, le compteur n'avance pas, d'où une série continue, sans trou ni doublon.
- Facture figée : vendeur, acheteur et lignes sont copiés dans `snapshot` (JSON) au moment de l'émission ;
  la page /facture/:id s'affiche à partir de cette copie.
"""
import json

from .. import db, php
from . import key

SELLER = {
    "name": "Digita Marketing (TONY ALPHA 8.0, EI)",
    "owner": "Anthony Legros, entrepreneur individuel",
    "address": "8 bis impasse des Jonquilles, 97430 Le Tampon, La Réunion",
    "siren": "844 384 198",
    "email": "contact@digita.buzz",
    "vat": "TVA non applicable, art. 293 B du CGI",
}


def create_from_order(order):
    """Émet la facture d'une commande payée (une seule par commande). Renvoie son identifiant."""
    existing = get_by_order_id(order["id"])
    if existing:
        return str(existing["id"])
    amount = php.floatval(order["amount"])
    year = int(php.date("Y"))
    items = db.fetch_all("SELECT product_name, product_type, quantity, price FROM order_items WHERE order_id = ? ORDER BY id",
                         [order["id"]])
    snapshot = json.dumps({
        "seller": SELLER,
        "buyer": {"name": order.get("billing_name") or order.get("customer_email"), "email": order.get("customer_email"),
                  "address": order.get("billing_address"), "company": order.get("billing_company"),
                  "siret": order.get("billing_siret")},
        "items": [{k: (str(v) if k == "price" else v) for k, v in i.items()} for i in items],
        "discount": str(order.get("discount_amount") or 0), "total": str(amount),
    }, ensure_ascii=False)
    row = db.fetch(
        """WITH n AS (
               INSERT INTO invoice_counters (year, last_number) VALUES (?, 1)
               ON CONFLICT (year) DO UPDATE SET last_number = invoice_counters.last_number + 1
               RETURNING last_number)
           INSERT INTO invoices (order_id, user_id, invoice_number, amount_ht, tax_rate, tax_amount, amount_ttc,
                                 billing_name, billing_email, billing_address, billing_company, billing_siret,
                                 status, paid_at, snapshot)
           SELECT ?, ?, 'DM-' || ? || '-' || lpad(n.last_number::text, 4, '0'), ?, 0, 0, ?, ?, ?, ?, ?, ?, 'paid', ?, ?
           FROM n RETURNING id, invoice_number""",
        [year, order["id"], order.get("user_id"), str(year), amount, amount,
         order.get("billing_name") or order.get("customer_email"), order.get("customer_email"), order.get("billing_address"),
         order.get("billing_company"), order.get("billing_siret"), php.date("Y-m-d H:i:s"), snapshot])
    db.execute("UPDATE orders SET invoice_number = ? WHERE id = ?", [row["invoice_number"], order["id"]])
    return str(row["id"])


def get_full_invoice(invoice_id):
    inv = db.fetch("""SELECT i.*, o.currency, o.discount_amount, o.promo_code_id
                      FROM invoices i JOIN orders o ON i.order_id = o.id WHERE i.id = ?""", [key(invoice_id)])
    if not inv:
        return None
    frozen = json.loads(inv["snapshot"]) if inv.get("snapshot") else None
    inv["seller"] = (frozen or {}).get("seller", SELLER)
    inv["items"] = frozen["items"] if frozen else db.fetch_all("SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
                                                              [inv["order_id"]])
    return inv


def get_by_order_id(order_id):
    return db.fetch("SELECT * FROM invoices WHERE order_id = ? ORDER BY id LIMIT 1", [key(order_id)])


def get_by_id(invoice_id):
    return db.fetch("SELECT * FROM invoices WHERE id = ?", [key(invoice_id)])


def unsynced(limit=50):
    """Factures pas encore enregistrées dans le livre des recettes d'INES."""
    return db.fetch_all("SELECT * FROM invoices WHERE ines_synced_at IS NULL ORDER BY id LIMIT ?", [limit])


def mark_synced(invoice_id):
    db.execute("UPDATE invoices SET ines_synced_at = NOW() WHERE id = ?", [key(invoice_id)])
