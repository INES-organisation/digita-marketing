"""Rendez-vous « diagnostic de 30 min » : créneaux et réservations dans INES Booking.

INES est la source de vérité (jours, heures, durée, congés se règlent dans INES /booking ; une
réservation y apparaît aussitôt, et dans le Planning). Les heures sont celles de La Réunion,
sans fuseau, comme dans INES. La table locale `appointments` garde une copie pour l'admin Digita.
"""
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from . import config, db, php
from .services import email, ines

log = logging.getLogger("digita.booking")

TZ = ZoneInfo("Indian/Reunion")
MIN_NOTICE = timedelta(hours=2)   # pas de rendez-vous dans les deux prochaines heures
HORIZON_DAYS = 21                 # créneaux proposés sur trois semaines


def now():
    return datetime.now(TZ).replace(tzinfo=None)


def available_days(horizon=HORIZON_DAYS):
    """({"2026-10-27": ["09:00", …], …}, event_type_id) — créneaux libres à venir.
    Lève httpx.HTTPError si INES ne répond pas."""
    start = now() + MIN_NOTICE
    end = start + timedelta(days=horizon)
    days, event_id = {}, None
    month = date(start.year, start.month, 1)
    while month <= end.date():
        data = ines.booking_availability(month.year, month.month)
        event_id = data["event"]["id"]
        for day, slots in data.get("availability", {}).items():
            keep = [s for s in slots if start <= datetime.fromisoformat(f"{day}T{s}") <= end]
            if keep:
                days[day] = keep
        month = date(month.year + month.month // 12, month.month % 12 + 1, 1)
    return dict(sorted(days.items())), event_id


BOOKED, TAKEN, DOWN = "booked", "taken", "down"


def book(day, slot, name, mail, phone="", notes=""):
    """Réserve `day` à `slot` dans INES. Renvoie (statut, message) : BOOKED, TAKEN (créneau pris
    ou invalide, en choisir un autre) ou DOWN (INES injoignable, à traiter comme une demande de rappel)."""
    try:
        days, event_id = available_days()
    except httpx.HTTPError as e:
        log.error("INES Booking injoignable : %s", e)
        return DOWN, "La réservation en ligne est momentanément indisponible."
    if slot not in days.get(day, []):
        return TAKEN, "Ce créneau n'est plus disponible. Choisissez-en un autre."
    details = "\n".join(x for x in (f"Téléphone : {phone}" if phone else "", notes) if x)
    try:
        booking = ines.book_slot(event_id, f"{day}T{slot}:00", name, mail, details)
    except httpx.HTTPError as e:
        log.error("Réservation INES échouée : %s", e)
        return DOWN, "La réservation en ligne est momentanément indisponible."
    if booking is None:
        return TAKEN, "Ce créneau vient d'être pris. Choisissez-en un autre."

    try:
        db.execute("INSERT INTO appointments (name, email, phone, date, time_slot, subject, notes, status) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed')",
                   [name, mail, phone, day, slot, "Diagnostic 30 min", notes])
    except Exception as e:  # noqa: BLE001 — la réservation INES fait foi, la copie locale est secondaire
        log.warning("Copie locale du rendez-vous non enregistrée : %s", e)
    when = format_when(day, slot)
    ines.push_lead(name, mail, "rendez-vous", f"Diagnostic 30 min réservé le {when}\n{details}".strip(), phone or None)
    cancel_url = config.APP_URL.rstrip("/") + "/rendez-vous/annuler?token=" + booking["cancel_token"]
    email.send_booking_confirmation(mail, name, when, cancel_url)
    return BOOKED, f"Rendez-vous confirmé le {when}. Un e-mail de confirmation vous a été envoyé."


DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
          "octobre", "novembre", "décembre"]


def format_day(day):
    d = date.fromisoformat(day)
    return f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"


def format_when(day, slot):
    hour, minute = slot.split(":")
    return f"{format_day(day)} à {int(hour)} h" + ("" if minute == "00" else f" {minute}")


def days_for_display(days):
    """Liste prête pour les sélecteurs : [{"date", "label", "slots"}]."""
    return [{"date": d, "label": php.ucfirst(format_day(d)), "slots": s} for d, s in days.items()]
