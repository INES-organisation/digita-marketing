"""Commandes de la boutique et liens de téléchargement (tables orders, order_items, shop_downloads).

Une commande de boutique est une commande ordinaire (même paiement Stripe via INES, même facture,
même « Mes commandes ») dont la ligne a product_type = 'pack' et product_slug = l'identifiant
du produit dans digita/boutique.py.
"""
import secrets
from datetime import datetime, timedelta

from .. import boutique, db
from . import key
from .order import generate_invoice_number


def create_order(user_id, product, user_email, consent_text, consent_ip):
    row = db.fetch(
        """INSERT INTO orders (user_id, amount, currency, status, customer_email, invoice_number, discount_amount,
                               consent_text, consent_at, consent_ip)
           VALUES (?, ?, 'EUR', 'pending', ?, ?, 0, ?, NOW(), ?) RETURNING id""",
        [user_id, product["price"], user_email, generate_invoice_number(), consent_text, (consent_ip or "")[:45]])
    order_id = str(row["id"])
    db.execute("""INSERT INTO order_items (order_id, product_id, product_type, product_slug, product_name, quantity, price)
                  VALUES (?, 0, 'pack', ?, ?, 1, ?)""", [order_id, product["slug"], product["title"], product["price"]])
    return order_id


def order_products(order_id):
    """Produits de boutique d'une commande (dans l'ordre des lignes)."""
    rows = db.fetch_all("SELECT product_slug FROM order_items WHERE order_id = ? AND product_type = 'pack' ORDER BY id",
                        [key(order_id)])
    return [p for p in (boutique.product(r["product_slug"]) for r in rows) if p]


def issue_downloads(order_id, user_id):
    """Crée les liens de téléchargement d'une commande payée (une seule fois). Renvoie les liens actifs."""
    if not db.fetch("SELECT 1 AS ok FROM shop_downloads WHERE order_id = ? LIMIT 1", [key(order_id)]):
        for product in order_products(order_id):
            for name in product.get("files", []):
                _new_link(order_id, user_id, product["slug"], name)
    return links(order_id)


def _new_link(order_id, user_id, slug, file_name):
    token = secrets.token_urlsafe(32)
    db.execute("""INSERT INTO shop_downloads (token, order_id, user_id, product_slug, file_name, expires_at, max_downloads)
                  VALUES (?, ?, ?, ?, ?, ?, ?)""",
               [token, key(order_id), user_id, slug, file_name,
                datetime.now() + timedelta(days=boutique.DOWNLOAD_DAYS), boutique.DOWNLOAD_MAX])
    return token


def links(order_id):
    """Dernier lien de chaque fichier de la commande, avec son état (valable ou à renouveler)."""
    rows = db.fetch_all("SELECT * FROM shop_downloads WHERE order_id = ? ORDER BY created_at DESC NULLS LAST", [key(order_id)])
    latest = {}
    for r in rows:
        latest.setdefault(r["file_name"], r)
    now = datetime.now()
    out = []
    for r in latest.values():
        expires = r["expires_at"] if isinstance(r["expires_at"], datetime) else datetime.fromisoformat(str(r["expires_at"]))
        out.append({**r, "valid": expires > now and int(r["downloads"] or 0) < int(r["max_downloads"] or 0)})
    return sorted(out, key=lambda r: r["file_name"])


def renew_links(order_id, user_id):
    """Nouveau lien pour chaque fichier dont le lien a expiré ou est épuisé (commande payée seulement)."""
    for r in links(order_id):
        if not r["valid"]:
            _new_link(order_id, user_id, r["product_slug"], r["file_name"])
    return links(order_id)


def use_link(token):
    """Compte un téléchargement si le lien est valable, et renvoie sa ligne ; sinon None."""
    row = db.fetch("""UPDATE shop_downloads SET downloads = downloads + 1
                      WHERE token = ? AND expires_at > NOW() AND downloads < max_downloads
                      RETURNING *""", [token])
    return row
