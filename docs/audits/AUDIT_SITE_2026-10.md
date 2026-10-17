# Audit du site digita.buzz — octobre 2026

Audit réalisé le 17/10/2026 avec Playwright (Chromium) sur le site en ligne : 34 pages types
(pages fixes, outils, blog, formations, recherche, connexion, pages légales, 404), en
ordinateur (1440 px) et mobile (390 px). Mesures : statut HTTP, temps de chargement, balises SEO,
données structurées, erreurs JavaScript, ressources en échec, images, formulaires, débordement mobile.
Les corrections marquées ✅ sont faites dans la PR « Coque unique, formulaires réparés, thème clair ».

## 1. À corriger en priorité (bloquant ou visible par tous)

| # | Constat (mesuré sur le site en ligne) | Statut |
|---|---|---|
| 1 | **Pas de pied de page** sur toutes les pages sauf l'accueil (28 pages sur 29) : le layout `main` l'avait perdu lors de la refonte d'avril. | ✅ pied de page premium partout |
| 2 | **Trois en-têtes différents** : barre latérale premium sur l'accueil, ancienne barre blanche + menu « agence » ailleurs, ancien header PHP sur connexion, inscription, recherches et 404. | ✅ une seule navigation (barre latérale, menu coulissant sur mobile) |
| 3 | **Formulaire de contact inopérant** : `POST /contact` répond 404, les messages étaient perdus (déjà le cas en PHP). | ✅ enregistré en base, copié dans le CRM INES, notifié à l'admin |
| 4 | **Newsletter inopérante** : le formulaire du pied de page de l'accueil envoyait vers `/newsletter/subscribe`, route inexistante (404). | ✅ inscription en base + INES, réponse sans rechargement |
| 5 | **Accueil illisible sur mobile** : la barre latérale de 260 px recouvrait le contenu (aucune règle mobile). | ✅ barre supérieure + menu coulissant |
| 6 | **Connexion / inscription sans mise en forme** (formulaire collé en haut, sous la barre). | ✅ intégrées au thème |
| 7 | **Page 404 brute** (texte « Page non trouvée » sans design) pour toute URL inconnue ; `/portfolio` et `/equipe` affichaient « Une erreur est survenue ». | ✅ vraie page 404 (noindex) ; portfolio/équipe renvoient vers « À propos » |
| 8 | **Erreur JavaScript sur l'accueil** (`Cannot read properties of null (reading 'classList')`) venant de `main.js`, plus un code de débogage qui dessinait « DEBUG CANVAS OK ». | ✅ script retiré |
| 9 | **Image manquante sur /blog** (`placeholder-blog.jpg`, 404 ×5) : aucun des 472 articles n'a d'image. | ✅ visuel de remplacement ; ⚠️ images d'articles à produire |
| 10 | **Partages réseaux sociaux des formations** vers `http://digita-marketing.local/...`. | ✅ URL du site |
| 11 | Débordement horizontal sur mobile (/a-propos, articles, /projets/brief). | ✅ disparu avec l'ancienne barre |
| 12 | **Mentions légales fictives** : SIRET 123 456 789 00012, « 123 Rue du Marketing, Paris », hébergeur « [Nom de l'hébergeur] », directeur « [Nom du directeur] ». Obligation légale (LCEN). | ✅ remplacées par les vraies informations (EI TONY ALPHA 8.0, SIREN 844 384 198, hébergeur OVH) |
| 13 | **Téléphone factice** « +262 692 XX XX XX » sur /contact et /support ; e-mail `contact@digita-marketing.com` (domaine différent de digita.buzz). | ✅ vrais téléphone et e-mail |

## 2. SEO

| Constat | Statut |
|---|---|
| L'accueil n'avait **ni meta description, ni canonical, ni Open Graph, ni JSON-LD** (son layout ignorait `metaDescription`). | ✅ l'accueil passe par le layout commun |
| Connexion, inscription, recherches : titre générique « Digita Marketing Digital », sans description. | ✅ titres dédiés, `noindex` |
| `<title>` non échappé (le titre des recherches contient la requête du visiteur). | ✅ échappé |
| Paramètre `?v=time()` sur chaque CSS : aucun cache navigateur possible. | ✅ version fixée au démarrage |
| Sitemap OK (903 URL, calculé à la demande), robots.txt OK (commentaire d'ancien domaine corrigé). | ✅ |
| **Contenu dupliqué** : 382 formations au même prix (297 €), même durée, descriptions générées sur le même modèle (« Formation complète pour maîtriser X de A à Z »), 2 inscrits au total. Risque de contenu jugé pauvre par Google. | ⚠️ réécrire les fiches prioritaires, regrouper ou désindexer le reste |
| 472 articles sans image : pas de miniature dans Google Discover ni sur les réseaux. | ⚠️ générer des visuels (l'IA INES peut aider) |
| Pas de `BreadcrumbList` / `FAQPage` sur les pages fixes ; FAQ de /contact sans schéma. | à ajouter |
| Image Open Graph = logo carré 350 Ko. | créer une image 1200×630 dédiée |
| Pas de Google Search Console ni d'outil de mesure déclaré dans le code. | à brancher |

## 3. Design et expérience

- ✅ Thème clair retrouvé dans l'historique (palette d'avant la refonte du 20/04/2026 : fond `#f7f7f7`, texte `#1f2937`, bleu `#2563eb`) et proposé en bascule à côté du thème sombre ; le choix est gardé dans le navigateur.
- ✅ Chatbot aux couleurs de la marque (il était bleu Bootstrap) et adapté au mobile.
- Les pages internes mélangent encore deux générations de contenu : sections sombres « premium » (services, contact, accueil) et blocs blancs Bootstrap de l'ère PHP (formations, blog, tarifs, boutique, solutions). Harmoniser le contenu des pages formations/blog/boutique avec le style premium.
- Animations AOS : tout le contenu de /services est caché tant que la page n'a pas défilé ; sur une capture ou un robot, la page paraît vide sous le titre.
- Émojis dans les H1 (« 🎓 Formations Digita », « 🛒 Boutique ») : peu cohérent avec le positionnement « cabinet premium ».
- Accessibilité : 4 à 10 champs sans libellé associé par page (modal d'audit, recherches). Corrigé sur le formulaire de contact ; reste le modal « Diagnostic » et les champs de recherche.
- Logo en PNG de 200 Ko chargé sur chaque page : passer en SVG ou WebP.

## 4. Formulaires de bout en bout

| Formulaire | État |
|---|---|
| Diagnostic / audit (modal, toutes pages) → `/api/audit-request` | fonctionne (base + INES + e-mails) |
| Contact → `/contact` | ✅ réparé |
| Newsletter (pied de page) | ✅ réparé, présent sur toutes les pages |
| Brief projet → `/projets/brief` | fonctionne |
| Connexion / inscription | fonctionnent ; après connexion tout utilisateur est envoyé vers `/admin/dashboard` (à vérifier pour un élève) |
| Recherche boutique (`/boutique/search`) et solutions (`/solutions/search`) | **404** : routes inexistantes, à créer ou retirer |
| Inscription à une formation : 3 formulaires visent `/formations/enroll/:id` | **route inexistante** (la vraie est `/formations/:slug/inscription`), à corriger |
| Outils gratuits (audit SEO, meta, ROI, calendrier) | fonctionnent |

Les envois réels n'ont pas été testés sur la production (pour ne pas créer de faux prospects dans
INES) ; contact et newsletter ont été testés de bout en bout sur une copie locale de la base.

## 5. Contenu à ajouter pour un site complet

1. ✅ Mentions légales, CGV, politique de confidentialité et factures mises à jour avec les vraies informations de l'entreprise.
2. **Bandeau cookies** : la politique cookies existe mais aucun consentement n'est demandé.
3. **Portfolio / études de cas** : des visuels clients existent dans le dépôt (`mps.png`, `poly.png`, `neomea.png`) mais ne sont pas utilisés ; `/portfolio` n'a jamais existé.
4. **Page équipe** (`/equipe` n'a jamais existé) et photos réelles.
5. **Preuves sociales vérifiables** : les chiffres « +250 clients », « x2,5 ROI », le témoignage « Thomas M., CEO » et « 3 créneaux disponibles cette semaine » sont affichés sans source ; à remplacer par de vrais avis (Google, LinkedIn).
6. **Réseaux sociaux** : liens retirés du pied de page car ils pointaient vers « # » ; à remettre avec les vraies URL.
7. Pages services détaillées (une page par expertise) pour le référencement local « La Réunion ».

## 6. Technique et performance

- Temps de réponse serveur bon (0,3–0,5 s pour les pages internes, 2,1 s pour l'accueil avec ses ressources).
- ✅ Bibliothèques chargées sans être utilisées retirées (GLightbox, Swiper, Isotope).
- ✅ ~165 fichiers obsolètes supprimés (ancien header/footer/menus, CSS et JS orphelins, images en double, ~100 notes de l'ère PHP).
- En-têtes de sécurité : HSTS, `nosniff`, `X-Frame-Options` présents ; pas de `Content-Security-Policy` ni `Referrer-Policy`.
- Fichiers statiques : gzip et cache 30 jours OK.
- `database/production_data*.sql` (exports avec données réelles) restent versionnés : à sortir du dépôt si celui-ci n'est pas strictement privé.
