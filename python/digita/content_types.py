"""Types de contenu du blog (plan de contenu du 09/11/2026). Couleur de chaque type : .blog-type--<slug>
dans public/assets/css/blog-layout.css (les catégories sont en bleu, .blog-cat).

Le type est stocké dans blog_articles.content_type (NULL pour les articles d'origine, non classés).
Il s'affiche en badge sur les cartes et en tête d'article, et sert de filtre sur /blog (?type=guide).
"""

TYPES = {
    "guide": {"label": "Guide", "plural": "Guides", "icon": "bi-journal-bookmark",
              "lead": "Tout comprendre sur un sujet, de A à Z."},
    "pas-a-pas": {"label": "Pas à pas", "plural": "Pas à pas", "icon": "bi-list-check",
                  "lead": "Réussir une tâche précise, étape par étape."},
    "comparatif": {"label": "Comparatif", "plural": "Comparatifs", "icon": "bi-layout-split",
                   "lead": "Choisir entre deux ou trois options."},
    "actualite": {"label": "Actualité", "plural": "Actualités", "icon": "bi-megaphone",
                  "lead": "Ce qui change pour les TPE, et ce qu'il faut faire."},
    "definition": {"label": "Définition", "plural": "Définitions", "icon": "bi-book",
                   "lead": "Comprendre un mot ou une notion du digital."},
    "modele": {"label": "Modèle", "plural": "Modèles", "icon": "bi-clipboard-check",
               "lead": "Un outil prêt à l'emploi : checklist, modèle, calendrier."},
}


def get(slug):
    """Le type connu, ou None (paramètre absent, inconnu ou article non classé)."""
    return TYPES.get(slug or "")
