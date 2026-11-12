"""Grille Essentiel / Pro / Premium des prestations digitales (page /tarifs).

Mêmes prix que le catalogue des missions de Tony Alpha 8.0 (tonyalpha80/python/ta80/data/missions.json),
DIGITA étant le référentiel des missions digitales : changer un prix ici, c'est le changer là-bas aussi.
Prix nets (TVA non applicable, art. 293 B du CGI). « monthly » : abonnement mensuel du niveau.
"""

LEVELS = {"essentiel": "Essentiel", "pro": "Pro", "premium": "Premium"}

GRILLE = [{'id': 'landing-page',
  'title': 'Landing page',
  'summary': 'Une page de vente ou de présentation avec formulaire de contact.',
  'delay_days': 5,
  'levels': {'essentiel': {'price': 499, 'monthly': None, 'note': '1 révision, contenus fournis par vous.'},
             'pro': {'price': 790, 'monthly': None, 'note': '2 révisions, rédaction incluse.'},
             'premium': {'price': 1190,
                         'monthly': None,
                         'note': "Révisions jusqu'à validation, rédaction et visuels inclus, 1 mois de "
                                 'suivi.'}}},
 {'id': 'site-vitrine',
  'title': 'Site vitrine',
  'summary': 'Un site de 5 pages au plus, responsive et référencé.',
  'delay_days': 15,
  'levels': {'essentiel': {'price': 990, 'monthly': None, 'note': '1 révision, contenus fournis par vous.'},
             'pro': {'price': 1690, 'monthly': None, 'note': '2 révisions, rédaction incluse.'},
             'premium': {'price': 2900,
                         'monthly': None,
                         'note': "Révisions jusqu'à validation, rédaction et visuels inclus, 1 mois de "
                                 'suivi.'}}},
 {'id': 'site-ecommerce',
  'title': 'Site e-commerce sur mesure',
  'summary': 'Boutique en ligne à votre marque : paiement sécurisé, gestion des stocks.',
  'delay_days': 30,
  'levels': {'essentiel': {'price': 2490, 'monthly': None, 'note': '1 révision, contenus fournis par vous.'},
             'pro': {'price': 3490, 'monthly': None, 'note': '2 révisions, rédaction incluse.'},
             'premium': {'price': 4900,
                         'monthly': None,
                         'note': "Révisions jusqu'à validation, rédaction et visuels inclus, 1 mois de "
                                 'suivi.'}}},
 {'id': 'identite-visuelle',
  'title': 'Identité visuelle',
  'summary': 'Logo, déclinaisons et charte graphique.',
  'delay_days': 7,
  'levels': {'essentiel': {'price': 190, 'monthly': None, 'note': 'Logo seul, 2 propositions.'},
             'pro': {'price': 490, 'monthly': None, 'note': 'Logo et charte graphique, 3 propositions.'},
             'premium': {'price': 900, 'monthly': None, 'note': 'Logo, charte complète et brand book.'}}},
 {'id': 'video',
  'title': 'Vidéo',
  'summary': 'Formats courts pour les réseaux ou vidéo de présentation.',
  'delay_days': 10,
  'levels': {'essentiel': {'price': 190, 'monthly': None, 'note': 'Vidéo courte (Reel, TikTok, Short).'},
             'pro': {'price': 590,
                     'monthly': None,
                     'note': "Vidéo promotionnelle d'entreprise ou de produit."},
             'premium': {'price': 1190,
                         'monthly': None,
                         'note': 'Production avancée : motion design ou tournage pro.'}}},
 {'id': 'contenus-reseaux',
  'title': 'Contenus réseaux sociaux',
  'summary': 'Publications préparées et planifiées chaque mois.',
  'delay_days': 7,
  'levels': {'essentiel': {'price': 0, 'monthly': 290, 'note': '8 publications par mois.'},
             'pro': {'price': 0,
                     'monthly': 390,
                     'note': 'Community management : 12 publications, modération, reporting.'},
             'premium': {'price': 0,
                         'monthly': 690,
                         'note': '20 publications dont vidéos courtes, modération, reporting.'}}},
 {'id': 'publicite',
  'title': 'Publicité en ligne',
  'summary': 'Campagnes Google Ads ou Meta Ads pilotées chaque mois.',
  'delay_days': 7,
  'levels': {'essentiel': {'price': 0, 'monthly': 290, 'note': 'Une plateforme (Google ou Meta).'},
             'pro': {'price': 0, 'monthly': 490, 'note': 'Deux plateformes, A/B tests.'},
             'premium': {'price': 0,
                         'monthly': 790,
                         'note': 'Multi-plateformes, retargeting, reporting hebdomadaire.'}}},
 {'id': 'email-marketing',
  'title': 'Newsletters et e-mails',
  'summary': "Newsletters et campagnes d'e-mails envoyées chaque mois.",
  'delay_days': 7,
  'levels': {'essentiel': {'price': 0, 'monthly': 190, 'note': '1 révision, contenus fournis par vous.'},
             'pro': {'price': 0, 'monthly': 290, 'note': '2 révisions, rédaction incluse.'},
             'premium': {'price': 0,
                         'monthly': 490,
                         'note': "Révisions jusqu'à validation, rédaction et visuels inclus, 1 mois de "
                                 'suivi.'}}},
 {'id': 'seo',
  'title': 'Audit et optimisation SEO',
  'summary': 'Être trouvé sur Google quand on cherche votre métier.',
  'delay_days': 10,
  'levels': {'essentiel': {'price': 390,
                           'monthly': None,
                           'note': 'SEO local : fiche Google Business et avis clients.'},
             'pro': {'price': 590, 'monthly': None, 'note': 'Audit technique et optimisation des pages.'},
             'premium': {'price': 1200,
                         'monthly': None,
                         'note': 'Audit complet, optimisation et plan de contenus sur 3 mois.'}}},
 {'id': 'agent-ia-24-7',
  'title': 'Agent IA 24/7',
  'summary': 'Un agent IA qui répond à vos clients jour et nuit, qualifie et remplit votre agenda.',
  'delay_days': 10,
  'levels': {'essentiel': {'price': 490,
                           'monthly': 149,
                           'note': 'Standardiste Messenger et Instagram : réponses 24 h/24, prise de '
                                   'rendez-vous, alertes SMS et e-mail (300 conversations par mois).'},
             'pro': {'price': 1200,
                     'monthly': 390,
                     'note': 'Commercial et standardiste complet : en plus, accueil téléphonique vocal 24/7 '
                             'et devis brouillons dans votre CRM.'},
             'premium': {'price': 1500,
                         'monthly': 990,
                         'note': 'Machine à leads : campagnes Meta Ads gérées et chaque prospect recontacté '
                                 'en 2 minutes (budget pub en plus).'}}},
 {'id': 'chatbot',
  'title': 'Chatbot pour site web ou WhatsApp',
  'summary': 'Un assistant qui répond aux questions fréquentes de vos visiteurs.',
  'delay_days': 7,
  'levels': {'essentiel': {'price': 490, 'monthly': None, 'note': '1 révision, contenus fournis par vous.'},
             'pro': {'price': 790, 'monthly': None, 'note': '2 révisions, rédaction incluse.'},
             'premium': {'price': 1190,
                         'monthly': None,
                         'note': "Révisions jusqu'à validation, rédaction et visuels inclus, 1 mois de "
                                 'suivi.'}}},
 {'id': 'automatisation',
  'title': 'Automatisation (e-mails, CRM)',
  'summary': "Relances, séquences d'e-mails et tâches répétitives automatisées.",
  'delay_days': 10,
  'levels': {'essentiel': {'price': 490, 'monthly': None, 'note': '1 révision, contenus fournis par vous.'},
             'pro': {'price': 790, 'monthly': None, 'note': '2 révisions, rédaction incluse.'},
             'premium': {'price': 1200,
                         'monthly': None,
                         'note': "Révisions jusqu'à validation, rédaction et visuels inclus, 1 mois de "
                                 'suivi.'}}}]


