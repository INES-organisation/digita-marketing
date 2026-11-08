"""Boutique DIGITA (page /boutique) : produits numériques vendus sur digita.buzz, matériel sur MultiProShop.

Source unique des produits et de leurs prix (digita.buzz fait foi, comme pour services_catalog.py).
Prix nets, TVA non applicable (art. 293 B du CGI), proposés le 08/11/2026 :

- Packs de prompts : fichiers téléchargeables, prix d'un produit numérique d'entrée de gamme (19-39 €).
- Workflows IA : modèles de la bibliothèque INES (« Templates INES », ent-001 à ent-010), qui ne tournent
  que dans INES : ils se vendent donc installés et paramétrés par DIGITA (prix d'une installation de
  freelance n8n/Make, bas de fourchette pour les TPE de La Réunion), maintenance mensuelle en option.
  La version fichier à installer soi-même (export n8n) viendra une fois les workflows reconstruits.
- Matériel (ordinateurs, électronique) : vendu et livré par MultiProShop, la boutique ne fait que le présenter.

OPEN reste à False tant que la vente en ligne n'est pas branchée (fichiers, table des commandes de
produits) : la page affiche alors « ouverture prochaine » et une liste d'attente.
"""

OPEN = False
MPS_URL = "https://multiproshop.com"

PROMPT_PACKS = [
    {"id": "pack-artisans-btp", "title": "Pack Artisans & BTP", "price": "29 €",
     "items": ["Devis et relances de devis", "Réponses aux avis Google", "Publications de chantier pour les réseaux"]},
    {"id": "pack-sante-bien-etre", "title": "Pack Santé & bien-être", "price": "29 €",
     "items": ["Rappels et confirmations de rendez-vous", "Réponses aux avis", "Conseils et publications de saison"]},
    {"id": "pack-immobilier", "title": "Pack Immobilier", "price": "29 €",
     "items": ["Annonces de biens", "Relances d'acquéreurs et de vendeurs", "Comptes rendus de visite"]},
    {"id": "pack-commerce", "title": "Pack Commerce & e-commerce", "price": "29 €",
     "items": ["Fiches produits", "E-mails de promotion et de relance", "Réponses au service client"]},
]
PROMPT_BUNDLE = {"id": "pack-complet", "title": "Les 4 packs de prompts", "price": "79 €"}

# Modèle INES d'origine entre parenthèses (frontend/src/app/workflows/templates-ines/WorkflowAutomationData.ts).
WORKFLOWS = [
    {"id": "qualification-prospects", "ines": "ent-001", "title": "Qualification et routage des prospects", "price": "390 €",
     "summary": "Chaque demande reçue par formulaire est lue par l'IA, notée et envoyée à la bonne personne avec une réponse prête."},
    {"id": "relance-devis", "ines": "ent-003", "title": "Relance automatique des devis (21 jours)", "price": "490 €",
     "summary": "Une séquence de relances personnalisées par e-mail tant que le prospect n'a pas répondu ; vous êtes prévenu à chaque réponse."},
    {"id": "clients-dormants", "ines": "ent-004", "title": "Réactivation des clients dormants", "price": "590 €",
     "summary": "Chaque semaine, les clients sans nouvelles depuis longtemps reçoivent un message adapté à leur historique."},
    {"id": "devis-ia", "ines": "ent-009", "title": "Génération de devis par l'IA", "price": "690 €",
     "summary": "À partir d'une demande, l'IA prépare un devis au format PDF que vous validez avant envoi, puis relance."},
    {"id": "rapports-alertes", "ines": "ent-005", "title": "Rapports et alertes automatiques", "price": "790 €",
     "summary": "Un point hebdomadaire de votre activité par e-mail, et une alerte dès qu'un indicateur décroche."},
    {"id": "support-niveau-1", "ines": "ent-008", "title": "Support client IA de niveau 1", "price": "890 €",
     "summary": "Les questions simples de vos clients reçoivent une réponse immédiate ; les autres vous sont transmises, déjà résumées."},
]
WORKFLOW_MAINTENANCE = "49 €/mois"
