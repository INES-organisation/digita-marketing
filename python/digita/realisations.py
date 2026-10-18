"""Réalisations affichées sur l'accueil (section « Réalisations »).

Pour ajouter une réalisation : ajouter un dictionnaire dans la liste « items » de sa catégorie
(title, url, description, et facultativement tag). Une catégorie sans réalisation affiche
« Premières réalisations bientôt en ligne ».
"""

REALISATIONS = [
    {
        "id": "sites-web",
        "title": "Sites web et landing",
        "icon": "bi-window-desktop",
        "color": "#D4AF37",
        "description": "Sites vitrines, pages de vente et landing pages pensées pour convertir.",
        "items": [
            {
                "title": "LP48 : votre page de vente en 48h",
                "url": "https://lp48.digita.buzz",
                "description": "Page de vente clé-en-main : copywriting, design, formulaire ou paiement "
                               "et mise en ligne inclus, livrée en 48h ouvrées.",
                "tag": "À partir de 997 € TTC",
            },
        ],
    },
    {
        "id": "reseaux-sociaux",
        "title": "Réseaux sociaux",
        "icon": "bi-people",
        "color": "#60a5fa",
        "description": "Stratégie éditoriale, création de contenu et animation de communautés.",
        "items": [],
    },
    {
        "id": "publicite",
        "title": "Publicité",
        "icon": "bi-megaphone",
        "color": "#f97316",
        "description": "Campagnes Google et Meta pilotées au coût d'acquisition.",
        "items": [],
    },
    {
        "id": "automatisation",
        "title": "Automatisation",
        "icon": "bi-diagram-3",
        "color": "#34d399",
        "description": "Workflows, CRM et intégrations qui font gagner des heures chaque semaine.",
        "items": [],
    },
    {
        "id": "agents-ia",
        "title": "Agents IA",
        "icon": "bi-robot",
        "color": "#a78bfa",
        "description": "Assistants et agents intelligents connectés à vos outils et à vos données.",
        "items": [],
    },
]
