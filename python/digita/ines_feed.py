"""Tarifs publiés pour INES (GET /api/catalogue) : digita.buzz fait foi, INES les relit chaque heure.

Tout vient de `services_catalog.py` et `solutions.py`. INES_NAMES relie un service du site aux
lignes du catalogue INES quand le nom diffère ; EXTRA et NEW couvrent ce qui n'est pas sur /services.
« Sur devis » vaut 0 : INES refuse alors la commande en ligne.
"""
import re

from . import services_catalog
from .solutions import LANCEMENT, LANDING, LP48

INES_NAMES = {
    ("ecommerce", "Création E-commerce"): ["Création & Optimisation E-commerce"],
    ("ecommerce", "Paiement"): ["Paiement & Logistique"],
    ("mobile", "Fonctionnalités"): ["Fonctionnalités App"],
    ("reseaux-sociaux", "Social Ads"): ["Social Ads (Publicité sur Réseaux Sociaux)"],
    ("reseaux-sociaux", "Création Contenu"): ["Création de Contenu Social Media"],
    ("identite-visuelle", "Identité de Marque"): ["Création d'Identité de Marque"],
    ("video-multimedia", "Contenu Vidéo Social"): ["Contenu Vidéo pour Réseaux Sociaux"],
    ("redaction", "Traduction"): ["Traduction & Localisation"],
    ("publicite", "Social Ads"): ["Social Ads (Publicité sur Réseaux Sociaux)"],
    ("publicite", "Display & Affiliation"): ["Publicité Display", "Affiliation"],
    ("email-marketing", "Automation"): ["Automation Marketing"],
    ("email-marketing", "Design Email"): ["Design & Développement Email"],
    ("ia-automation", "Chatbots"): ["Chatbots & Assistants Virtuels"],
    ("ia-automation", "Automation"): ["Automatisation Marketing"],
    ("strategie", "CRO & Growth"): ["Conversion & Optimisation", "Stratégie de Conversion (CRO)", "Growth Hacking"],
    ("formation", "Coaching"): ["Coaching & Consulting"],
}
EXTRA = {
    LP48["title"]: LP48["price"],
    "Maintenance Web": "49 €/mois",
    "Photographie Professionnelle": "290 €/demi-journée",
    "Gestion de Base de Données": "149 €",
}
# Lignes absentes d'INES : créées à la première lecture.
NEW = {
    LANDING["title"]: {"category": "Sites Web", "description": f"Page de vente : {LANDING['scope']}."},
    LANCEMENT["title"]: {"category": "Packs & Formules", "description": f"Inclut : {LANCEMENT['promise']}."},
}
UNITS = {"mois": "mois", "article": "article", "heure": "heure", "jour": "jour", "mot": "mot",
         "template": "template", "demi-journée": "demi-journee"}


def parse_price(price):
    """« 2 490 € » → (2490.0, "forfait") ; « 0,08 €/mot » → (0.08, "mot") ; « Sur devis » → (0.0, "forfait")."""
    match = re.match(r"([\d\s,]+)€(?:/(.+))?$", price.strip())
    if not match:
        return 0.0, "forfait"
    return float(re.sub(r"\s", "", match[1]).replace(",", ".")), UNITS[match[2]] if match[2] else "forfait"


def entries():
    prices = dict(EXTRA)
    prices[LANCEMENT["title"]] = LANCEMENT["price"]
    for category in services_catalog.categories():
        for service in category["services"]:
            for name in INES_NAMES.get((category["id"], service["name"]), [service["name"]]):
                prices[name] = service["price"]
    feed = []
    for name, price in prices.items():
        base_price, unit = parse_price(price)
        feed.append({"name": name, "base_price": base_price, "unit": unit, **NEW.get(name, {})})
    return feed
