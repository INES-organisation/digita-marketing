"""Boutique DIGITA (/boutique) : produits vendus et payés sur digita.buzz, matériel sur MultiProShop.

Source unique des produits et de leurs prix (digita.buzz fait foi, comme services_catalog.py).
Prix nets, TVA non applicable (art. 293 B du CGI), fixés le 08/11/2026 :

- Packs de master prompts : PDF mis en page + version texte (Markdown) pour copier-coller, dans
  python/digita/boutique_files/ (PDF générés par python/tools/build_boutique_pdfs.py). Livrés par lien
  personnel après paiement.
- Workflows IA : les 10 « Workflows Entreprise » de la bibliothèque INES (ent-001 à ent-010). Ils ne
  tournent que dans INES : on vend leur installation et leur paramétrage par DIGITA. Prix calés sur la
  grille « Automatisation » de /tarifs (490 / 790 / 1 200 €) selon la complexité du workflow (nombre de
  nœuds, niveau INES Moyen / Avancé / Expert), bien en dessous des prix « ETI » indiqués dans INES.
- Matériel (ordinateurs, électronique) : vendu et livré par MultiProShop, la boutique le présente.

OPEN : vente en ligne ouverte (table shop_downloads et colonnes de la migration
database/migrations/2026_11_08_boutique.sql appliquées en production).
"""

OPEN = True
MPS_URL = "https://multiproshop.com"
WORKFLOW_MAINTENANCE = "49 €/mois"
DOWNLOAD_DAYS = 30        # validité d'un lien de téléchargement
DOWNLOAD_MAX = 5          # téléchargements par lien (un nouveau lien s'obtient depuis « Mes commandes »)

PROMPT_PACKS = [
    {"slug": "pack-artisans-btp", "title": "Pack Artisans & BTP", "price": 29, "file": "pack-artisans-btp.md",
     "summary": "10 master prompts pour les écrits de tous les jours d'un artisan ou d'une entreprise du bâtiment.",
     "items": ["Devis clairs et relances à J+3, J+10, J+21", "Réponses aux avis Google", "Publications de chantier avant/après",
               "Demandes urgentes, retards, réclamations", "Fiches services pour le référencement local"]},
    {"slug": "pack-sante-bien-etre", "title": "Pack Santé & bien-être", "price": 29, "file": "pack-sante-bien-etre.md",
     "summary": "10 master prompts pour instituts, praticiens du bien-être et coachs, sans allégation thérapeutique.",
     "items": ["Confirmations, rappels et annulations de rendez-vous", "Réponses aux avis", "Publications de saison et conseils",
               "Carte de soins et fiche Google Business", "Fidélisation et relance des clients inactifs"]},
    {"slug": "pack-immobilier", "title": "Pack Immobilier", "price": 29, "file": "pack-immobilier.md",
     "summary": "10 master prompts pour agences et mandataires, mentions obligatoires laissées à compléter.",
     "items": ["Annonces de biens", "Relances acquéreurs et vendeurs", "Comptes rendus de visite",
               "Publications réseaux d'un nouveau bien", "Script d'appel de prospection"]},
    {"slug": "pack-commerce", "title": "Pack Commerce & e-commerce", "price": 29, "file": "pack-commerce.md",
     "summary": "10 master prompts pour boutiques physiques et en ligne.",
     "items": ["Fiches produits optimisées pour Google", "Promotions, newsletters, paniers abandonnés",
               "Service client : retours, retards, produits défectueux", "Réponses aux avis", "FAQ produit"]},
]
PROMPT_BUNDLE = {"slug": "pack-complet", "title": "Les 4 packs de master prompts", "price": 79,
                 "files": [p["file"] for p in PROMPT_PACKS],
                 "summary": "Les 40 master prompts des quatre métiers, pour 79 € au lieu de 116 €."}

WORKFLOW_GROUPS = ["Commercial IA", "Opérations IA", "Support et veille"]

