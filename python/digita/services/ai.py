"""Service IA (équivalent de app/Services/AIService.php) : OpenAI, audit SEO, ROI."""
import ipaddress
import json
import math
import os
import re
import socket
import time
import urllib.parse

import httpx

from .. import php
from . import ines


class AIError(Exception):
    """Exception levée par sendRequest() en PHP (clé absente, réponse HTTP ≠ 200)."""


def _send_request(endpoint, data):
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise AIError("Clé API OpenAI non configurée")
    try:
        r = httpx.post(f"https://api.openai.com/v1/{endpoint}", content=php.json_encode(data),
                       headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
                       timeout=60)
    except httpx.HTTPError as e:
        raise AIError("Erreur API OpenAI: " + str(e)) from e
    if r.status_code != 200:
        raise AIError("Erreur API OpenAI: " + r.text)
    return r.json()


def chat(messages, system_prompt=None):
    chat_messages = []
    if php.t(system_prompt):
        chat_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        chat_messages.append({"role": m.get("role") or "user", "content": m["content"]})
    if ines.enabled():
        try:
            return ines.generate([m for m in chat_messages if m["role"] != "system"], system_prompt or None)
        except httpx.HTTPError as e:
            raise AIError("Erreur API INES: " + str(e)) from e
    resp = _send_request("chat/completions", {
        "model": os.getenv("OPENAI_MODEL", "gpt-4"),
        "messages": chat_messages,
        "temperature": 0.7,
        "max_tokens": 500,
    })
    try:
        content = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        content = None
    return "" if content is None else content


def generate_meta_description(page_title, page_content):
    prompt = "Génère une meta description SEO optimisée (max 160 caractères) pour cette page:\n\n"
    prompt += f"Titre: {page_title}\n"
    prompt += "Contenu: " + php.substr(page_content, 0, 500) + "...\n"
    prompt += "\nLa meta description doit être en français, attractive et contenir des mots-clés pertinents."
    return chat([{"content": prompt}])


def _json_array(text):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, (dict, list)) else {}


def extract_contact_info(conversation_text):
    prompt = "Extrais les informations de contact de cette conversation. "
    prompt += "Réponds UNIQUEMENT en JSON avec les clés : name, email, phone, company, project_type, budget, urgency (low/medium/high). "
    prompt += "Mets null pour les champs non trouvés.\n\n"
    prompt += f"Conversation :\n{conversation_text}"
    return _json_array(chat([{"content": prompt}]))


def calculate_lead_score(lead):
    score = 0
    for field, pts in (("email", 20), ("phone", 15), ("name", 10), ("company", 10),
                       ("project_type", 15), ("budget", 15)):
        if not php.empty(lead.get(field)):
            score += pts
    urgency = lead.get("urgency") if lead.get("urgency") is not None else ""
    score += 15 if urgency == "high" else 10 if urgency == "medium" else 5
    return min(score, 100)


def extract_business_context(conversation_text):
    prompt = "Analyse cette conversation de consulting digital. Extrais les informations business structurées suivantes au format JSON uniquement :\n"
    prompt += "{\n"
    prompt += "  \"business_sector\": \"Secteur d'activité (ex: Immobilier, E-commerce)\",\n"
    prompt += "  \"business_goals\": \"Objectifs principaux (ex: Acquisition, Notoriété, Automatisation)\",\n"
    prompt += "  \"target_audience\": \"Cible client (ex: B2B, Particuliers)\",\n"
    prompt += "  \"estimated_budget\": \"Budget évoqué ou estimé\",\n"
    prompt += "  \"current_pain_points\": \"Points de douleur ou obstacles actuels\",\n"
    prompt += "  \"competitors\": \"Concurrents mentionnés\",\n"
    prompt += "  \"preferred_expertise\": \"Expertise DIGITA la plus adaptée (strategic, seo, creative)\"\n"
    prompt += "}\n"
    prompt += "Si une information est manquante, mets null.\n\n"
    prompt += f"CONVERSATION :\n{conversation_text}"
    response = chat([{"content": prompt}], "Tu es un analyste business expert.")
    return _json_array(response.replace("```json", "").replace("```", "").strip())


def generate_editorial_calendar(niche, duration="1 mois", frequency="3 par semaine"):
    prompt = f"Génère un calendrier éditorial pour un blog dans la niche \"{niche}\".\n"
    prompt += f"Durée : {duration}\n"
    prompt += f"Fréquence : {frequency}\n\n"
    prompt += "Pour chaque article, donne :\n"
    prompt += "- Date de publication\n"
    prompt += "- Titre de l'article (optimisé SEO)\n"
    prompt += "- Mot-clé principal\n"
    prompt += "- Type de contenu (guide, liste, étude de cas, tutoriel, actualité)\n"
    prompt += "- Résumé en 1 phrase\n\n"
    prompt += "Réponds en format structuré, clair et actionnable."
    return chat([{"content": prompt}], None)


