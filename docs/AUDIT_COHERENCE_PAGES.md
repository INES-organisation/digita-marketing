# Audit de cohérence des pages de digita.buzz (8 novembre 2026)

Analyse seule : aucune page n'a été modifiée pour cet audit. Les références de style et de contenu sont l'accueil, /services, /solutions et /diagnostic. Les prix font foi dans `services_catalog.py`, `grille.py` et `solutions.py`.

Chemins : V = `python/digita/templates/app/Views`, P = `python/digita/templates/includes/partials`, C = `public/assets/css`.

## 1. Problèmes transversaux (à traiter d'abord)

### Faux chiffres et fausse équipe (risque de crédibilité et de pratique commerciale trompeuse)
- /a-propos : « Fondée en 2019 », « plus de 200 entreprises », « 5+ années », « 200+ projets », « 15 experts », « 95 % de satisfaits » (V/about/index-content.html l.20-46). L'entreprise a été immatriculée en juin 2026, n'a qu'une personne et n'a livré qu'un logo.
- /catalogue : « Plus de 300 services » (l.7), pour environ 57 réellement listés.
- /formations : « Plus de 382 formations », « 3000+ heures de contenu », « 24/7 accès illimité ». Les 382 formations sont générées automatiquement, toutes à 97 €, toutes « Bientôt disponible », avec des sujets hors cible (crypto, NFT).
- « Notre équipe / nos experts / nos consultants » : /support, /outils, /contact, /blog, politique de confidentialité.
- « Le plus populaire » (/tarifs) et « Populaire » (/boutique, /formations) : fausse preuve sociale.

