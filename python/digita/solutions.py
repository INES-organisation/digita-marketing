"""Offres de la page /solutions (reprises par le chatbot et le formulaire de diagnostic).

OFFERS : les trois systèmes d'acquisition IA 24/7, construits sur l'agent d'acquisition d'INES
(Messenger, Instagram, Lead Ads, téléphone, SMS, site web → CRM, Planning, devis brouillons).
Prix HT fixés le 26/10/2026 (fourchette selon le paramétrage). Chaque ligne « includes » doit
correspondre à une fonction réelle d'INES (voir docs/SUIVI_CONNEXION_INES.md §6).

PACKS : autres packs clés en main, composés de services du catalogue (`services_catalog.py`) ;
prix des composants = prix d'entrée publics, prix du pack établi après le diagnostic tant que
« price » est vide.
"""

OFFERS = [
    {
        "id": "standardiste",
        "title": "Standardiste Messenger & Insta 24/7",
        "level": "Entrée de gamme",
        "icon": "bi-chat-dots-fill",
        "for": "Artisans, instituts de beauté, restaurants, commerces locaux, indépendants.",
        "promise": "répondre à chaque message Facebook et Instagram, jour et nuit, et remplir l'agenda",
        "includes": [
            "Réponses instantanées sur Facebook Messenger et Instagram, 24 h/24",
            "Qualification du projet et du budget",
            "Prise de rendez-vous directement dans votre agenda",
            "Alerte immédiate par SMS et e-mail à chaque lead et chaque rendez-vous",
        ],
        "setup": "490 € à 890 € HT",
        "setup_note": "connexion de la page, personnalisation des réponses et des règles métier",
        "monthly": "149 € à 249 € HT / mois",
        "monthly_note": "maintenance, hébergement, jusqu'à 300 conversations par mois",
    },
    {
        "id": "commercial-ia",
        "title": "Commercial & Standardiste IA Complet",
        "level": "Texte + téléphone",
        "icon": "bi-telephone-inbound-fill",
        "featured": True,
        "for": "BTP, promoteurs, agences immobilières, installateurs de pompes à chaleur et solaire, cabinets d'expertise.",
        "promise": "un accueil texte et téléphone 24/7 qui qualifie, réserve et prépare le devis",
        "includes": [
            "Tout le Standardiste Messenger & Insta",
            "Accueil téléphonique vocal 24/7 sur un numéro dédié",
            "Qualification des appels et rappel des prospects par SMS",
            "Créneaux bloqués directement dans votre planning",
            "Fiche contact et devis brouillon créés automatiquement dans votre CRM",
        ],
        "setup": "1 200 € à 2 400 € HT",
        "setup_note": "",
        "monthly": "390 € à 590 € HT / mois",
        "monthly_note": "500 conversations texte et jusqu'à 200 minutes d'appels qualifiés par mois",
    },
    {
        "id": "machine-a-leads",
        "title": "Machine à Leads Clé en Main",
        "level": "Publicité + IA",
        "icon": "bi-funnel-fill",
        "for": "PME avec un budget publicitaire mensuel qui veulent un flux continu de clients.",
        "promise": "des campagnes Facebook et Instagram dont chaque prospect est recontacté dans les 2 minutes",
        "includes": [
            "Création, gestion et optimisation de vos campagnes Meta Ads (Facebook, Instagram)",
            "Formulaires Lead Ads intégrés aux publicités",
            "Agent IA 24/7 : chaque prospect recontacté dans les 2 minutes par SMS et e-mail",
            "Qualification par SMS et prise de rendez-vous dans votre planning",
        ],
        "setup": "1 500 € HT",
        "setup_note": "frais de lancement",
        "monthly": "990 € à 1 800 € HT / mois",
        "monthly_note": "accompagnement mensuel ; budget publicitaire réglé directement par vous à Meta",
    },
]

PACKS = [
    {
        "id": "ecommerce",
        "title": "Boutique e-commerce prête à vendre",
        "icon": "bi-bag-check-fill",
        "for": "Commerçants et porteurs de projet qui lancent une boutique dans une niche précise.",
        "promise": "une boutique en ligne optimisée pour sa niche, prête à encaisser",
        "problem": "Une boutique en ligne vide ne vend pas : il faut le catalogue, le référencement et le trafic de lancement.",
        "components": [
            ("Boutique en ligne avec paiement sécurisé et gestion des stocks", "2 490 €"),
            ("Fiches produits rédigées pour le référencement", "79 €/article"),
            ("Référencement technique de la boutique", "490 €"),
            ("Campagne publicitaire de lancement", "290 €/mois"),
            ("E-mails automatiques (panier abandonné, relance client)", "490 €"),
        ],
        "price": None,
        "anchor": "/services#ecommerce",
    },
    {
        "id": "local",
        "title": "Visibilité locale 974",
        "icon": "bi-geo-alt-fill",
        "for": "Commerces et services de proximité à La Réunion.",
        "promise": "être trouvé sur Google et choisi par les clients du quartier",
        "problem": "Les clients cherchent sur Google Maps et tombent sur les concurrents mieux notés.",
        "components": [
            ("Site vitrine, hébergement inclus", "990 €"),
            ("Fiche Google Business optimisée et collecte d'avis", "390 €"),
            ("Publications régulières sur les réseaux sociaux", "390 €/mois"),
        ],
        "price": None,
        "anchor": "/services#seo",
    },
]