# « ines » : identifiant du modèle dans INES (frontend/src/app/workflows/templates-ines/WorkflowAutomationData.ts).
WORKFLOWS = [
    {"slug": "qualification-prospects", "ines": "ent-001", "group": "Commercial IA", "price": 490,
     "title": "Qualification et routage des prospects",
     "summary": "Chaque demande entrante est lue par l'IA (budget, lieu, type de besoin), notée et envoyée aussitôt à la bonne personne, avec une réponse prête."},
    {"slug": "suivi-21-jours", "ines": "ent-003", "group": "Commercial IA", "price": 590,
     "title": "Séquence de suivi sur 21 jours",
     "summary": "Cinq e-mails personnalisés par l'IA (J0, J3, J7, J14, J21) pour chaque prospect, et une tâche d'appel quand il le faut."},
    {"slug": "reactivation-clients", "ines": "ent-004", "group": "Commercial IA", "price": 690,
     "title": "Réactivation des clients dormants",
     "summary": "Chaque lundi, les contacts inactifs depuis plus de 90 jours reçoivent une campagne de 3 messages sur 12 jours, rédigée selon leur historique."},
    {"slug": "devis-ia", "ines": "ent-009", "group": "Commercial IA", "price": 890,
     "title": "Génération de devis par l'IA",
     "summary": "À partir d'une demande, l'IA prépare un devis complet en PDF (lignes, remise, arguments), que vous validez avant l'envoi et la relance."},
    {"slug": "lead-scoring", "ines": "ent-007", "group": "Commercial IA", "price": 1290,
     "title": "Notation des prospects en temps réel",
     "summary": "Chaque action d'un prospect recalcule sa note d'intérêt de 0 à 100 ; vous êtes alerté dès qu'un contact devient chaud."},
    {"slug": "traitement-documents", "ines": "ent-002", "group": "Opérations IA", "price": 990,
     "title": "Traitement des documents par l'IA",
     "summary": "Factures, devis et contrats lus automatiquement : extraction des données, contrôle, détection des anomalies et classement."},
    {"slug": "rapports-alertes", "ines": "ent-005", "group": "Opérations IA", "price": 790,
     "title": "Rapports et alertes automatiques",
     "summary": "Chaque matin de semaine, un point clair de vos ventes, tâches et contacts, et une alerte dès qu'un indicateur décroche."},
    {"slug": "onboarding-client", "ines": "ent-006", "group": "Opérations IA", "price": 1190,
     "title": "Accueil automatisé des nouveaux clients",
     "summary": "Dès la signature : accès envoyés, messages d'accompagnement sur 30 jours (J0 à J30) et mesure de la satisfaction."},
    {"slug": "support-niveau-1", "ines": "ent-008", "group": "Support et veille", "price": 990,
     "title": "Support client IA de niveau 1",
     "summary": "Chaque demande est classée : réponse immédiate si elle est simple, transmise avec un résumé complet si elle est délicate."},
    {"slug": "veille-concurrentielle", "ines": "ent-010", "group": "Support et veille", "price": 690,
     "title": "Veille concurrentielle automatique",
     "summary": "Chaque lundi, une synthèse de ce que font vos concurrents (sites, actualités, réseaux), avec les points d'alerte."},
]


def euros(amount):
    return f"{amount:,}".replace(",", " ") + " €"


def _pack_files(markdown_name):
    """Un pack se livre en PDF mis en page et en version texte (pour copier-coller les prompts)."""
    return [markdown_name.replace(".md", ".pdf"), markdown_name]


MEDIA_TYPES = {".pdf": "application/pdf", ".md": "text/markdown; charset=utf-8"}


def products():
    """Tous les produits vendables, par identifiant : packs (téléchargement) et workflows (installation)."""
    items = {}
    for p in PROMPT_PACKS:
        items[p["slug"]] = {**p, "kind": "download", "files": _pack_files(p["file"])}
    items[PROMPT_BUNDLE["slug"]] = {**PROMPT_BUNDLE, "kind": "download", "items": [p["title"] for p in PROMPT_PACKS],
                                    "files": [f for p in PROMPT_PACKS for f in _pack_files(p["file"])]}
    for w in WORKFLOWS:
        items[w["slug"]] = {**w, "kind": "service", "files": []}
    return items


def product(slug):
    return products().get(slug)
