"""Réalisations affichées sur l'accueil (section « Réalisations »).

Chaque catégorie présente ce que nous savons réaliser (offre, tarif indicatif, délai,
prestations) puis, dans « items », les pages à voir en ligne : uniquement des pages réelles,
avec title, description, url et tag (le prix). Une catégorie sans page n'affiche pas le bloc.
Les prix des offres en commun avec /solutions viennent de solutions.py, jamais recopiés ici.
"""
from .solutions import LANCEMENT, LANDING, LP48, OFFERS

STANDARDISTE = OFFERS[0]
AGENT_PRICE = STANDARDISTE["monthly"].split(" à ")[0] + "/mois"  # « 149 €/mois »
AGENT_URL = "https://agent24-7.digita.buzz"

REALISATIONS = [
    {
        "id": "sites-web",
        "title": "Sites web et landing",
        "icon": "bi-window-desktop",
        "color": "#D4AF37",
        "tagline": "Des sites qui font sonner le téléphone.",
        "description": "Offre 974 : on crée, on héberge et on maintient votre site vitrine. "
                       "Vous payez votre identité visuelle une fois, puis une petite maintenance.",
        "price": f"Dès {LANDING['price']}",
        "price_note": f"{LANDING['title']} : {LANDING['scope']}. Site vitrine : 990 € d'identité visuelle (logo, "
                      "charte, photos, textes), 690 € si vous avez déjà un logo ; site et hébergement inclus, "
                      "puis maintenance 49 €/mois (engagement 12 mois)",
        "delay": "5 jours ouvrés à 4 semaines",
        "capabilities": [
            "Site vitrine sur mesure, rapide et compatible mobile",
            "Landing pages et pages de vente qui convertissent",
            "Référencement Google de base, Analytics et Search Console branchés",
            "Nom de domaine (1 an offert), SSL, formulaire de contact",
            "Vous possédez domaine, contenus et code : aucune prise d'otage",
        ],
        "items": [
            {
                "title": "LP48 : votre page de vente en 48h",
                "url": "https://lp48.digita.buzz",
                "description": "Page de vente clé en main : copywriting, design, formulaire ou paiement "
                               "et mise en ligne inclus, livrée en 48h ouvrées.",
                "tag": LP48["price"],
            },
        ],
    },
    {
        "id": "reseaux-sociaux",
        "title": "Réseaux sociaux",
        "icon": "bi-people",
        "color": "#60a5fa",
        "tagline": "Des publications régulières, sans y passer vos soirées.",
        "description": "On crée, on planifie, on publie et on répond aux commentaires. "
                       "Vous récoltez les clients.",
        "price": "Dès 390 €/mois",
        "price_note": "Essentiel : 1 réseau, 8 publications. Pro : 2 réseaux, 12 à 16 publications, 590 €/mois",
        "delay": "Engagement 3 mois minimum",
        "capabilities": [
            "Charte réseaux sociaux adaptée à votre métier",
            "8 à 16 publications par mois : visuels, vidéos courtes, textes",
            "Calendrier mensuel validé par vous en 10 minutes",
            "Messages et commentaires traités tous les jours",
            "Point mensuel de 30 minutes avec les chiffres clés",
        ],
        "items": [
            {
                "title": "Pack de lancement : logo et page Facebook",
                "url": "/solutions#lancement",
                "description": LANCEMENT["promise"].capitalize() + ".",
                "tag": LANCEMENT["price"],
            },
        ],
    },
    {
        "id": "publicite",
        "title": "Publicité",
        "icon": "bi-megaphone",
        "color": "#f97316",
        "tagline": "Payez pour des résultats, pas pour des promesses.",
        "description": "Campagnes Google, Facebook et Instagram pilotées pour que chaque euro "
                       "investi vous en rapporte plus.",
        "price": "290 €/mois",
        "price_note": "gestion pour un budget publicitaire jusqu'à 1 000 €/mois (300 à 500 € conseillés pour démarrer), "
                      "sans engagement au-delà d'un mois",
        "delay": "Résultats en 2 à 6 semaines",
        "capabilities": [
            "Objectif chiffré : appels, devis ou visites en boutique",
            "Création des publicités : visuels, textes, vidéos courtes",
            "Tests à petit budget, puis on amplifie ce qui marche",
            "Page d'atterrissage dédiée si vous n'avez pas de site",
            "Sans engagement long : si ça ne donne rien, on s'arrête",
        ],
        "items": [],
    },
    {
        "id": "automatisation",
        "title": "Automatisation",
        "icon": "bi-diagram-3",
        "color": "#34d399",
        "tagline": "Arrêtez de faire à la main ce que l'ordinateur peut faire.",
        "description": "Devis, factures, relances, rendez-vous, transferts entre logiciels : "
                       "on branche vos outils pour que tout se fasse tout seul.",
        "price": "490 €",
        "price_note": "par scénario simple (un outil vers un autre), payé une fois ; scénarios complexes sur devis "
                      "(outils : 10 à 30 €/mois)",
        "delay": "1 à 3 semaines",
        "capabilities": [
            "Gmail, Outlook, Google Sheets, agendas, CRM, WhatsApp Business",
            "Devis et factures (Pennylane, Sellsy…), e-commerce",
            "Scénarios n8n, Make ou Zapier, testés et documentés",
            "Applications métier et applis mobiles sur mesure",
        ],
        "items": [],
    },
    {
        "id": "agents-ia",
        "title": "Agents IA",
        "icon": "bi-robot",
        "color": "#a78bfa",
        "tagline": "Un assistant qui ne dort jamais, formé sur vos informations.",
        "description": "Il répond à vos clients, prend des rendez-vous, qualifie les demandes "
                       "et transmet à un humain quand il le faut.",
        "price": AGENT_PRICE,
        "price_note": f"{STANDARDISTE['title']} : mise en service {STANDARDISTE['setup']}, "
                      f"puis {STANDARDISTE['monthly']} ({STANDARDISTE['monthly_note']})",
        "delay": "2 à 4 semaines",
        "capabilities": [
            "Réponse immédiate 24h/24 sur Messenger, Instagram et au téléphone",
            "Entraîné sur vos services, vos tarifs et votre façon de parler",
            "Qualification des demandes et rendez-vous posés dans votre agenda",
            "Alerte par SMS et e-mail, fiche créée dans votre CRM",
            "Testé à huis clos avant la mise en ligne, conversations visibles",
            "Modèles européens (Mistral) ou sous contrat strict (Claude, OpenAI)",
        ],
        "items": [
            {
                "title": "INES : votre agent IA 24/7",
                "url": AGENT_URL,
                "description": "Elle répond à vos prospects jour et nuit, qualifie le projet et pose le "
                               "rendez-vous dans votre agenda. Testez-la en direct sur la page.",
                "tag": f"Dès {AGENT_PRICE}",
            },
        ],
    },
]
