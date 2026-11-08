"""Pont vers INES : leads vers son CRM, IA via sa passerelle, e-mails via son fournisseur d'envoi
(même réseau Docker que ines-backend).

Sans INES_API_KEY, rien n'est envoyé : le site garde son comportement d'origine (base locale seule)."""
import logging
import os
import threading
import time

import httpx

log = logging.getLogger("digita.ines")


def _url(path):
    return os.getenv("INES_API_URL", "http://ines-backend:8000").rstrip("/") + path


def _headers():
    return {"Authorization": "Bearer " + os.getenv("INES_API_KEY", "")}


def enabled():
    return bool(os.getenv("INES_API_KEY"))


def push_lead(name, email, source, notes="", phone=None, outreach=None, outreach_email=True, tags=()):
    """Copie un lead dans INES, en arrière-plan : la base locale reste la référence et une panne
    d'INES ne bloque jamais le formulaire.

    Avec `outreach` (True/False), le lead passe par l'agent d'acquisition 24/7 d'INES
    (/external/acquisition/leads) : contact + affaire + alerte du propriétaire, et premier contact du
    prospect si outreach=True (par SMS seulement si outreach_email=False, le site ayant déjà écrit).
    Sans `outreach`, ou si l'agent est désactivé : simple fiche CRM (/contacts/ingest).

    Tags de la fiche : « DIGITA.buzz » (site d'origine), « form:<source> » (formulaire), puis `tags`
    (expertise choisie, « spam? »…), pour trier les prospects dans le CRM."""
    if not enabled() or not (email or phone):  # un téléphone seul suffit (prospect du chatbot)
        return
    payload = {"name": name or email or phone, "email": email or None, "phone": phone or None, "category": "Lead DIGITA",
               "tags": ["DIGITA.buzz", f"form:{source}", *tags], "notes": notes or None}
    if outreach is None:
        threading.Thread(target=_post_lead, args=(payload,), daemon=True).start()
        return
    web = {"name": name or "", "email": email or None, "phone": phone or None, "message": notes or "",
           "source": f"digita.buzz — {source}", "outreach": bool(outreach), "outreach_email": bool(outreach_email),
           "tags": payload["tags"]}
    threading.Thread(target=_post_web_lead, args=(web, payload), daemon=True).start()


def _post_web_lead(web, fallback, delays=(0, 5, 30)):
    for attempt, delay in enumerate(delays, 1):
        time.sleep(delay)
        try:
            r = httpx.post(_url("/api/v1/external/acquisition/leads"), json=web, headers=_headers(), timeout=30)
            r.raise_for_status()
            if r.json().get("status") != "disabled":
                return True
            break  # agent désactivé dans INES : fiche CRM simple
        except httpx.HTTPError as e:
            log.warning("Lead non transmis à l'agent INES (%s, essai %d) : %s", fallback["tags"][1], attempt, e)
    return _post_lead(fallback, delays=(0,))


def _post_lead(payload, delays=(0, 5, 30)):
    # Un lead perdu ne se rattrape pas (cas réel du 21/10/2026) : trois tentatives espacées, puis
    # une erreur dans le journal avec l'e-mail du prospect pour le reprendre à la main.
    for attempt, delay in enumerate(delays, 1):
        time.sleep(delay)
        try:
            httpx.post(_url("/api/v1/contacts/ingest"), json=payload, headers=_headers(), timeout=10).raise_for_status()
            return True
        except httpx.HTTPError as e:
            log.warning("Lead non transmis à INES (%s, essai %d) : %s", payload["tags"][1], attempt, e)
    log.error("Lead PERDU pour le CRM INES : %s <%s> (%s)", payload["name"], payload["email"], payload["tags"][1])
    return False


def generate(messages, system=None, temperature=0.7, max_tokens=500):
    """Texte généré par la passerelle IA d'INES (POST /api/v1/generate). Lève httpx.HTTPError."""
    body = {"messages": messages, "system": system, "temperature": temperature, "max_tokens": max_tokens,
            # Le cache INES ne regarde que `prompt` : sans no_cache deux conversations différentes
            # recevraient la même réponse.
            "no_cache": True}
    if os.getenv("INES_AI_MODEL"):
        body["model"] = os.getenv("INES_AI_MODEL")
    r = httpx.post(_url("/api/v1/generate"), json=body, headers=_headers(), timeout=60)
    r.raise_for_status()
    return r.json().get("text") or ""


def send_email(to, subject, html, from_name, from_address=None, template=None):
    """E-mail envoyé par le fournisseur d'INES (POST /api/v1/emails/transactional). Renvoie False sur échec.
    Visible dans INES (Communications › Journal) sous « digita/<template> »."""
    body = {"to": to, "subject": subject, "html": html, "from_name": from_name, "from_address": from_address,
            "site": "digita", "template": template}
    try:
        httpx.post(_url("/api/v1/emails/transactional"), json=body, headers=_headers(), timeout=30).raise_for_status()
        return True
    except httpx.HTTPError as e:
        log.error("E-mail non envoyé par INES à %s : %s", to, e)
        return False


