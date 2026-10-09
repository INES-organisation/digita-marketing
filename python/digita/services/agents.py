"""AgentOrchestrator.php et ContextManager.php : agents spécialisés et brief client."""
from .. import db, php
from . import ai

AGENTS = {
    "strategic": {
        "name": "Consultant Stratégique Senior",
        "prompt": "Tu es le Consultant Stratégique Senior de DIGITA. Ton focus est le ROI et la croissance business. Analyse les enjeux financiers, les cibles de marché et propose des solutions de haute volée (Automatisation, Tunnels de vente complexes). Ton ton est direct, expert et tourné vers les résultats.",
    },
    "seo": {
        "name": "Architecte SEO & Performance",
        "prompt": "Tu es l'Architecte SEO de DIGITA. Tu vois le web comme une structure de données. Ton rôle est de maximiser l'autorité et la visibilité. Tu parles de sémantique, de maillage, de Core Web Vitals et de domination de SERP. Ton ton est technique mais pédagogue pour un décideur.",
    },
    "creative": {
        "name": "Directeur de Création & Brand Content",
        "prompt": "Tu es le Directeur de Création de DIGITA. Ton focus est l'émotion et l'image de marque. Tu transformes des services en expériences. Tu parles de 'Tone of Voice', de psychologie du design et de rétention par le contenu. Ton ton est inspirant, élégant et premium.",
    },
}

AGENT_FOR_INTENT = {
    "seo": "seo", "site_web": "seo", "audit": "seo",
    "strategie": "strategic", "devis": "strategic", "prix": "strategic", "business": "strategic",
    "contenu": "creative", "image": "creative", "branding": "creative", "video": "creative",
}


def process_request(user_message, history, client_brief):
    intent = _route_intention(user_message, history)
    key = AGENT_FOR_INTENT.get(intent, "strategic")
    agent = AGENTS[key]
    return {
        "agent": agent["name"],
        "agent_key": key,
        "response": ai.chat(history, _build_full_prompt(agent, client_brief)),
        "intent": intent,
    }


def _route_intention(message, history):
    history_text = ""
    for m in history[-3:]:
        history_text += php.strval(m.get("role") or "user") + ": " + php.strval(m.get("content") or "") + "\n"
    prompt = "Analyse le message de l'utilisateur et détermine l'expertise DIGITA requise.\n"
    prompt += f"Contexte historique :\n{history_text}\n"
    prompt += f"Message : {message}\n\n"
    prompt += "Réponds UNIQUEMENT par un mot-clé : seo, strategie, contenu, site_web, devis, branding, autre."
    return php.trim(ai.chat([], prompt)).lower()


def _build_full_prompt(agent, brief):
    prompt = f"IDENTITÉ : {agent['prompt']}\n\n"
    prompt += "CONTEXTE CLIENT ACTUEL :\n"
    if not brief:
        prompt += "- Aucun brief établi. Ton objectif est de poser 1 question stratégique pour mieux comprendre leur business.\n"
    else:
        for k, v in brief.items():
            if php.t(v):
                prompt += f"- {k} : {php.strval(v)}\n"
    prompt += "\nDIRECTIVES :\n"
    prompt += "1. Reste dans ton rôle d'expert.\n"
    prompt += "2. Sois proactif : si une info manque pour faire un devis, demande-la avec élégance.\n"
    prompt += "3. Ton de voix : Premium, Cabinet de Conseil, Professionnel, Rassurant.\n"
    prompt += "4. Si l'utilisateur semble prêt, propose un rendez-vous (/contact).\n"
    return prompt


# ---------------------------------------------------------------- ContextManager
def get_context(session_id, user_id=None):
    sql, params = "SELECT * FROM client_context WHERE session_id = ?", [session_id]
    if php.t(user_id):
        sql += " OR user_id = ?"
        params.append(user_id)
    sql += " ORDER BY updated_at DESC NULLS LAST, id DESC LIMIT 1"
    return db.fetch(sql, params) or {}


def calculate_maturity_score(context, projects=()):
    score = 0.0
    fields = ["business_sector", "business_goals", "target_audience", "estimated_budget",
              "current_pain_points", "competitors"]
    for f in fields:
        if not php.empty(context.get(f)):
            score += 50 / len(fields)
    if projects:
        score += 10
        if any(p["status"] == "completed" for p in projects):
            score += 20
    if context.get("lead_score") is not None:
        score += php.floatval(context["lead_score"]) / 100 * 20
    return min(php.php_round(score), 100)