# ---------------------------------------------------------------- audit SEO
URL_RX = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[\x21-\x7e]+$")
HOST_RX = re.compile(r"^(?:[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?\.?$")


def valid_url(url):
    """Approximation de filter_var($url, FILTER_VALIDATE_URL)."""
    if not URL_RX.match(url or ""):
        return False
    p = urllib.parse.urlsplit(url)
    if p.scheme.lower() in ("http", "https"):
        host = p.hostname or ""
        if host.startswith("[") or ":" in host:
            return True
        return bool(host) and bool(HOST_RX.match(host))
    return True


def _public_host(host):
    """Refuse les adresses internes : sur le VPS le conteneur voit le réseau d'INES."""
    if os.getenv("DIGITA_AUDIT_ALLOW_PRIVATE") == "1":
        return True
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError):
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            return False
    return True


def _fetch(url):
    """curl avec FOLLOWLOCATION, timeout 15 s, sans vérification TLS. Renvoie (html, code, durée)."""
    start = time.monotonic()
    code = 0
    with httpx.Client(verify=False, timeout=15, headers={"User-Agent": "Digita-SEO-Audit/1.0"}) as c:
        for _ in range(20):
            p = urllib.parse.urlsplit(url)
            if p.scheme.lower() not in ("http", "https") or not p.hostname or not _public_host(p.hostname):
                return "", 0, time.monotonic() - start
            try:
                r = c.get(url, follow_redirects=False)
            except (httpx.HTTPError, ValueError):
                return "", 0, time.monotonic() - start
            code = r.status_code
            if r.is_redirect and "location" in r.headers:
                url = urllib.parse.urljoin(url, r.headers["location"])
                continue
            return r.content.decode("utf-8", errors="replace"), code, time.monotonic() - start
    return "", code, time.monotonic() - start


