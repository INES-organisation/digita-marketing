"""Contenus de l'accueil qui servent deux fois : la FAQ (affichée et en données structurées)."""
import json

FAQ = [
    ('Combien coûte un site internet ?',
     "Une landing page démarre à 499 €. Pour un site vitrine, vous payez votre identité visuelle une fois : 990 € (690 € si vous avez déjà un logo), le site et l'hébergement sont inclus, puis une maintenance de 49 €/mois avec un engagement de 12 mois. Le devis est gratuit et détaillé."),
    ('En combien de temps mon site est-il en ligne ?',
     'Une landing page est livrée en 5 jours ouvrés, une page de vente LP48 en 48 heures ouvrées, un site vitrine en 3 à 4 semaines selon la rapidité des échanges sur les contenus.'),
    ('Est-ce que je reste propriétaire de mon site ?',
     'Oui. Nom de domaine, textes, images et accès vous appartiennent. Si vous partez, vous récupérez tout.'),
    ('Y a-t-il un engagement ?',
     "La publicité est sans engagement au-delà d'un mois. Les réseaux sociaux demandent 3 mois minimum, le temps d'installer une présence régulière. Le site vitrine comprend 12 mois de maintenance. Tout est écrit noir sur blanc dans le devis."),
    ('Les prix incluent-ils la TVA ?',
     'TVA non applicable (article 293 B du CGI) : le prix affiché est le prix que vous payez.'),
    ("Puis-je essayer l'agent IA sans risque ?",
     "Oui : le Standardiste Messenger & Insta 24/7 s'essaie 14 jours. La mise en service n'est facturée que si INES a enregistré au moins un rendez-vous dans votre agenda pendant l'essai ; sinon, rien n'est dû (CGV, article 5 bis)."),
    ("Un agent IA, concrètement, c'est quoi ?",
     'Un assistant qui répond à vos clients sur Messenger, Instagram ou votre site, 24h/24. Il connaît vos services et vos prix, prend des rendez-vous et vous passe la main quand il le faut. À partir de 149 €/mois après la mise en service.'),
    ('Comment se passe le diagnostic gratuit ?',
     '30 minutes en visio ou par téléphone. On regarde votre activité, vos outils et vos objectifs, et vous repartez avec 2 ou 3 actions prioritaires. Sans engagement : vous décidez ensuite.'),
    ('Avec qui travaillez-vous ?',
     'Avec les TPE et PME de La Réunion : artisans, commerçants, professions libérales, restaurateurs, prestataires de services… Si vous avez des clients à trouver ou du temps à gagner, on peut sûrement vous aider.'),
]


def structured_data():
    """JSON-LD de l'accueil : entreprise locale, site web et FAQ (résultats enrichis Google)."""
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "ProfessionalService",
                "@id": "https://digita.buzz/#entreprise",
                "name": "DIGITA",
                "alternateName": "Digita Marketing",
                "url": "https://digita.buzz/",
                "logo": "https://digita.buzz/assets/images/digita-192.png",
                "image": "https://digita.buzz/assets/images/og-digita.jpg",
                "description": "Agence IA et automatisation à La Réunion : sites web, réseaux sociaux, publicité, "
                               "automatisations et assistants IA pour TPE et PME.",
                "telephone": "+262693487817",
                "email": "contact@digita.buzz",
                "priceRange": "€€",
                "address": {"@type": "PostalAddress", "addressLocality": "Le Tampon", "postalCode": "97430",
                            "addressRegion": "La Réunion", "addressCountry": "FR"},
                "areaServed": {"@type": "AdministrativeArea", "name": "La Réunion"},
                "sameAs": ["https://www.facebook.com/profile.php?id=61593931724997"],
            },
            {
                "@type": "WebSite",
                "@id": "https://digita.buzz/#site",
                "url": "https://digita.buzz/",
                "name": "DIGITA",
                "inLanguage": "fr-FR",
                "publisher": {"@id": "https://digita.buzz/#entreprise"},
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
                    for q, r in FAQ
                ],
            },
        ],
    }
    # « </ » échappé pour qu'aucun texte ne puisse fermer la balise <script>
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
