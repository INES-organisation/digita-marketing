"""Rendez-vous du diagnostic dans INES Booking, chatbot relié au CRM INES, outils IA, packs Solutions."""
import datetime
import threading

import pytest
from starlette.testclient import TestClient

from digita import booking, db, sessions
from digita.main import app
from digita.routes import chatbot, leads
from digita.services import ai, email, ines

EVENT = {"id": "evt-1", "slug": "appel-strat-gique"}


@pytest.fixture(autouse=True)
def memory_sessions(monkeypatch):
    store = {}
    monkeypatch.setattr(sessions, "_load", lambda sid: store.get(sid))
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: store.__setitem__(sid, data))


@pytest.fixture
def ines_booking(monkeypatch):
    """INES Booking simulé : créneaux de mardi prochain 9 h-10 h, réservations enregistrées."""
    calls = {"booked": [], "leads": [], "mails": [], "saved": []}
    monkeypatch.setattr(booking, "now", lambda: datetime.datetime(2026, 10, 25, 12, 0))
    monkeypatch.setattr(ines, "booking_availability", lambda y, m: {
        "event": EVENT, "availability": {"2026-10-25": ["13:00"], "2026-10-27": ["09:00", "09:30"]} if m == 10 else {}})

    def book_slot(event_id, start_at, name, mail, notes=""):
        calls["booked"].append((event_id, start_at, name, notes))
        return {"id": "slot-1", "cancel_token": "tok"}
    monkeypatch.setattr(ines, "book_slot", book_slot)
    monkeypatch.setattr(ines, "push_lead", lambda *a: calls["leads"].append(a))
    monkeypatch.setattr(email, "send_booking_confirmation", lambda *a: calls["mails"].append(a))
    monkeypatch.setattr(email, "send_new_contact_notification", lambda *a: True)
    monkeypatch.setattr(db, "execute", lambda sql, p=None: calls["saved"].append(p))
    return calls


def test_slots_come_from_ines_without_past_ones(ines_booking):
    days = TestClient(app).get("/api/booking/slots").json()["days"]
    # 13 h aujourd'hui est à moins de 2 h : retiré
    assert days == [{"date": "2026-10-27", "label": "Mardi 27 octobre", "slots": ["09:00", "09:30"]}]


def test_diagnostic_form_books_the_slot_in_ines(ines_booking):
    c = TestClient(app)
    form = {"name": "Ana", "email": "ana@example.com", "date": "2026-10-27", "time_slot": "09:30"}
    assert c.post("/api/audit-request", data=form).json()["success"] is False  # téléphone requis
    r = c.post("/api/audit-request", data={**form, "phone": "0692123456", "pack": "Devis et relances automatiques"}).json()
    assert r["success"] and r["booked"] and "mardi 27 octobre à 9 h 30" in r["message"]
    assert ines_booking["booked"][0][:3] == ("evt-1", "2026-10-27T09:30:00", "Ana")
    assert "Pack : Devis et relances automatiques" in ines_booking["booked"][0][3]
    assert ines_booking["mails"][0][3].endswith("/rendez-vous/annuler?token=tok")
    assert ines_booking["leads"][0][2] == "rendez-vous" and ines_booking["leads"][0][4] == "0692123456"

    taken = c.post("/api/audit-request", data={**form, "phone": "0692123456", "time_slot": "11:00"}).json()
    assert taken["success"] is False and "plus disponible" in taken["message"]


def test_chatbot_books_in_ines(ines_booking):
    c = TestClient(app)
    assert c.get("/api/chatbot/slots").json()["slots"] == ["09:00", "09:30"]
    r = c.post("/api/chatbot/appointment", data={"name": "Ana", "email": "ana@example.com", "phone": "0692123456",
                                                 "date": "2026-10-27", "time_slot": "09:00"}).json()
    assert r["success"] and ines_booking["booked"][0][1] == "2026-10-27T09:00:00"


def test_cancel_link_needs_a_click(monkeypatch):
    cancelled = []
    monkeypatch.setattr(ines, "cancel_slot", lambda token: cancelled.append(token) or True)
    c = TestClient(app, base_url="https://digita.buzz")
    page = c.get("/rendez-vous/annuler?token=tok").text
    assert cancelled == [] and "Oui, annuler" in page  # un aperçu du lien n'annule rien
    import re
    token = re.search(r'name="_csrf_token" value="([^"]+)"', page).group(1)
    r = c.post("/rendez-vous/annuler", data={"_csrf_token": token, "token": "tok"})
    assert cancelled == ["tok"] and "Rendez-vous annulé" in r.text


def test_chatbot_contact_details_reach_ines_crm(monkeypatch):
    leads_sent = []
    monkeypatch.setattr(chatbot, "_try_qualify_lead", lambda conv_id: None)  # IA indisponible
    monkeypatch.setattr(chatbot.db, "fetch_all", lambda sql, p=None: [{"role": "user", "content": "Rappelez-moi au 0692 12 34 56"}])
    monkeypatch.setattr(ines, "push_lead", lambda *a: leads_sent.append(a))
    chatbot._capture_lead(7, "Rappelez-moi au 0692 12 34 56")
    assert leads_sent[0][1] is None and leads_sent[0][2] == "chatbot" and leads_sent[0][4] == "0692 12 34 56"
    assert chatbot.CONTACT_RX.search("mon mail : ana@example.com") and not chatbot.CONTACT_RX.search("bonjour")


def test_meta_generator_keeps_only_the_description():
    raw = ("# Meta Description SEO Optimisée\n```\nAgence web La Réunion : création de sites internet vitrines pour "
           "artisans et petits commerces. Demandez votre devis gratuit.\n```\n**Caractères : 158/160** ✓\n"
           "**Points forts :**\n- ✅ Contient les mots-clés")
    meta = ai.clean_meta(raw)
    assert meta.startswith("Agence web La Réunion") and meta.endswith("devis gratuit.") and len(meta) <= 160


def test_editorial_calendar_starts_tomorrow(monkeypatch):
    prompts = []
    monkeypatch.setattr(ai, "chat", lambda messages, system=None: prompts.append(messages[0]["content"]) or
                        'Voici : [{"date": "2026-10-28", "title": "B", "keyword": "k", "type": "guide", "summary": "s"},'
                        ' {"date": "2026-10-26", "title": "A", "keyword": "k", "type": "liste", "summary": "s"}]')
    items = ai.generate_editorial_calendar("piscines", "2 semaines", "1 par semaine", datetime.date(2026, 10, 25))
    assert [i["title"] for i in items] == ["A", "B"] and "2 articles" in prompts[0] and "du 2026-10-26" in prompts[0]


def test_solutions_page_lists_turnkey_packs():
    from digita import solutions
    html = TestClient(app).get("/solutions").text
    for pack in solutions.PACKS:
        assert pack["title"] in html and f'/diagnostic?pack={pack["id"]}#consultant' in html
    assert "Prix du pack établi après le diagnostic gratuit" in html
    diag = TestClient(app).get("/diagnostic?pack=devis").text
    assert 'name="pack" value="Devis et relances automatiques"' in diag
