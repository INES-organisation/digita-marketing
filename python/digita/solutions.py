"""Packs clés en main de la page /solutions (repris par le chatbot).

Un pack assemble des services du catalogue (`services_catalog.py`) pour régler un problème
précis, de bout en bout. Les composants affichent le prix public de chaque service ; le prix du
pack lui-même est établi après le diagnostic gratuit tant qu'il n'est pas fixé. Prix des composants
= prix d'entrée (« dès ») de la ligne correspondante du catalogue ou de realisations.py
(docs/SUIVI_CONNEXION_INES.md §3). Pour fixer un prix : renseigner « price ».
"""

PACKS = [
    {
        "id": "acquisition",
        "title": "Système d'acquisition automatique",
        "icon": "bi-funnel-fill",
        "for": "TPE et PME qui veulent des demandes de clients régulières, sans dépendre du bouche-à-oreille.",
        "promise": "des prospects qui arrivent, sont suivis et relancés tout seuls",
        "problem": "Les demandes arrivent par à-coups, se perdent dans WhatsApp et personne n'a le temps de relancer.",
        "components": [
            ("Page de vente LP48, livrée en 48 h ouvrées", "997 €"),
            ("Campagnes Facebook, Instagram ou Google Ads", "290 €/mois"),
            ("CRM et relances automatiques par e-mail", "490 €"),
            ("Assistant IA 24/7 sur le site ou WhatsApp", "990 €"),
            ("Tableau de bord des demandes et du coût par prospect", "290 €/mois"),
        ],
        "price": None,
        "anchor": "/services#ia-automation",
    },
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
        "id": "rendez-vous",
        "title": "Prise de rendez-vous automatisée",
        "icon": "bi-calendar2-check-fill",
        "for": "Cabinets de santé, instituts de beauté, bien-être et prestataires de services.",
        "promise": "des rendez-vous pris en ligne, rappelés automatiquement, et des avis clients",
        "problem": "Le téléphone sonne pendant les rendez-vous, les absences coûtent cher et les avis ne sont jamais demandés.",
        "components": [
            ("Site vitrine, hébergement inclus", "990 €"),
            ("Prise de rendez-vous en ligne et rappels automatiques", "490 €"),
            ("Demande d'avis Google automatique après la visite", "390 €"),
            ("Assistant IA qui répond aux questions fréquentes", "990 €"),
        ],
        "price": None,
        "anchor": "/services#sites-web",
    },
    {
        "id": "devis",
        "title": "Devis et relances automatiques",
        "icon": "bi-file-earmark-check-fill",
        "for": "Artisans, entreprises du BTP, cuisinistes, piscinistes, rénovation.",
        "promise": "des demandes de devis qualifiées et relancées jusqu'à la signature",
        "problem": "Les demandes de devis arrivent incomplètes, les devis partent tard et ne sont jamais relancés.",
        "components": [
            ("Site vitrine avec formulaire de devis qualifié", "990 €"),
            ("CRM et relances automatiques des devis envoyés", "490 €"),
            ("Campagnes locales Google Ads", "290 €/mois"),
            ("Référencement local et fiche Google", "390 €"),
        ],
        "price": None,
        "anchor": "/services#ia-automation",
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