def audit_seo(url):
    result = {"url": url, "score": 0, "checks": [], "recommendations": []}
    html, http_code, load_time = _fetch(url)
    if not php.t(html) or http_code >= 400:
        result["error"] = "Impossible d'accéder à l'URL (HTTP " + str(http_code) + ")"
        return result

    checks, recs = result["checks"], result["recommendations"]
    points = 0
    max_points = 0

    def check(name, status, detail):
        checks.append({"name": name, "status": status, "detail": detail})

    # 1. Title
    max_points += 10
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = m.group(1) if m else ""
    if php.t(title):
        n = len(title)
        if 30 <= n <= 60:
            points += 10
            check("Balise Title", "good", f"{title} ({n} car.)")
        else:
            points += 5
            check("Balise Title", "warning", f"Longueur non optimale ({n} car., idéal 30-60)")
            recs.append("Ajustez la longueur du title entre 30 et 60 caractères.")
    else:
        check("Balise Title", "error", "Absente")
        recs.append("Ajoutez une balise <title> unique et descriptive.")

    # 2. Meta description
    max_points += 10
    m = re.search(r"<meta\s+name=[\"']description[\"']\s+content=[\"'](.*?)[\"']", html, re.S | re.I)
    meta_desc = m.group(1) if m else ""
    if php.t(meta_desc):
        n = len(meta_desc)
        if 120 <= n <= 160:
            points += 10
            check("Meta Description", "good", php.mb_strimwidth(meta_desc, 0, 80, "...") + f" ({n} car.)")
        else:
            points += 5
            check("Meta Description", "warning", f"Longueur non optimale ({n} car., idéal 120-160)")
            recs.append("Ajustez la meta description entre 120 et 160 caractères.")
    else:
        check("Meta Description", "error", "Absente")
        recs.append("Ajoutez une meta description unique et attractive.")

    # 3. H1
    max_points += 10
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    if len(h1) == 1:
        points += 10
        check("Balise H1", "good", php.strip_tags(h1[0]))
    elif len(h1) > 1:
        points += 5
        check("Balise H1", "warning", f"{len(h1)} balises H1 trouvées (1 seule recommandée)")
        recs.append("Utilisez une seule balise H1 par page.")
    else:
        check("Balise H1", "error", "Aucune balise H1")
        recs.append("Ajoutez une balise H1 unique contenant le mot-clé principal.")

    # 4. Images alt
    max_points += 10
    imgs = re.findall(r"<img[^>]*>", html, re.S | re.I)
    total_images = len(imgs)
    with_alt = sum(1 for i in imgs if re.search(r"alt=[\"'][^\"']+[\"']", i, re.I))
    if total_images == 0:
        points += 10
        check("Images Alt", "good", "Aucune image trouvée")
    elif with_alt == total_images:
        points += 10
        check("Images Alt", "good", f"{total_images}/{total_images} images avec alt")
    else:
        ratio = php.php_round(with_alt / total_images * 100)
        points += php.php_round(with_alt / total_images * 10)
        check("Images Alt", "warning" if ratio > 50 else "error",
              f"{with_alt}/{total_images} images avec alt ({php.strval(ratio)}%)")
        recs.append("Ajoutez des attributs alt descriptifs à toutes les images.")

    # 5. HTTPS
    max_points += 10
    if url.startswith("https://"):
        points += 10
        check("HTTPS", "good", "Connexion sécurisée")
    else:
        check("HTTPS", "error", "Site non sécurisé")
        recs.append("Migrez votre site vers HTTPS pour la sécurité et le SEO.")

    # 6. Temps de chargement
    max_points += 10
    lt = php.strval(php.php_round(load_time, 2))
    if load_time < 2:
        points += 10
        check("Temps de chargement", "good", lt + "s")
    elif load_time < 4:
        points += 5
        check("Temps de chargement", "warning", lt + "s (idéal < 2s)")
        recs.append("Optimisez le temps de chargement (compression, cache, images).")
    else:
        check("Temps de chargement", "error", lt + "s (trop lent)")
        recs.append("Votre site est trop lent. Optimisez les performances.")

    # 7. Viewport
    max_points += 10
    if re.search(r"<meta\s+name=[\"']viewport[\"']", html, re.I):
        points += 10
        check("Mobile (viewport)", "good", "Balise viewport présente")
    else:
        check("Mobile (viewport)", "error", "Balise viewport absente")
        recs.append("Ajoutez une balise meta viewport pour le responsive.")

    # 8. Open Graph
    max_points += 10
    if re.search(r"<meta\s+property=[\"']og:", html, re.I):
        points += 10
        check("Open Graph", "good", "Balises OG présentes")
    else:
        check("Open Graph", "warning", "Balises OG absentes")
        recs.append("Ajoutez des balises Open Graph pour un meilleur partage social.")

    # 9. Liens internes
    max_points += 10
    links = re.findall(r"<a\s+[^>]*href=[\"']([^\"']*)[\"'][^>]*>", html, re.I)
    domain = urllib.parse.urlsplit(url).hostname or ""
    internal = external = 0
    for link in links:
        # strpos($link, '') renvoie 0 en PHP 8 : sans domaine, tout lien compte comme interne.
        if link.startswith("/") or domain in link:
            internal += 1
        elif link.startswith("http"):
            external += 1
    if internal >= 3:
        points += 10
        check("Liens internes", "good", f"{internal} liens internes, {external} externes")
    elif internal > 0:
        points += 5
        check("Liens internes", "warning", f"{internal} liens internes (ajoutez-en plus)")
        recs.append("Ajoutez plus de liens internes pour améliorer le maillage.")
    else:
        check("Liens internes", "error", "Aucun lien interne")
        recs.append("Ajoutez des liens internes vers vos pages importantes.")

    # 10. Schema.org
    max_points += 10
    if re.search(r"application/ld\+json", html, re.I) or re.search(r"itemtype=[\"']https?://schema\.org", html, re.I):
        points += 10
        check("Schema.org", "good", "Données structurées détectées")
    else:
        check("Schema.org", "warning", "Aucune donnée structurée")
        recs.append("Ajoutez des données structurées Schema.org (JSON-LD).")

    result["score"] = php.php_round(points / max_points * 100) if max_points > 0 else 0
    result["title"] = title
    result["meta_description"] = meta_desc
    result["load_time"] = php.php_round(load_time, 2)
    result["images_count"] = total_images
    result["links_internal"] = internal
    result["links_external"] = external
    return result


# ---------------------------------------------------------------- ROI
def calculate_roi(params):
    budget = php.floatval(params.get("budget", 0))
    cpc = php.floatval(params.get("cpc", 1.5))
    conversion_rate = php.floatval(params.get("conversion_rate", 2)) / 100
    avg_order_value = php.floatval(params.get("avg_order_value", 100))
    margin = php.floatval(params.get("margin", 30)) / 100

    if budget <= 0 or cpc <= 0:
        return {"error": "Budget et CPC doivent être supérieurs à 0"}

    clicks = float(math.floor(budget / cpc))
    conversions = float(math.floor(clicks * conversion_rate))
    revenue = conversions * avg_order_value
    profit = revenue * margin
    roi = php.php_round((profit - budget) / budget * 100, 1)
    cpa = php.php_round(budget / conversions, 2) if conversions > 0 else 0
    return {
        "budget": budget, "clicks": clicks, "conversions": conversions,
        "revenue": php.php_round(revenue, 2), "profit": php.php_round(profit, 2),
        "roi": roi, "cpa": cpa, "roas": php.php_round(revenue / budget, 2),
    }
