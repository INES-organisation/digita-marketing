"""Chatbot IA (ChatbotController.php)."""
import logging

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import db, php, security
from ..services import agents, ai, ines

log = logging.getLogger("digita.chatbot")

SLOTS = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30",
         "15:00", "15:30", "16:00", "16:30", "17:00"]


def _json(payload):
    return Response(php.json_encode(payload), media_type="application/json")


async def send_message(request):
    form = await request.form()
    user_message = php.trim(form.get("message", ""))
    session_id = form.get("session_id") if "session_id" in form else security.session_id(request)
    page = php.trim(form.get("page", ""))
    if php.empty(user_message):
        return _json({"success": False, "error": "Message vide"})
    user_id = request.session.get("user_id")
    ip = security.remote_addr(request)
    return _json(await run_in_threadpool(_send_message, user_message, session_id, page, user_id, ip))


def _send_message(user_message, session_id, page, user_id, ip):
    try:
        conv = db.fetch("SELECT * FROM chatbot_conversations WHERE session_id = ? "
                        "ORDER BY created_at DESC, id DESC LIMIT 1", [session_id])
        if not conv:
            conv_id = str(db.fetch(
                "INSERT INTO chatbot_conversations (session_id, user_id, visitor_ip, visitor_page) "
                "VALUES (?, ?, ?, ?) RETURNING id", [session_id, user_id, ip, page])["id"])  # lastInsertId() : chaîne
        else:
            conv_id = conv["id"]
        db.execute("INSERT INTO chatbot_messages (conversation_id, role, content) VALUES (?, 'user', ?)",
                   [conv_id, user_message])
        history = db.fetch_all("SELECT role, content FROM chatbot_messages WHERE conversation_id = ? "
                               "ORDER BY created_at DESC, id DESC LIMIT 10", [conv_id])
        history.reverse()
        brief = agents.get_context(session_id, user_id)
        res = agents.process_request(user_message, history, brief)
        reply = res["response"]
        db.execute("INSERT INTO chatbot_messages (conversation_id, role, content) VALUES (?, 'assistant', ?)",
                   [conv_id, reply])
        db.execute("UPDATE chatbot_conversations SET updated_at = NOW() WHERE id = ?", [conv_id])
        # Le PHP teste ici une variable jamais définie ($msgCount) : l'extraction du brief
        # n'a donc jamais lieu. Comportement conservé.
        return {"success": True, "reply": reply, "agent": res["agent"],
                "intent": res["intent"] if res.get("intent") is not None else "info",
                "conversation_id": conv_id}
    except Exception as e:  # noqa: BLE001 — catch (Exception) PHP : réponse de secours
        log.warning("Chatbot sans IA : %s", e)
        return {"success": True, "reply": fallback_reply(user_message), "fallback": True}


def history(request):
    session_id = request.query_params.get("session_id") if "session_id" in request.query_params \
        else security.session_id(request)
    conv = db.fetch("SELECT * FROM chatbot_conversations WHERE session_id = ? "
                    "ORDER BY created_at DESC, id DESC LIMIT 1", [session_id])
    if not conv:
        return _json({"success": True, "messages": []})
    messages = db.fetch_all("SELECT role, content, created_at FROM chatbot_messages WHERE conversation_id = ? "
                            "ORDER BY created_at ASC, id ASC", [conv["id"]])
    return _json({"success": True, "messages": messages})


async def qualify(request):
    form = await request.form()
    conv_id = php.intval(form.get("conversation_id", 0))
    if not conv_id:
        return _json({"success": False, "error": "ID conversation manquant"})
    await run_in_threadpool(_try_qualify_lead, conv_id)
    return _json({"success": True})