def euros(x):
    """1690 → « 1 690 € »."""
    return f"{x:,}".replace(",", "\u202f") + "\u00a0€"


def price_label(level):
    """Prix affiché d'un niveau : forfait, forfait + mensualité, ou mensualité seule."""
    once, monthly = level["price"], level.get("monthly")
    if once and monthly:
        return f"{euros(once)} + {euros(monthly)}/mois"
    if monthly:
        return f"{euros(monthly)}/mois"
    return euros(once)


# Formations vendues sur INES (achat et suivi dans l'espace INES ; DIGITA ne montre qu'une fiche,
# servie à /formations/<id>). « visible » reste False tant que la formation n'est pas prête dans INES :
# voir docs/SUIVI_FORMATIONS.md. Aucun chiffre de résultat dans ces textes.
FORMATIONS_INES = [
    {"id": "etre-trouve-sur-google",
     "title": "Être trouvé sur Google en 30 jours",
     "price": 149,
     "price_note": "Paiement unique, sur INES",
     "url": "https://ines.weballone.com/formation/etre-trouve-sur-google",  # à confirmer à la création dans INES
     "visible": False,
     "card": "Fiche Google, avis, site et suivi : une action simple par leçon, pendant quatre semaines.",
     "lead": "Quinze leçons courtes, une action concrète à chaque fois, pour que vos clients vous trouvent "
             "quand ils cherchent votre métier près de chez eux. La leçon 1 est offerte.",
     "meta": "Formation en ligne pour TPE de La Réunion : fiche Google, avis, site et suivi, en 15 leçons "
             "vidéo et un kit de 8 outils. Leçon 1 offerte.",
     "content_title": "4 semaines, 15 leçons vidéo",
     "content_lead": "Chaque leçon est une courte vidéo narrée (voix de synthèse) avec une fiche action, et un "
                     "quiz de trois questions.",
     "modules": ["Semaine 1 : comprendre ce que voit votre client et faire l'état des lieux",
                 "Semaine 2 : revendiquer et régler votre fiche Google (catégorie, zone, horaires, services, photos)",
                 "Semaine 3 : obtenir des avis, y répondre, éviter ce qui fait disparaître une fiche",
                 "Semaine 4 : relier votre site, le rendre rapide sur téléphone, suivre vos résultats"],
     "includes": ["15 leçons vidéo et leurs fiches action",
                  "Un kit de 8 outils à adapter : grille d'état des lieux, modèles de demande et de réponse aux "
                  "avis, gabarit de page service, tableau de suivi…",
                  "Un quiz par leçon",
                  "La leçon 1 en accès libre"],
     "tag": "Leçon 1 offerte",
     "notice": "Aucune position sur Google n'est garantie : personne ne peut la promettre. Les résultats "
               "dépendent de votre métier, de votre zone et de la régularité de vos actions.",
     "audience_title": "Artisans, commerçants, indépendants",
     "audience_text": "Pour les entreprises de La Réunion qui veulent être trouvées par leurs clients sans outil "
                      "payant ni jargon. Tout se fait depuis un téléphone ou un ordinateur."},
    {"id": "dgt-systeme",
     "title": "DGT-Système : créer et vendre son produit digital avec INES",
     "price": 197,
     "price_note": "Paiement unique, sur INES",
     "url": "https://ines.weballone.com/formation/dgt-systeme",
     "visible": False,
     "card": "Choisir un sujet, construire l'offre, créer le produit, le vendre et le livrer avec INES.",
     "lead": "Un parcours pas à pas pour choisir un sujet, construire une offre, créer le produit, le mettre en "
             "vente et le livrer automatiquement, avec les outils d'INES.",
     "meta": "Parcours en ligne pour créer, mettre en vente et livrer un produit digital avec INES : 11 modules, "
             "43 leçons vidéo, attestation INES.",
     "content_title": "11 modules, 43 leçons vidéo",
     "content_lead": "Chaque leçon est une courte vidéo narrée (voix de synthèse), avec un objectif et les étapes "
                     "à suivre dans INES. Un quiz clôt chaque module.",
     "modules": ["Module 0 : démarrer, le modèle du produit digital",
                 "Module 1 : choisir sa niche et son client idéal",
                 "Module 2 : concevoir son offre",
                 "Module 3 : créer le produit avec INES",
                 "Module 4 : la page de vente",
                 "Module 5 : la vidéo de vente et les visuels",
                 "Module 6 : attirer des visiteurs sans budget publicitaire",
                 "Module 7 : paiement, offres complémentaires",
                 "Module 8 : automatiser la livraison, assistants IA",
                 "Module 9 : support, avis clients, développement",
                 "Module bonus : le marketing avec l'IA"],
     "includes": ["Les 43 leçons vidéo et les quiz de fin de module",
                  "13 ressources à consulter dans INES : modèles, grilles et checklists",
                  "Un examen final et un projet pratique réalisé dans INES",
                  "Une attestation INES quand l'examen et le projet sont validés"],
     "tag": "Parcours avec attestation INES",
     "notice": "L'attestation INES n'est pas une certification reconnue par l'État (RNCP ou Répertoire "
               "spécifique). Les outils d'INES utilisés pendant le parcours consomment des crédits, y compris "
               "avec le compte gratuit.",
     "audience_title": "Indépendants, formateurs, experts d'un métier",
     "audience_text": "Pour transformer un savoir-faire en produit vendu en ligne (guide, modèles, mini-formation), "
                      "sans équipe technique. Aucun résultat de vente n'est garanti : il dépend du sujet, de l'offre "
                      "et du travail fourni."},
]
FORMATIONS_INES_BY_ID = {f["id"]: f for f in FORMATIONS_INES}
