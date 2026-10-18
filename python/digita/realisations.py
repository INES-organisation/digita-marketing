"""Réalisations affichées sur l'accueil (section « Réalisations »).

Chaque catégorie présente ce que nous savons réaliser (offre, tarif indicatif, délai,
prestations) puis les projets livrés. Pour ajouter un projet : ajouter un dictionnaire dans
la liste « items » de sa catégorie :
    title, description, et facultativement url (lien externe), client, tag, metrics
    (liste de couples (valeur, libellé)).
Une catégorie sans projet affiche « Premiers projets bientôt en ligne ».
"""

REALISATIONS = [
    {
        "id": "sites-web",
        "title": "Sites web et landing",
        "icon": "bi-window-desktop",
        "color": "#D4AF37",
        "tagline": "Des sites qui font sonner le téléphone.",
        "description": "Offre 974 : on crée, on héberge et on maintient votre site vitrine. "
                       "Vous ne payez que votre identité visuelle, une fois.",
        "price": "1 490 €",
        "price_note": "identité visuelle (logo, charte, photos, textes), site offert, "
                      "puis maintenance 79 €/mois sur 24 mois",
        "delay": "3 à 4 semaines",
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
                "tag": "À partir de 997 €",
            },
            {
                "title": "Lurel : un point de vente digital pour les promotions du mois",
                "client": "Commerce local, La Réunion",
                "description": "Une page promotionnelle claire et pensée mobile pour présenter l'offre "
                               "du mois aux clients, en magasin comme en ligne.",
                "metrics": [("< 1 semaine", "mise en ligne"), ("Réutilisable", "pour les prochaines offres")],
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
        "price": "590 €/mois",
        "price_note": "tarif indicatif selon le nombre de réseaux et de publications",
        "delay": "Engagement 3 mois minimum",
        "capabilities": [
            "Charte réseaux sociaux adaptée à votre métier",
            "12 à 20 publications par mois : visuels, vidéos courtes, textes",
            "Calendrier mensuel validé par vous en 10 minutes",
            "Messages et commentaires traités tous les jours",
            "Point mensuel de 30 minutes avec les chiffres clés",
        ],
        "items": [],
    },
    {
        "id": "publicite",
        "title": "Publicité",
        "icon": "bi-megaphone",
        "color": "#f97316",
        "tagline": "Payez pour des résultats, pas pour des promesses.",
        "description": "Campagnes Google, Facebook et Instagram pilotées pour que chaque euro "
                       "investi vous en rapporte plus.",
        "price": "490 €/mois",
        "price_note": "gestion, hors budget publicitaire (300 à 500 €/mois conseillés)",
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
        "price": "890 €",
        "price_note": "par scénario, payé une fois (outils : 10 à 30 €/mois)",
        "delay": "1 à 3 semaines",
        "capabilities": [
            "Gmail, Outlook, Google Sheets, agendas, CRM, WhatsApp Business",
            "Devis et factures (Pennylane, Sellsy…), e-commerce",
            "Scénarios n8n, Make ou Zapier, testés et documentés",
            "Applications métier et applis mobiles sur mesure",
        ],
        "items": [
            {
                "title": "TTC France : une plateforme pour piloter toute une régie publicitaire",
                "client": "Régie publicitaire radio",
                "description": "Les fichiers Excel et les e-mails remplacés par une plateforme unique, "
                               "du contrat signé à la facturation, avec un tableau de bord par métier.",
                "metrics": [("≈ 40 min", "gagnées par dossier"), ("÷ 5", "erreurs de saisie"),
                            ("4 métiers", "sur une seule plateforme")],
            },
            {
                "title": "TTC Sales : une appli mobile pour ne plus perdre un appel commercial",
                "client": "Force de vente terrain",
                "description": "Application iOS et Android : contacts du jour, appel, SMS ou WhatsApp "
                               "en un geste, suivi automatique de chaque relance.",
                "metrics": [("≈ 2 min", "délai de rappel"), ("≈ 0", "lead non traité"),
                            ("iOS + Android", "disponible")],
            },
            {
                "title": "TatooModel : de la candidature au contrat signé, dans un seul outil",
                "client": "Industrie du tatouage",
                "description": "Formulaire de candidature unique, suivi visuel de chaque dossier et "
                               "campagnes e-mail automatisées.",
                "metrics": [("100 %", "candidatures centralisées"), ("÷ 3", "temps de traitement")],
            },
        ],
    },
    {
        "id": "agents-ia",
        "title": "Agents IA",
        "icon": "bi-robot",
        "color": "#a78bfa",
        "tagline": "Un assistant qui ne dort jamais, formé sur vos informations.",
        "description": "Il répond à vos clients, prend des rendez-vous, qualifie les demandes "
                       "et transmet à un humain quand il le faut.",
        "price": "1 490 €",
        "price_note": "mise en place, puis quelques centimes par conversation",
        "delay": "2 à 4 semaines",
        "capabilities": [
            "Réponse immédiate 24h/24, sur votre site, WhatsApp ou messagerie",
            "Entraîné sur vos services, vos tarifs et votre façon de parler",
            "Qualification des demandes de devis et prise de rendez-vous",
            "Testé à huis clos avant la mise en ligne, conversations visibles",
            "Modèles européens (Mistral) ou sous contrat strict (Claude, OpenAI)",
        ],
        "items": [],
    },
]