def _try_qualify_lead(conv_id):
    messages = db.fetch_all("SELECT role, content FROM chatbot_messages WHERE conversation_id = ? "
                            "ORDER BY created_at ASC, id ASC", [conv_id])
    text = "".join(("Visiteur" if m["role"] == "user" else "Assistant") + ": " + m["content"] + "\n"
                   for m in messages)
    try:
        info = ai.extract_contact_info(text)
        if isinstance(info, list):
            info = dict(enumerate(info))
        if php.empty(info.get("email")) and php.empty(info.get("phone")) and php.empty(info.get("name")):
            return
        score = ai.calculate_lead_score(info)
        values = [info.get(k) for k in ("name", "email", "phone", "company", "project_type", "budget")]
        values.append(info.get("urgency") if info.get("urgency") is not None else "medium")
        values.append(score)
        existing = db.fetch("SELECT id FROM lead_qualifications WHERE conversation_id = ?", [conv_id])
        if existing:
            db.execute("UPDATE lead_qualifications SET name = ?, email = ?, phone = ?, company = ?, project_type = ?, "
                       "budget = ?, urgency = ?, score = ? WHERE id = ?", values + [existing["id"]])
        else:
            db.execute("INSERT INTO lead_qualifications (conversation_id, name, email, phone, company, project_type, "
                       "budget, urgency, score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [conv_id] + values)
        db.execute("UPDATE chatbot_conversations SET is_qualified = 1 WHERE id = ?", [conv_id])
    except Exception as e:  # noqa: BLE001
        log.error("Qualification lead échouée: %s", e)


async def appointment(request):
    form = await request.form()
    name = php.trim(form.get("name", ""))
    mail = php.trim(form.get("email", ""))
    phone = php.trim(form.get("phone", ""))
    date = form.get("date", "")
    slot = form.get("time_slot", "")
    subject = php.trim(form.get("subject", ""))
    if php.empty(name) or php.empty(mail) or php.empty(date) or php.empty(slot):
        return _json({"success": False, "error": "Champs obligatoires manquants (nom, email, date, créneau)"})
    if not security.valid_email(mail):
        return _json({"success": False, "error": "Email invalide"})
    user_id = request.session.get("user_id")
    return await run_in_threadpool(_book, name, mail, phone, date, slot, subject, user_id)


def _book(name, mail, phone, date, slot, subject, user_id):
    # Une date invalide fait échouer la requête comme en MySQL strict (erreur PHP non interceptée).
    existing = db.fetch("SELECT id FROM appointments WHERE date = ? AND time_slot = ? AND status != 'cancelled'",
                        [date, slot])
    if existing:
        return _json({"success": False, "error": "Ce créneau est déjà pris. Veuillez en choisir un autre."})
    db.execute("INSERT INTO appointments (name, email, phone, date, time_slot, subject, user_id) "
               "VALUES (?, ?, ?, ?, ?, ?, ?)", [name, mail, phone, date, slot, subject, user_id])
    ines.push_lead(name, mail, "rendez-vous", f"Rendez-vous le {date} à {slot} : {subject or ''}", phone)
    return _json({"success": True,
                  "message": "Rendez-vous confirmé le " + php.date("d/m/Y", php.strtotime(date)) + " à " + slot})


def slots(request):
    date = request.query_params.get("date") if "date" in request.query_params \
        else php.date("Y-m-d", php.strtotime("+1 day"))
    booked = {r["time_slot"] for r in db.fetch_all(
        "SELECT time_slot FROM appointments WHERE date = ? AND status != 'cancelled'", [date])}
    return _json({"success": True, "date": date, "slots": [s for s in SLOTS if s not in booked]})


def fallback_reply(message):
    m = message.lower()

    def has(*words):
        return any(w in m for w in words)

    if has("prix", "tarif", "coût"):
        return "Nos tarifs dépendent de votre projet. Pour un devis personnalisé gratuit, rendez-vous sur notre page /projets/brief ou contactez-nous via /contact."
    if has("formation", "cours"):
        return "Nous proposons des formations certifiantes en marketing digital ! Découvrez notre catalogue sur /formations."
    if has("seo", "référencement"):
        return "Le SEO est notre spécialité ! Testez notre audit SEO gratuit sur /outils/audit-seo pour analyser votre site."
    if has("site", "web"):
        return "Nous créons des sites web professionnels adaptés à vos besoins. Décrivez votre projet sur /projets/brief pour recevoir un devis."
    if has("rdv", "rendez-vous", "rencontrer"):
        return "Avec plaisir ! Contactez-nous via /contact pour planifier un rendez-vous avec notre équipe."
    if has("bonjour", "salut", "hello"):
        return "Bonjour ! Bienvenue chez Digita Marketing. Comment puis-je vous aider aujourd'hui ? 😊"
    return "Merci pour votre message ! Pour une réponse personnalisée, n'hésitez pas à nous contacter via /contact ou à décrire votre projet sur /projets/brief. Un conseiller vous répondra rapidement."