### Prix : quatre sources qui se contredisent
- Font foi : `services_catalog.py`, `grille.py`, `solutions.py`.
- Copies en dur qui divergent :
  - V/catalogue/index-content.html (1 418 lignes) ;
  - P/sidebar-onglet.html (la barre d'icônes de droite) ;
  - V/tarifs/index-content.html (cartes) ;
  - `models/project.py` (estimations du brief).
- Exemples :
  - Premium 2 990 € et Tunnel de vente 1 490 € n'existent nulle part ailleurs.
  - Business 990 € annonce « 5-10 pages » et « 3-4 semaines », alors que la grille dit « 5 pages » et « 15 jours ».
  - SEO à 490 €/mois contre une grille à 390/590/1 200 €.
  - Audit SEO 690 €, PWA 1 490 €, Photo 290 € contre les montants du catalogue.
  - Brief : landing à 997 € au lieu de 499 €, urgence ×1,5 au lieu de +30 %.
- Même dans la source : l'e-commerce est affiché « à partir de 2 490 € » alors qu'une de ses lignes est à 290 €/mois.

### Promesses impossibles ou fausses
- « Support dédié 24/7 », « réponse en moins de 2 h », horaires « lun-ven 9h-18h, sam 9h-13h » (affichés seulement sur /support).
- Paiement en 2 à 4 fois sans frais (/tarifs), alors que les CGV prévoient un acompte et un solde.
- Délais de réponse : 48 h (/contact), 48 h ouvrées (/services), 24 h ouvrées (/diagnostic), 24 h (brief).

### Appels à l'action
- Les pages de référence mènent à « Diagnostic gratuit » (/diagnostic), à WhatsApp et à la réservation d'un appel de 30 min.
- Les autres pages mènent à /contact « Demander un devis », à /projets/brief (qui exige d'être connecté) ou à des boutons sans lien.
- WhatsApp n'apparaît que sur l'accueil et /agent24-7.
- La navbar et le footer n'ont pas de bouton « Diagnostic gratuit ».

### Couleurs
- Vert, jaune et rouge Bootstrap (success, warning, danger) :
  - /outils et ses 4 outils ;
  - /boutique ;
  - badges des formations ;
  - coches de /tarifs et /a-propos ;
  - 57 icônes vertes de la barre de droite ;
  - 404 et brief.
- Bleus en thème sombre :
  - halo bleu de `.bg-premium-glow` (héros de /services, /solutions, /contact, /diagnostic) ;
  - fond navy `.bg-premium-dark-blue` (barre des catégories du blog) ;
  - `--blue-glow` ;
  - `text-blue` (classe inexistante) ;
  - popups navy de la barre de droite.
- Magenta et violet sur les formations (`#a21caf`, `#667eea→#764ba2`).
- En thème clair, les héros sont tantôt blancs, tantôt en bandeau bleu : légal, catalogue, tarifs, à propos, boutique, catégories du blog.
- Emojis dans les H1 : /support 💬, /outils 🛠️, /formations 🎓, /boutique 🛒, /blog 📰.

### Ton
Jargon « prestige » sans rapport avec le ton simple des pages de référence :
- « Architecture de Collaboration », « Hub Réunion », « FAQ PRESTIGE », « Lancer l'Analyse » (/contact) ;
- « Le Mag Stratégique », « Omnicanal », « leaders de demain » (/blog) ;
- « Priority Desk », « DIGITA Intelligence », « Lead Gen Advanced » (brief) ;
- « Executive Offer » (modale de conversion).

## 2. Page par page

### /a-propos (haute priorité : elle est dans le menu)
- À retirer :
  - les chiffres et l'histoire inventés ;
  - les 6 valeurs génériques ;
  - la vision « référence de l'océan Indien » ;
  - « Digita Marketing est née d'une passion commune ».
- À ajouter :
  - Anthony Legros (photo et texte de l'accueil) ;
  - l'approche (IA, automatisation, INES) ;
  - le statut d'entrepreneur individuel et Le Tampon ;
  - des liens vers /solutions, /services et /tarifs ;
  - les boutons Diagnostic gratuit et WhatsApp ;
  - un schéma Person/AboutPage.
- Style : passer des cartes Bootstrap blanches aux glass-cards de l'accueil ; coches vertes → accent.
- La meta description annonce « Notre méthode » : reprendre la section Méthode de l'accueil.

### /support
- La carte « Chat en direct » affiche `alert('Chat disponible prochainement')` alors que le chatbot fonctionne : à brancher sur le chatbot et WhatsApp.
- Documentation, vidéos et « Parcourir » pointent sur « # » : section à supprimer.
- À retirer : « < 2 h », « support prioritaire », les horaires inventés, « notre équipe », la FAQ sur les tickets.
- À ajouter : lien vers l'espace client, WhatsApp, données structurées FAQPage.
- Corps de page en blanc Bootstrap sous un héros premium : à harmoniser.

### /outils et les 4 outils
- Une couleur par outil (vert, jaune, rouge) : tout passer sur l'accent.
- CTA « Créer un projet » et « Nous contacter » : à remplacer par Diagnostic gratuit.
- Calculateur ROI :
  - « Profit net » ne déduit pas le budget : avec les valeurs par défaut, il affiche « Profit net 390 € » en vert à côté de « ROI −61 % » ;
  - le bouton diagnostic disparaît quand le résultat s'affiche en JS.
- Les erreurs affichent « Vérifiez votre clé API OpenAI » (message interne) : à remplacer.
- Ni fil d'Ariane ni lien retour vers /outils ; doublon de l'audit SEO avec /diagnostic.
- Code mort : route /outils déclarée deux fois, CSS `.outils-hero` inutilisé.

### /formations
- Décision à prendre : dépublier le catalogue fictif ou n'afficher que les formations réellement disponibles.
- Fiche : « 11 h de vidéo », « ressources téléchargeables » et « certificat » pour un contenu qui n'existe pas.
- Landing de formation :
  - le titre de l'onglet est écrasé (« Chatbot pour site web » sans « | DIGITA ») ;
  - le formulaire d'inscription gratuite poste vers une route qui n'existe pas ;
  - la page est indexable, en doublon de la fiche.
- Coquilles : « Intermediaire », « 1 inscrits ».
- Prix : 97 € en ligne contre 390 €/jour et 120 €/h dans le catalogue, sans explication.
- Étoiles du formulaire d'avis toutes pleines au départ.

### /tarifs
- À retirer :
  - les cartes Premium 2 990 € et Tunnel 1 490 € ;
  - « Le plus populaire » ;
  - « Support dédié 24/7 » ;
  - la FAQ sur le paiement échelonné.
- À aligner sur la grille : Business (5 pages, 15 jours), SEO, Logo (« dès 190 € »).
- À ajouter en cartes : l'Agent IA 24/7 (149-249 €/mois) et son essai de 14 jours, LP48 997 €, Landing 499 €. L'offre phare n'est aujourd'hui que dans le tableau.
- Idéalement, générer les cartes depuis `grille.py` et `solutions.py` pour qu'elles ne divergent plus.
- À ajouter : FAQPage en données structurées ; CTA Diagnostic gratuit et WhatsApp à la place de « Demander un devis ».

### /services
- Ton « prestige » : « Expertise Convergence », « projet prestige », « Diagnostic Stratégique ».
- CTA des cartes : « Demander un devis » vers /contact, à mener vers /diagnostic.
- SEO On-Page à 490 €/mois contre la grille SEO en forfait.

### /solutions
- Ajouter l'essai gratuit de 14 jours du Standardiste (CGV 5 bis) et WhatsApp.

### /catalogue
- 1 418 lignes de prix en dur qui contredisent `services_catalog.py`, « Plus de 300 services ».
- L'Agent IA et les Solutions sont absents.
- À générer depuis le catalogue ou à fusionner avec /services, puis rediriger.

### /boutique
- Produits fictifs (template 197 €, pack 349 €, suite d'outils 149 €, alors que les outils sont gratuits), badges inventés.
- Recommandation : suppression avec redirection 301, puis retrait du sitemap, de robots.txt, du footer et du menu agence.

### /contact
- Jargon et fausse équipe : « Nos experts », « orchestrateur d'agents », « Hub ».
- « Localiser le Hub » pointe sur « # ».
- La liste « Expertise » ne reprend pas les vraies offres (« Identité de Prestige », « Automatisation Cœur »).
- À ajouter : adresse, horaires, WhatsApp, lien vers /diagnostic, lien vers la politique de confidentialité dans la case RGPD.
- Bouton « Lancer l'Analyse » : à renommer « Envoyer mon message » (voir la section 3).

### /diagnostic
- Ajouter WhatsApp et un lien vers la politique de confidentialité sous le formulaire.
- Icônes en `text-blue`, une classe qui n'existe pas.

### Blog
- L'index n'affiche que 10 articles sur 407 : ajouter une pagination.
- Double fil d'Ariane sur les articles.
- Le lien auteur pointe vers /agent24-7 (noindex) : le diriger vers /a-propos.
- CTA vers /contact au lieu de /diagnostic.
- Jargon : « Mag Stratégique », « Omnicanal ».
- Barre des catégories navy, qui glisse sous la navbar.
- Pages catégorie et recherche dans l'ancien style Bootstrap.

### Pages légales (haute priorité, obligations légales)
- Cookies : décrit Google Analytics, une bannière de consentement et des vidéos, qui n'existent pas. Réalité : un cookie de session, deux réglages dans le navigateur (thème, chat), Google Fonts et les CDN. Date de 2025.
- Confidentialité : il manque le chatbot, le CRM INES, la prise de rendez-vous, le traitement par IA, Stripe, Google Fonts et les CDN.
- CGV :
  - le médiateur de la consommation n'est pas nommé (obligatoire) ;
  - aucune clause sur les abonnements mensuels (durée, résiliation) ;
  - aucune clause sur les formations numériques (rétractation) ;
  - les services d'IA et d'automatisation sont absents de la liste.
- Mentions légales :
  - ni SIRET ni mention de micro-entrepreneur ;
  - la phrase sur les cookies est inexacte ;
  - « tribunaux français » alors que les CGV disent Saint-Pierre.

### /projets/brief
- Estimations contraires aux tarifs.
- Jargon et fonctionnalités en anglais.
- Connexion obligatoire alors que la page est mise en avant.
- Prix affiché « 0.00 € ».
- Recommandation : renvoyer vers /diagnostic, ou réécrire la page et la rendre accessible sans compte.

### Connexion et inscription
- Pas de H1.
- Pas de lien vers les CGU et la politique de confidentialité à l'inscription.
- Jargon « compte WAO ».
- Le style des alertes rouges est forcé sur tout le site.

### Erreurs
- 500 en texte brut : il faut une page aux couleurs du site.
- La 404 ne propose ni /diagnostic ni /services.

### Header, footer, menus, chatbot
- Navbar : ajouter « Diagnostic gratuit » ; ordre proposé « À propos, Services, Solutions, Tarifs, Contact ».
- Menu agence :
  - accroche « Marketing Digital » à remplacer (IA et automatisation) ;
  - « Lancer un projet » à mener vers /diagnostic ;
  - lien Boutique à retirer.
- Barre de droite (57 icônes) :
  - 3e copie des prix en dur ;
  - icônes vertes et popups navy ;
  - l'Agent IA est absent.
- Footer :
  - à ajouter : WhatsApp, horaires, « EI, TVA non applicable » ;
  - à retirer : liens Boutique et Brief ;
  - « Espace membre » ici contre « Mon espace » dans le menu de l'accueil.
- Chatbot : ajouter « Diagnostic gratuit » et WhatsApp aux actions rapides.
- Modale « Executive Offer / Audit Flash Stratégique » : à renommer en Diagnostic gratuit, ou à retirer des pages publiques.

## 3. Bouton « Lancer l'Analyse » de /contact

Il ne lance aucune analyse. Il envoie le formulaire de contact :
1. Vérifications : jeton anti-falsification, limite d'envois, nom, e-mail valide et message obligatoires. Filtre anti-spam : champ piège invisible, envoi trop rapide après l'ouverture de la page, démarchage détecté, plus de 2 liens.
2. Le message est enregistré dans la table `contact_messages`, visible dans l'administration.
3. Il est copié dans le CRM INES, via l'agent d'acquisition 24/7. Celui-ci crée le contact et une affaire, prévient le propriétaire et envoie au prospect un premier message automatique. Un message classé spam devient une simple fiche CRM marquée « spam? », sans réponse. Un robot n'y va pas du tout.
4. Un e-mail de notification part vers l'adresse admin.
5. Le visiteur revient sur /contact#formulaire avec « Merci, votre message a bien été envoyé. Nous vous répondons sous 48 h. »

Le libellé est trompeur : remplacer par « Envoyer mon message ». La case « J'autorise l'analyse de ces données pour l'établissement de ma recommandation stratégique » est à réécrire avec un lien vers la politique de confidentialité.

## 4. Lots proposés

1. Vérité et légal : faux chiffres et fausse équipe, /a-propos réécrite, cookies, confidentialité, CGV (médiateur, abonnements), mentions.
2. Prix uniques : cartes /tarifs, /catalogue, barre de droite et brief générés depuis `grille.py`, `solutions.py` et `services_catalog.py` ; offres fantômes retirées.
3. Pages fictives : /boutique supprimée (301), décision sur /formations, /support nettoyé.
4. Conversion : Diagnostic gratuit et WhatsApp dans la navbar, le footer et toutes les pages ; /contact et /projets/brief réécrits.
5. Couleurs et style : palette d'accent unique, bleus retirés du thème sombre, héros homogènes, emojis retirés, pages Bootstrap passées au style premium.
6. Finitions : pagination du blog, fil d'Ariane, outils (ROI, messages d'erreur), 404/500, H1 des pages de connexion, données structurées FAQPage, Person et WebApplication.
