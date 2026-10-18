"""Réalisations affichées sur l'accueil (section « Réalisations »).

Chaque catégorie présente son offre (price, price_note, delay, points) puis ses réalisations.
Pour ajouter une réalisation : ajouter un dictionnaire dans la liste « items » de sa catégorie
(title, description, et facultativement client, url, tag, metrics : liste de [valeur, libellé]).
Une réalisation sans url s'affiche sans lien. Une catégorie sans réalisation affiche
« Premières réalisations bientôt en ligne ».
"""

REALISATIONS = [
    {
        "id": "sites-web",
        "title": "Sites web et landing",
        "icon": "bi-window-desktop",
        "color": "#D4AF37",
        "description": "Sites vitrines, pages de vente et landing pages pensées pour convertir.",
        "price": "Site vitrine offert",
        "price_note": "Vous payez seulement votre identité visuelle, une fois : à partir de 1 490 €. "
                      "Maintenance 79 €/mois pendant 24 mois, puis sans engagement.",
        "delay": "3 à 4 semaines",
        "points": [
            "Design sur mesure, développement Next.js rapide et bien référencé",
            "Hébergement, SSL et nom de domaine .re ou .fr (1 an offert)",
            "Logo, charte, 10 photos et textes : les livrables sont à vous",
            "Cumulable avec le Kap Numérik pour financer l'identité visuelle",
        ],
        "items": [
            {
                "title": "LP48 : votre page de vente en 48h",
                "url": "https://lp48.digita.buzz",
                "description": "Page de vente clé-en-main : copywriting, design, formulaire ou paiement "
                               "et mise en ligne inclus, livrée en 48h ouvrées.",
                "tag": "À partir de 997 € TTC",
            },
            {
                "title": "Lurel",
                "client": "Commerce local, La Réunion",
                "description": "Une page promotionnelle claire et pensée mobile pour présenter l'offre du mois "
                               "aux clients, en magasin et en ligne.",
                "metrics": [["< 1 semaine", "Mise en ligne"], ["Réutilisable", "Prochaines offres"]],
            },
        ],
    },
    {
        "id": "reseaux-sociaux",
        "title": "Réseaux sociaux",
        "icon": "bi-people",
        "color": "#60a5fa",
        "description": "On crée, on planifie, on publie et on répond aux commentaires. Vous récoltez les clients.",
        "price": "À partir de 590 €/mois",
        "price_note": "Engagement 3 mois minimum.",
        "delay": "Premier calendrier dès le premier mois",
        "points": [
            "12 à 20 publications par mois sur 1 à 3 réseaux choisis avec vous",
            "Visuels, vidéos courtes et textes faits pour votre métier",
            "Messages et commentaires traités tous les jours",
            "Un point chiffré de 30 minutes chaque mois",
        ],
        "items": [],
    },
    {
        "id": "publicite",
        "title": "Publicité",
        "icon": "bi-megaphone",
        "color": "#f97316",
        "description": "Campagnes Google, Facebook et Instagram pilotées pour que chaque euro investi en rapporte plus.",
        "price": "À partir de 490 €/mois",
        "price_note": "Gestion des campagnes, budget publicitaire en plus (300 à 500 €/mois conseillés pour démarrer).",
        "delay": "Résultats sous 2 à 6 semaines",
        "points": [
            "Objectif chiffré : appels, devis ou visites en boutique",
            "Plusieurs versions de visuels et de textes testées",
            "On coupe ce qui ne marche pas, on amplifie ce qui marche",
            "Pas d'engagement long",
        ],
        "items": [],
    },
    {
        "id": "automatisation",
        "title": "Automatisation",
        "icon": "bi-diagram-3",
        "color": "#34d399",
        "description": "Devis, factures, relances, rendez-vous : vos outils branchés ensemble pour que tout se fasse tout seul.",
        "price": "À partir de 890 € par scénario",
        "price_note": "Payé une fois. Les outils (n8n, Make, Zapier) coûtent souvent 10 à 30 €/mois.",
        "delay": "1 à 3 semaines selon la complexité",
        "points": [
            "Plusieurs heures gagnées chaque semaine",
            "Moins d'oublis et d'erreurs de saisie",
            "Gmail, Sheets, agenda, CRM, facturation, WhatsApp Business",
            "Scénarios testés et documentés, modifiables par vous",
        ],
        "items": [
            {
                "title": "TTC France",
                "client": "Régie publicitaire radio",
                "description": "Une plateforme sur-mesure qui remplace fichiers Excel et emails, de la signature "
                               "du contrat à la facturation.",
                "metrics": [["≈ 40 min", "Gagnées par dossier"], ["÷ 5", "Erreurs de saisie"],
                            ["4 métiers", "Sur une plateforme"]],
            },
            {
                "title": "TTC Sales",
                "client": "Force de vente terrain",
                "description": "Une application iOS et Android pour les commerciaux : contacts du jour, appel, SMS "
                               "ou WhatsApp en un tap, suivi automatique de chaque relance.",
                "metrics": [["≈ 2 min", "Délai de rappel"], ["≈ 0", "Lead non traité"]],
            },
            {
                "title": "TatooModel",
                "client": "Industrie du tatouage",
                "description": "De la candidature au contrat signé dans le même outil : pipeline de suivi, "
                               "documents sécurisés et campagnes email automatisées.",
                "metrics": [["100 %", "Candidatures centralisées"], ["÷ 3", "Temps de traitement"]],
            },
        ],
    },
    {
        "id": "agents-ia",
        "title": "Agents IA",
        "icon": "bi-robot",
        "color": "#a78bfa",
        "description": "Un assistant formé sur vos documents, vos prix et votre façon de parler, qui travaille 24h/24.",
        "price": "À partir de 1 490 € + usage",
        "price_note": "Usage : quelques centimes par conversation, estimé avant le lancement.",
        "delay": "2 à 4 semaines de mise en place",
        "points": [
            "Réponse immédiate à vos clients, même la nuit et le week-end",
            "Qualification des demandes et prise de rendez-vous",
            "Sur votre site, votre WhatsApp ou votre messagerie",
            "Il passe la main à un humain quand il le faut",
        ],
        "items": [],
    },
]
