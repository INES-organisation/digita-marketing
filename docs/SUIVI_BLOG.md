# Suivi du blog : nouveaux articles

État au 9 novembre 2026 (types de contenu ajoutés, à déployer). Le plan éditorial (mots-clés, calendrier, structure d'un article, design) se trouve
dans le Claude Doc « Plan éditorial du blog DIGITA ». Ce fichier décrit ce qui a été fait dans le dépôt et
comment ajouter un lot.

## En ligne

30 articles publiés sur https://digita.buzz/blog, en 6 lots, tous fusionnés dans `main` et déployés :

| Lot | PR | Articles (slug) |
|---|---|---|
| 1 : Réalisations de l'accueil | #14 | `prix-site-internet-reunion`, `instagram-ou-facebook-reunion`, `budget-publicite-facebook-reunion`, `automatiser-devis-artisan`, `agent-ia-repondre-clients-24h` |
| 2 | #15 | `fiche-google-reunion`, `site-vitrine-ou-page-facebook`, `gite-reunion-haute-saison`, `repondre-clients-pendant-les-fetes`, `avis-google-entreprise` |
| 3 | #16 | `lexique-ia-tpe`, `saison-cyclonique-entreprise`, `chatgpt-tpe-usages`, `relances-automatiques-devis-factures`, `chatbot-whatsapp-entreprise` |
| 4 | #17 | `rgpd-tpe-essentiel`, `prise-rendez-vous-en-ligne`, `site-internet-artisan`, `boutique-en-ligne-reunion`, `temps-perdu-taches-repetitives` |
| 5 | #18 | `nom-de-domaine-entreprise`, `newsletter-tpe`, `idees-publications-reseaux-sociaux`, `landing-page-definition`, `page-facebook-piratee` |
| 6 | #20 | `bilan-digital-fin-annee`, `lexique-marketing-digital`, `audit-seo-lire-rapport`, `creer-logo-entreprise`, `facture-electronique-tpe` |
| 7 | #24 | `ecrire-pour-google-tpe`, `entretenir-securiser-site`, `accelerer-son-site`, `google-analytics-search-console`, `google-ads-tpe`, `plan-marketing-digital-une-page` |
| 8 | #25 | `photos-telephone`, `videos-courtes-telephone`, `choisir-crm`, `fideliser-clients`, `linkedin-dirigeant` |
| 9 | #26 | `createurs-contenu-reunion`, `marketplace-reunion`, `supports-imprimes-qr-codes`, `bad-buzz-local` |
| 10 | à venir | `accessibilite-site-internet` |

Les anciens articles (472 de l'ère PHP) ont été supprimés le 9 novembre 2026 (voir plus bas).

## Types de contenu (9 novembre 2026)

Chaque nouvel article a un type, défini dans `python/digita/content_types.py` et stocké dans la colonne
`blog_articles.content_type` (migration `database/migrations/2026_11_09_blog_content_type.sql`). Les anciens
articles restent sans type (`NULL`).

| Type (slug) | Libellé | Pour quoi | Articles actuels |
|---|---|---|---|
| `guide` | Guide | Tout comprendre sur un sujet | 11 |
| `pas-a-pas` | Pas à pas | Réussir une tâche précise | 10 |
| `comparatif` | Comparatif | Choisir entre deux ou trois options | 2 |
| `actualite` | Actualité | Ce qui change, et ce qu'il faut faire | 1 |
| `definition` | Définition | Comprendre un mot ou une notion | 3 |
| `modele` | Modèle | Checklist, modèle, calendrier prêts à l'emploi | 3 |

- Le type s'affiche en badge sur les cartes, en tête d'article et dans « Poursuivre la lecture », avec une
  couleur par type (classes `.blog-type--<slug>` dans `blog-layout.css`) : guide or, pas à pas vert,
  comparatif violet, actualité orange, définition turquoise, modèle rose. Les filtres de `/blog` reprennent
  la couleur du type.
- Les catégories sont en bleu partout (`.blog-cat`, pastilles de catégorie actives), comme le bouton « Voir
  les offres et tarifs » de l'accueil (`.v2-btn-blue`).
- « Poursuivre la lecture » propose d'abord des articles typés.
- `/blog` affiche des filtres par type (`/blog?type=guide`, seulement les types non vides, avec le nombre
  d'articles), puis les catégories. Un type inconnu redirige vers `/blog`.
- `/blog` liste d'abord les articles typés (les nouveaux), puis les anciens, 12 par page, avec pagination
  (`?page=2`, combinable avec `?type=`). La pagination des catégories est corrigée (le décalage était ignoré).
- Les cartes affichent la couverture quand elle est dans `/assets/images/blog/`.
- Dans l'admin, le formulaire d'article a un champ « Type de contenu ».
- Pour un nouveau lot : renseigner `"content_type"` dans `database/blog/articles.json`, `build_blog_sql.py`
  l'insère. Un test vérifie que chaque article a un type connu.

## Suppression des anciens articles (9 novembre 2026)

Décision d'Anthony le 9 novembre 2026 : le site n'a pas encore de visites, donc pas de référencement à
préserver. Le blog ne garde que des articles utiles et clairs, sans article archivé ni redirection.

- La migration `database/migrations/2026_11_09_blog_suppression_anciens_articles.sql` supprime les 472
  anciens articles (sans type) et les redirections qui menaient vers eux. Les articles du plan éditorial sont
  protégés par leur slug.
- Une sauvegarde est faite sur le serveur juste avant : `/opt/digita/backups/blog_avant_suppression_2026-11-09.sql`.
- Les anciennes adresses répondent 404.
- Mise en ligne faite le 9 novembre 2026 (commit dae991f) : 164 redirections et 472 articles supprimés,
  il reste 30 articles, tous publiés et typés. Sauvegarde de 1,6 Mo vérifiée avant la migration.
- Lots 7 et 8 mis en ligne le 9 novembre 2026 (commit a82f079) : 41 articles publiés, tous typés.
- Les 16 sujets utiles repérés dans les anciens articles sont réécrits comme nouveaux articles (lots 7 à 9).

## Règles de rédaction

- **Aucun client cité, aucun chiffre inventé.** Les exemples sont des cas fictifs, et le titre de leur encadré
  commence par « Exemple (cas fictif) ». « Nos clients » est interdit. Un encadré « à adapter » (modèle,
  structure type) ne commence pas par « Exemple ».
- **Sources officielles vérifiées** dans le bloc « Sources » en fin d'article : Service Public Entreprendre,
  CNIL, Cybermalveillance.gouv.fr, 17Cyber, Afnic, Météo-France, aides Google et Meta, etc. Pas de chiffre
  sans source.
- **Tarifs DIGITA** repris uniquement de `python/digita/grille.py` et `python/digita/solutions.py`, avec la
  mention « Grille tarifaire DIGITA : page Tarifs, consultée le … ».
- **Pas de promesse non vérifiée sur les pratiques de DIGITA**, par exemple « le domaine est toujours déposé
  à votre nom ». On décrit ce que l'offre contient, rien de plus.
- **Sujets écartés pour l'instant** : Kap Numérik (à vérifier), l'étude de cas du logo (accord du client
  nécessaire), le financement des formations IA (les fonds exigent Qualiopi, que DIGITA n'a pas). Le logo est
  traité au lot 6 comme une méthode générale, avec un exemple fictif, sans parler d'un projet réel.
- **Sujets réglementaires** (facture électronique, RGPD) : uniquement ce que disent impots.gouv.fr, Service
  Public Entreprendre ou la CNIL, et renvoi vers l'expert-comptable pour les cas particuliers (par exemple les
  règles propres aux départements d'outre-mer, non confirmées par les pages officielles lues).
- **Auteur** : Anthony Legros, avec la photo de la page `/agent24-7`
  (`/assets/images/v2/fondateur-anthony-legros.webp`). Il est défini dans `AUTHOR` de
  `python/digita/routes/blog.py` et repris dans les données structurées `BlogPosting`.

## Structure d'un article

Le corps HTML est dans `database/blog/<slug>.html`. Les métadonnées (titre, `meta_title` ≤ 60 caractères,
`meta_description` ≤ 160, extrait, catégorie, pôle, icône, titre du visuel) sont dans
`database/blog/articles.json`. L'ordre des blocs :

1. `en-bref` : trois points à retenir ;
2. une accroche concrète, puis au moins quatre `h2`, avec des tableaux `table-article` et des listes
   `checklist` ou `etapes` ;
3. des encadrés `encadre-exemple` (cas fictif ou modèle à adapter) ;
4. l'encadré `encadre-digita` « Ce que fait DIGITA », avec le prix et des liens vers `/services#…`,
   `/solutions#…` ou `/diagnostic`. Ancres existantes : `sites-web`, `seo`, `ia-automation`, `ecommerce`,
   `publicite`, `reseaux-sociaux`, `email-marketing` ;
5. « Questions fréquentes » en `h3` ;
6. `article-sources` : les sources, ou « Pour aller plus loin » avec des liens internes.

## Page article

Gabarit `python/digita/templates/app/Views/blog/show-content.html`, styles `public/assets/css/blog-layout.css`.

- Image à la une, bloc auteur, sommaire généré à partir des `h2` et `h3`, partage, « Poursuivre la lecture ».
- **Sommaire toujours visible** (lot 5) :
  - sur ordinateur (≥ 992 px), il reste collé dans la colonne de droite (`article-sidebar-sticky`), avec la
    carte diagnostic en dessous. La section en cours est mise en évidence et la liste défile seule si elle
    est longue ;
  - sur mobile et tablette, un bouton « Sommaire » flottant (`toc-flottant`) apparaît en bas à gauche dès que
    le sommaire du début d'article sort de l'écran. Il affiche la section en cours et ouvre la liste ;
  - « À lire aussi » n'est plus dans la colonne sur ordinateur, pour laisser la place au sommaire.

## Ajouter un lot

Depuis `python/` :

1. Écrire `database/blog/<slug>.html` et ajouter l'entrée dans `database/blog/articles.json`.
2. Couverture 1200 × 630 : `node tools/blog_covers.js`, lancé depuis un dossier de travail, génère
   `cover-<slug>.png` pour chaque article (fond noir, anneaux dorés, icône Bootstrap, titre du visuel).
   Convertir ensuite en WebP qualité 82 (Pillow) dans `public/assets/images/blog/<slug>.webp`.
3. SQL : `python tools/build_blog_sql.py ../database/migrations/<date>_blog_articles_lotN.sql <slug> …`.
   Les articles sont insérés en brouillon (`ON CONFLICT (slug) DO NOTHING`). La catégorie doit exister dans
   `service_categories` (catégories utilisées jusqu'ici : `creation-web`, `seo`, `reseaux-sociaux`, `publicite-en-ligne`,
   `intelligence-artificielle`, `crm`), sinon l'article n'a pas de catégorie. Si un article contient « % »,
   `tools/apply_sql.py` échoue (psycopg2 lit « % » comme un paramètre) : appliquer le fichier avec `psql -f`,
   comme sur le serveur.
4. Tests : `python -m pytest -q` (141 tests au lot 9). `tests/test_blog.py` vérifie les longueurs des metas, la couverture, les
   `h2`, « En bref », les sources, l'absence de lignes vides et la mention « fictif » des exemples.
5. PR, validation d'Anthony, fusion.
6. Mise en ligne sur le VPS (`ssh ines-vps`, depuis l'iMac) :

```
ssh ines-vps 'bash -s' <<'EOF'
set -e
cd /opt/digita && git checkout main && git pull
docker compose -f python/deploy/docker-compose.yml --env-file /opt/ines/.env.production --env-file python/deploy/.env up -d --build
docker exec -i ines-postgres psql -v ON_ERROR_STOP=1 -U digita -d digita < database/migrations/<date>_blog_articles_lotN.sql
docker exec ines-postgres psql -v ON_ERROR_STOP=1 -U digita -d digita -c "UPDATE blog_articles SET status='published', published_at=NOW() WHERE status='draft' AND slug IN ('…')"
EOF
```

La reconstruction est nécessaire, parce que les images et les gabarits sont dans l'image Docker. Ne pas
utiliser `--remove-orphans` : les conteneurs `multiproshop-web` et `multiproshop-worker` sont signalés comme
orphelins mais doivent rester.

Le mode auto de Claude Code sur l'iMac peut refuser `ssh ines-vps`, parce que la commande touche la
production. Dans ce cas, il faut une règle de permission Bash pour `ssh ines-vps` dans les réglages de
Claude Code, ou lancer le bloc à la main.

## Reste à faire

- Offres INES dans les articles (avis donné à Anthony le 9 novembre 2026) : seulement dans l'encadré « Ce que
  fait DIGITA », seulement quand l'outil répond au sujet, jamais classé dans un comparatif, et seulement une
  offre présente dans la grille avec son prix. Aujourd'hui aucune offre INES seule n'y figure : ne pas la citer.

- Calendrier : après le lot 6, tous les sujets du plan éditorial sont traités, sauf Kap Numérik et le
  financement des formations. Les prochains lots demandent de nouveaux sujets.
- Rédiger les 16 nouveaux sujets : les 16 sont écrits. Le dernier, l'article sur l'accessibilité
  (lot 10, `accessibilite-site-internet`), s'appuie sur la fiche DGCCRF du 13 novembre 2025 collée par Anthony
  le 9 novembre 2026, les pages officielles refusant la lecture depuis le serveur de travail.
- Idées d'articles sur des outils INES (9 novembre 2026), en attente du choix d'Anthony : devis depuis le
  téléphone, click & collect, réservations sans commission, planning et rapports d'intervention, QR codes, page
  de liens, carte de visite et signature e-mail, sondages, messagerie unique. Aucun n'a encore d'offre ni de prix
  dans la grille : vérifier dans INES qu'il fonctionne, puis ne citer INES qu'une fois l'offre créée. : voir le Claude Doc « Plan de contenu : articles d'origine et
  formations ».
- Google Search Console : sitemap et suivi des clics par article vers `/diagnostic`.
- Photos réelles de La Réunion pour remplacer ou compléter les couvertures générées.