# ---------------------------------------------------------------- rendez-vous (INES Booking)
# Le type de rendez-vous se règle dans INES (/booking) : jours, heures, durée, dates bloquées.
def booking_slug():
    return os.getenv("INES_BOOKING_SLUG", "appel-strat-gique")


def booking_availability(year, month):
    """{"event": {...}, "availability": {"2026-10-28": ["09:00", …]}} — créneaux libres du mois.
    Lève httpx.HTTPError si INES ne répond pas."""
    r = httpx.get(_url(f"/api/v1/booking/public/{booking_slug()}/availability"),
                  params={"year": year, "month": month}, timeout=10)
    r.raise_for_status()
    return r.json()


def book_slot(event_type_id, start_at, name, email, notes=""):
    """Réserve le créneau dans INES (heure locale de La Réunion, ISO sans fuseau). Renvoie la
    réservation (avec cancel_token) ; None si le créneau vient d'être pris (409)."""
    r = httpx.post(_url("/api/v1/booking/slots"), json={
        "event_type_id": event_type_id, "invitee_name": name, "invitee_email": email,
        "invitee_notes": notes or None, "start_at": start_at}, timeout=10)
    if r.status_code == 409:
        return None
    r.raise_for_status()
    return r.json()


def cancel_slot(cancel_token):
    r = httpx.post(_url(f"/api/v1/booking/slots/{cancel_token}/cancel"), timeout=10)
    if r.status_code == 404:
        return False
    r.raise_for_status()
    return True



# ---------------------------------------------------------------- ventes → livre des recettes INES
def sale_payload(invoice):
    """Vente payée sur digita.buzz, au format de POST /api/v1/external/sales (livre des recettes INES)."""
    import json

    snap = json.loads(invoice["snapshot"]) if invoice.get("snapshot") else {}
    buyer = snap.get("buyer", {})
    lines = [{"label": i.get("product_name") or "Vente", "quantity": int(i.get("quantity") or 1),
              "unit_price": float(i.get("price") or 0),
              # micro-entreprise : « ventes » = marchandises ; formations en ligne, contenus numériques et
              # installations sont des prestations de services (plafond et taux URSSAF des prestations)
              "nature": "prestation"} for i in snap.get("items", [])]
    total = round(float(invoice["amount_ttc"]), 2)
    gross = round(sum(l["quantity"] * l["unit_price"] for l in lines), 2)
    if lines and gross and gross != total:
        # Code promo : INES exige que les lignes reconstituent le total encaissé ; la remise est
        # répartie sur les lignes (le dernier centime d'arrondi va sur la dernière ligne).
        for l in lines:
            l["unit_price"] = round(l["unit_price"] * total / gross, 2)
        diff = round(total - sum(l["quantity"] * l["unit_price"] for l in lines), 2)
        lines[-1]["unit_price"] = round(lines[-1]["unit_price"] + diff / lines[-1]["quantity"], 2)
    elif not lines:
        lines = [{"label": "Vente en ligne", "quantity": 1, "unit_price": total, "nature": "prestation"}]
    return {"external_id": f"digita-invoice-{invoice['id']}", "kind": "sale",
            # heure du serveur (UTC) : INES exige une date avec fuseau
            "date": str(invoice.get("paid_at") or invoice.get("created_at")).replace(" ", "T") + "+00:00",
            "invoice_number": invoice["invoice_number"],
            "customer": {"name": buyer.get("name") or invoice.get("billing_name") or invoice.get("billing_email"),
                         "email": buyer.get("email") or invoice.get("billing_email"),
                         "address": buyer.get("address"), "siren": buyer.get("siret")},
            "lines": lines, "total": total, "currency": "EUR",
            "payment_method": "carte bancaire (Stripe)", "refund_of": None}


def push_sale(invoice):
    """Enregistre la vente dans INES. Renvoie True si INES l'a (créée ou déjà connue) ; sinon elle sera
    renvoyée par le rattrapage nocturne (automation.reconcile_pending_orders)."""
    if not enabled():
        return False
    try:
        r = httpx.post(_url("/api/v1/external/sales"), json=sale_payload(invoice), headers=_headers(), timeout=20)
        if r.status_code == 200 and r.json().get("status") in ("created", "exists"):
            return True
        log.warning("Vente %s non enregistrée dans INES : HTTP %s %s", invoice.get("invoice_number"), r.status_code, r.text[:200])
    except (httpx.HTTPError, ValueError) as e:
        log.warning("Vente %s non enregistrée dans INES : %s", invoice.get("invoice_number"), e)
    return False
