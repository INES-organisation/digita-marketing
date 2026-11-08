"""Factures : numéro au paiement (série annuelle sans trou), facture figée, envoi au livre des recettes INES."""
import json

from digita.models import invoice as Invoice
from digita.services import ines


def test_invoice_number_comes_from_the_yearly_counter_in_one_statement(monkeypatch):
    calls = []
    monkeypatch.setattr(Invoice, "get_by_order_id", lambda oid: None)
    monkeypatch.setattr(Invoice.db, "fetch_all", lambda sql, p=None: [{"product_name": "Pack Commerce", "product_type": "pack",
                                                                       "quantity": 1, "price": "29.00"}])
    monkeypatch.setattr(Invoice.db, "fetch", lambda sql, p=None: calls.append((sql, p)) or {"id": 3, "invoice_number": "DM-2026-0007"})
    monkeypatch.setattr(Invoice.db, "execute", lambda sql, p=None: calls.append((sql, p)))
    order = {"id": 12, "user_id": 5, "amount": "29.00", "customer_email": "c@d.fr", "billing_name": "Marie Hoarau",
             "billing_address": "1 rue de Paris, 97400 Saint-Denis", "billing_company": None, "billing_siret": None}
    assert Invoice.create_from_order(order) == "3"
    sql, params = calls[0]
    # compteur et insertion dans la même instruction : pas de numéro consommé si l'insertion échoue
    assert "INSERT INTO invoice_counters" in sql and "INSERT INTO invoices" in sql and "lpad" in sql
    snapshot = json.loads(params[-1])
    assert snapshot["buyer"]["name"] == "Marie Hoarau" and snapshot["seller"]["siren"] == "844 384 198"
    assert calls[1] == ("UPDATE orders SET invoice_number = ? WHERE id = ?", ["DM-2026-0007", 12])


def test_sale_payload_for_ines_receipts_ledger():
    snap = {"buyer": {"name": "Marie Hoarau", "email": "c@d.fr", "address": "Saint-Denis", "siret": None},
            "items": [{"product_name": "Pack Commerce", "product_type": "pack", "quantity": 1, "price": "29.00"}]}
    inv = {"id": 3, "invoice_number": "DM-2026-0007", "paid_at": "2026-11-08 10:00:00", "amount_ttc": "29.00",
           "billing_email": "c@d.fr", "snapshot": json.dumps(snap)}
    p = ines.sale_payload(inv)
    assert p["external_id"] == "digita-invoice-3" and p["kind"] == "sale" and p["date"] == "2026-11-08T10:00:00+00:00"
    assert p["total"] == 29.0 and p["lines"][0]["nature"] == "prestation" and p["customer"]["name"] == "Marie Hoarau"


def test_sale_payload_spreads_a_promo_over_the_lines():
    snap = {"buyer": {"name": "A", "email": "a@b.fr"},
            "items": [{"product_name": "Formation", "product_type": "formation", "quantity": 1, "price": "97.00"}]}
    inv = {"id": 4, "invoice_number": "DM-2026-0008", "paid_at": "2026-11-08 10:00:00", "amount_ttc": "77.60",
           "billing_email": "a@b.fr", "snapshot": json.dumps(snap)}
    p = ines.sale_payload(inv)
    assert p["total"] == 77.6 and round(sum(l["quantity"] * l["unit_price"] for l in p["lines"]), 2) == 77.6
