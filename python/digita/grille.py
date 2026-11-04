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
