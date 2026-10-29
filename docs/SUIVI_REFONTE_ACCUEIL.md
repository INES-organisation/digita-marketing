# Suivi — Refonte de l'accueil et du positionnement (analyse Synaps)

**Ouvert le :** 28/10/2026
**Objectif :** une page d'accueil qui dit en 5 secondes ce que DIGITA vend, à qui et à quel prix, avec des preuves vérifiables et un design sobre et rapide ; puis le même design sur les pages internes.
**Page de travail :** `/accueil-v2` (`noindex`, absente du sitemap), qui remplacera `/` à la fin (lot 6).
**Lié à :** [PLAN_ACTION_OPTIMISATION_IA_SEARCH.md](PLAN_ACTION_OPTIMISATION_IA_SEARCH.md), [ACCROCHES_TAGLINES_SEO.md](ACCROCHES_TAGLINES_SEO.md) §0 (règles de rédaction), [AUDIT_SITE_2026-10.md](audits/AUDIT_SITE_2026-10.md), [SUIVI_CONNEXION_INES.md](SUIVI_CONNEXION_INES.md) §3 (offres)

---

## 1. Point de départ : ce qu'on retient de synaps.re (analysé le 28/10/2026)

| Levier Synaps | Ce que DIGITA en fait |
| --- | --- |
| Une promesse en une phrase, une offre d'entrée sans risque (site à 49 €, payé s'il plaît), puis des abonnements (10 €, 79 €/mois) | Promesse « réponse 24/7 », essai sans risque sur le Standardiste (D1, D2). **On ne copie pas le prix à 49 €** : DIGITA vise des PME dont un prospect vaut cher. |
| « Vous en êtes où ? On part de là. » : 3 situations | Section « On part de votre situation » (3 portes : messages, acquisition, site). |
| Le prix bas expliqué (l'IA fait gagner du temps) | Section « Le calcul » : 168 h contre 35 h, un contrat qui paie l'abonnement. |
| Un visage et une histoire (Loïc) | Bloc fondateur (D4). |
| Preuves précises : clients nommés, scores, chiffres réels du compte pub | Réalisations existantes + chiffres réels d'INES (D5, D6). |
| L'IA a un nom (« Phénomène », une freelance sur WhatsApp) | Nommer l'agent (D10). |
| Guides de décision (« combien coûte… », « Synaps vs Wix ») et page « vous payez déjà un abonnement ? » | Lot 3. |
| Palette réduite (papier, encre, un accent), 2 polices hébergées, animations qui montrent le produit, site statique léger | Design system v2 (lot 1). |

**Écart avec ma première analyse :** j'avais recommandé `llms.txt` et des versions `.md` des pages. Le plan IA Search (§2) rappelle que Google les ignore. Ils restent utiles au mieux pour d'autres assistants : priorité basse (D13).

## 2. Décisions à prendre

Recommandation en gras. Toutes les décisions ont été prises le 29/10/2026 (dernière colonne).

| # | Sujet | Options | Recommandation | Décision |
| --- | --- | --- | --- | --- |
| D1 | Promesse principale de l'accueil | (a) agent IA 24/7 qui répond, qualifie et pose le RDV ; (b) agence globale (site, réseaux, pub, IA) comme aujourd'hui | **(a)**. Les autres services restent accessibles, mais l'accueil vend une seule chose. H1 provisoire : « Chaque prospect reçoit une réponse. Même à 23 h. » | ✅ 29/10 : (a) |
| D2 | Offre d'entrée sans risque | (a) essai 14 jours du Standardiste, mise en service payée seulement si l'agent a pris au moins un RDV ; (b) mise en service remboursée sous 30 jours ; (c) rien de plus que le diagnostic gratuit | **(a)**. Coût réel pour DIGITA : le temps de paramétrage, et INES le réduit. Conditions à écrire dans les CGV. | ✅ 29/10 : (a), CGV art. 5 bis |
| D3 | Mention fiscale des prix | /tarifs dit « TVA non applicable, art. 293 B » alors que /solutions et `solutions.py` affichent « HT » | **Une seule mention.** En franchise : retirer « HT » partout. Assujetti : corriger la FAQ de /tarifs. **À trancher selon votre statut réel : risque juridique.** | ✅ 29/10 : TVA non applicable, art. 293 B → « HT » retiré partout |
| D4 | Visage du fondateur | Photo, prénom, parcours en 5 lignes, sur l'accueil et sur /a-propos | **Oui.** Une vraie photo, pas d'image générée (plan IA §4, règle 1). Contenu à fournir par vous. | ✅ 29/10 : photo et texte fournis (`images/fondateur/`) |
| D5 | Chiffres des réalisations déjà en ligne (« ≈ 40 min gagnées par dossier », « ÷ 5 erreurs », « ≈ 2 min de délai de rappel », « ≈ 0 lead non traité », « 100 % », « ÷ 3 ») | Garder avec une source, ou retirer | **Garder seulement ceux qui ont une source** (export, déclaration client), conformément à ACCROCHES §0.2. Demander aux clients l'autorisation d'être nommés et cités. | ✅ 29/10 : lancement, aucune référence client ; seule preuve : INES |
| D6 | Chiffres réels d'INES à publier | Délai de première réponse, part des messages hors heures de bureau, RDV pris, sur les comptes DIGITA et clients | **Oui, dès 30 jours de données.** C'est l'équivalent des « 92 050 personnes touchées » de Synaps. | ✅ 29/10 : oui, après 30 jours de données |
| D7 | WhatsApp | Le 06 93 48 78 17 est-il joignable sur WhatsApp (Business) ? | **Oui si possible** : lien `wa.me` pré-rempli par offre. Sinon, on retire le bouton. | ✅ 29/10 : oui |
| D8 | Thème | (a) clair par défaut, sombre selon le réglage de l'appareil (fait sur la page v2) ; (b) sombre uniquement, comme aujourd'hui | **(a)**. Or et marine conservés pour la continuité de marque ; or réservé aux boutons et accents. | ✅ 29/10 |
| D9 | Polices | Bricolage Grotesque (titres) + Instrument Sans (texte), hébergées sur le site (71 Ko en tout) ; remplacent Plus Jakarta Sans, Inter, Outfit et Kaushan Script | **Valider.** | ✅ 29/10 |
| D10 | Nom de l'agent | Un prénom ou un nom de personnage pour l'agent INES côté clients | **Oui** : on parle à quelqu'un, pas à un logiciel. Nom à choisir (court, prononçable, disponible en .re et .fr si on veut une page dédiée). | ✅ 29/10 : **INES** |
| D11 | Formations, boutique, blog | Sortir formations et boutique de la navigation principale ; `noindex` des fiches de formation minces (382 fiches au même modèle) ; réécrire les 10 à 20 qui comptent | **Oui**, aligné sur le plan IA Search, phase 2 (*scaled content abuse*). | ✅ 29/10 : à faire (lot 4.6) |
| D12 | Place du site vitrine 974 (990 €) | Offre principale ou porte secondaire | **Porte secondaire** (3e situation de l'accueil). | ✅ 29/10 |
| D13 | `llms.txt` et versions `.md` | Faire ou non | **Non pour l'instant** (ignorés par Google, voir §1) ; à revoir au lot 5. | ✅ 29/10 : non |
| D14 | Chatbot sur la nouvelle accueil | Absent de la page v2 pour l'instant | **Le remettre, restylé v2, comme démo en direct** : « écrivez à notre agent maintenant ». C'est la preuve que Synaps ne peut pas donner. | ✅ 29/10 : fait |
| D15 | Date de bascule de `/` | — | Après les lots 1 à 3 et les décisions D1 à D5 ; pas un vendredi. | ✅ 29/10 : après les lots 2 et 3 |

## 3. Plan et avancement

### Lot 1 — Design system et page de travail

| # | Tâche | Statut |
| --- | --- | --- |
| 1.1 | Feuille `public/assets/css/v2.css` : jetons de couleur (clair et sombre), 2 polices variables hébergées et préchargées, espacements fluides, aucune dépendance (ni Bootstrap, ni AOS, ni Google Fonts), animations désactivées si « réduire les animations » | ✅ 28/10 |
| 1.2 | Route `/accueil-v2` (`pages.home_v2`, gabarit `templates/home-v2.html`) : `noindex, nofollow`, canonical vers `/`, absente du sitemap, bandeau « version de travail » | ✅ 28/10 |
| 1.3 | Sections : hero + conversation animée (Messenger 23 h 14 → RDV posé → fiche CRM), 3 situations, le calcul, les 3 offres (données de `solutions.OFFERS`, pas de copie), 4 étapes, garantie (à valider), réalisations (`realisations.py`), fondateur (à compléter), FAQ, appel final | ✅ 28/10 |
| 1.4 | Données structurées : `ProfessionalService` (téléphone, zone La Réunion, offres) et `FAQPage` générée depuis `HOME_V2_FAQ` | ✅ 28/10 |
| 1.5 | Test `test_home_v2_draft_is_noindex_and_uses_real_offers` (noindex, un seul H1, offres réelles, aucun chiffre interdit, aucune dépendance lourde, FAQPage, absente du sitemap) | ✅ 28/10 |
| 1.6 | Vérifié en local : capture 1440 px et 390 px, aucun débordement horizontal, contenu visible sans JavaScript | ✅ 28/10 |
| 1.7 | Logo : WebP de 18 Ko (`images/v2/logo-digita.webp`) sur fond clair, logotype en texte sur fond sombre (lettres noires du logo) ; SVG à venir | ⚠️ SVG à fournir |
| 1.8 | Image de partage 1200×630 dédiée | ⏳ |
| 1.9 | Images du dossier réorganisé (`identite/`, `fondateur/`, `réalisations/`, `contenu/`) : versions web dans `images/v2/` (fondateur 27 Ko, lettrage et logo INES 8 à 9 Ko) ; `digita.png` (favicon, icône du menu, logo des données structurées) ramené de 2,4 Mo à 337 Ko en 1024 px, l'original reste dans `identite/logo.png` ; chemins de `hero-bg.svg`, `pattern.svg` et `placeholder-blog.svg` mis à jour (déplacés dans `contenu/`) | ✅ 29/10 |
| 1.10 | Chatbot sorti du layout : `includes/partials/chatbot.html` + `assets/js/chatbot.js`, partagé par toutes les pages et la v2 (style v2 dans `v2.css`) ; il se présente comme INES (accueil et consigne de l'IA) | ✅ 29/10 |

### Lot 2 — Contenu et offres (après D1, D2, D3, D7, D10, D12)

| # | Tâche | Statut |
| --- | --- | --- |
| 2.1 | Fixer le H1 et le sous-titre ; reporter dans ACCROCHES §18 | ✅ H1 en place sur la v2 ; ⏳ report dans ACCROCHES à la bascule |
| 2.2 | Rédiger l'offre d'essai et l'ajouter aux CGV ; retirer l'encadré « à valider » | ✅ 29/10 : CGV art. 5 bis (`#essai-standardiste`), section « L'essai » et question dans la FAQ |
| 2.3 | Une seule mention fiscale dans `solutions.py`, /tarifs, /solutions, la FAQ et le chatbot | ✅ 29/10 (la facture garde « Sous-total », sans TVA) |
| 2.4 | /tarifs refait autour de l'escalier d'offres (Standardiste → Commercial IA → Machine à Leads, puis site et services à la carte) ; « Starter 490 € = logo » retiré du premier plan | ⏳ |
| 2.5 | Relecture « sans jargon » des pages publiques : supprimer « orchestration totale », « scalabilité native », « DSI/CMO externalisé », « gouvernance des données », « pilotage OKR » | ⏳ |
| 2.6 | Liens WhatsApp pré-remplis par offre | ✅ 29/10 (v2) ; ⏳ /solutions au lot 5 |
| 2.7 | Nom de l'agent dans la page, le chatbot et les messages INES | ✅ 29/10 (page v2, chatbot) |

### Lot 3 — Preuves et contenu de décision (après D4, D5, D6)

| # | Tâche | Statut |
| --- | --- | --- |
| 3.1 | Bloc fondateur (accueil) + page /a-propos réécrite à la première personne, avec photo et données `Person` | ✅ bloc v2 ; ⏳ /a-propos et `Person` |
| 3.2 | Études de cas : la première sera INES elle-même (DIGITA comme client) ; les clients viendront avec les premiers projets | ⏳ |
| 3.3 | Chiffres réels d'INES sur l'accueil, avec date et périmètre | ⏳ après 30 jours de données (fin novembre 2026) |
| 3.4 | Avis Google affichés avec lien vers la fiche | ⏳ |
| 3.5 | Guides de décision (un par mois, signés, datés) : « Combien coûte un standardiste à La Réunion ? », « Standardiste IA ou secrétaire : le vrai calcul », « Lead Ads à La Réunion : coût par prospect », « Permanence téléphonique ou agent IA » | ⏳ |
| 3.6 | Pages « vous payez déjà pour ça ? » (permanence téléphonique, Calendly + Zapier, CRM sous-utilisé) et pages métier (BTP, pompes à chaleur et solaire, immobilier, instituts) : rédigées à la main, pas de pages clonées | ⏳ |

### Lot 4 — SEO technique et IA Search (plan IA Search, phases 1, 2, 4, 5)

| # | Tâche | Statut |
| --- | --- | --- |
| 4.1 | Méga-menu des pages internes : remplacer ses 14 couples h2/h3 (lus avant le H1 sur chaque page) par des éléments non-titres | ⏳ |
| 4.2 | Fenêtre « Diagnostic » de l'accueil actuel : son h3 est le premier titre de la page (disparaît avec la bascule) | ⏳ lot 6 |
| 4.3 | Retirer AOS des pages internes (contenu masqué tant qu'on n'a pas défilé, plan IA phase 1) | ⏳ |
| 4.4 | `BreadcrumbList` sur les pages internes, `Service` + `Offer` sur /solutions, `FAQPage` sur /tarifs | ⏳ |
| 4.5 | Search Console : vérifier l'option « Inclure… dans les fonctionnalités d'IA générative », brancher le suivi des impressions IA | ⏳ accès Search Console |
| 4.6 | `noindex` des fiches de formation minces, réécriture des 10 à 20 prioritaires | ⏳ D11 |
| 4.7 | Mesure avant/après : PageSpeed mobile (LCP, INP, CLS), poids de page, de l'accueil actuel et de la v2 | ⏳ (quota PageSpeed épuisé le 28/10) |

### Lot 5 — Pages internes au design v2

| # | Tâche | Statut |
| --- | --- | --- |
| 5.1 | Nouveau layout commun (en-tête, pied de page) sur `v2.css`, sans Bootstrap | ⏳ |
| 5.2 | Migration dans l'ordre : /solutions, /tarifs, /diagnostic, /a-propos, /contact, puis services, blog, formations | ⏳ |
| 5.3 | Chatbot restylé v2 (D14) | ⏳ |
| 5.4 | Suppression des CSS devenus orphelins (`premium-preview.css`, `layout-premium.css`, `theme-accents.css`…) | ⏳ |

### Lot 6 — Bascule de l'accueil

| # | Tâche | Statut |
| --- | --- | --- |
| 6.1 | `/` sert `home-v2.html` : retirer le bandeau et les encadrés « à valider », passer en `index, follow` | ⏳ |
| 6.2 | `/accueil-v2` redirige en 301 vers `/` | ⏳ |
| 6.3 | Mettre à jour les tests de l'accueil (`test_home_hero_without_unsourced_figures`, `test_home_uses_vertical_menu_anchored_on_sections`) | ⏳ |
| 6.4 | Grille de contrôle du plan IA Search (§4) passée sur la nouvelle accueil | ⏳ |
| 6.5 | Déploiement, vérification en production, demande d'indexation dans Search Console | ⏳ |

## 4. Règles pour toute la refonte

1. Aucun chiffre de résultat sans source ; aucun superlatif (ACCROCHES §0.2).
2. Les prix viennent des fichiers de données (`solutions.py`, `realisations.py`, `services_catalog.py`), jamais recopiés à la main dans un gabarit.
3. Une encre, un fond, un accent. Pas de verre dépoli, de particules, d'émojis dans les titres ni de nouvelle police.
4. Une animation doit montrer le produit (un message, un RDV posé), pas décorer. Le contenu reste lisible sans elle.
5. Mots du client, pas jargon : « répondre à vos messages », pas « orchestration des flux ».

## 5. Journal

| Date | Fait |
| --- | --- |
| 28/10/2026 | Analyse de synaps.re ; ouverture du suivi ; lot 1 (1.1 à 1.6) : design system v2, page `/accueil-v2`, test. |
| 29/10/2026 | Toutes les décisions prises. « HT » retiré (art. 293 B) ; essai de 14 jours dans les CGV ; agent nommé INES ; WhatsApp par offre ; bloc fondateur et section INES ; chatbot partagé et restylé ; chiffres non sourcés retirés de `realisations.py` (D5). Déployé en aperçu sur `/accueil-v2`. |

## 6. Points ouverts

- **Nom affiché du fondateur** : « Anthony Legros », tiré du nom du fichier photo. À confirmer (ou « Tony Legros »).
- **Accueil actuel** : les projets « TTC France », « TTC Sales », « TatooModel » et « Lurel » y restent affichés (sans leurs chiffres). D5 dit qu'il n'y a pas encore de référence client : à confirmer s'il faut les retirer avant la bascule.
- **Logo SVG** à fournir (1.7).
