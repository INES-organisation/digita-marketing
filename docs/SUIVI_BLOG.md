# Suivi du blog : nouveaux articles

État au 8 novembre 2026. Le plan éditorial (mots-clés, calendrier, structure d'un article, design) se trouve
dans le Claude Doc « Plan éditorial du blog DIGITA ». Ce fichier décrit ce qui a été fait dans le dépôt et
comment ajouter un lot.

## En ligne

25 articles publiés sur https://digita.buzz/blog, en 5 lots, tous fusionnés dans `main` et déployés :

| Lot | PR | Articles (slug) |
|---|---|---|
| 1 : Réalisations de l'accueil | #14 | `prix-site-internet-reunion`, `instagram-ou-facebook-reunion`, `budget-publicite-facebook-reunion`, `automatiser-devis-artisan`, `agent-ia-repondre-clients-24h` |
| 2 | #15 | `fiche-google-reunion`, `site-vitrine-ou-page-facebook`, `gite-reunion-haute-saison`, `repondre-clients-pendant-les-fetes`, `avis-google-entreprise` |
| 3 | #16 | `lexique-ia-tpe`, `saison-cyclonique-entreprise`, `chatgpt-tpe-usages`, `relances-automatiques-devis-factures`, `chatbot-whatsapp-entreprise` |
| 4 | #17 | `rgpd-tpe-essentiel`, `prise-rendez-vous-en-ligne`, `site-internet-artisan`, `boutique-en-ligne-reunion`, `temps-perdu-taches-repetitives` |
| 5 | #18 | `nom-de-domaine-entreprise`, `newsletter-tpe`, `idees-publications-reseaux-sociaux`, `landing-page-definition`, `page-facebook-piratee` |

Les anciens articles (472 de l'ère PHP) n'ont pas été modifiés.

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
  nécessaire), le financement des formations IA (les fonds exigent Qualiopi, que DIGITA n'a pas).
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
   Les articles sont insérés en brouillon (`ON CONFLICT (slug) DO NOTHING`).
4. Tests : `python -m pytest -q`. `tests/test_blog.py` vérifie les longueurs des metas, la couverture, les
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

- Calendrier : les articles suivants du plan éditorial (hors sujets écartés ci-dessus).
- Nettoyage des 472 anciens articles (garder, fusionner, `noindex`, redirections 301) avec un export Search
  Console.
- Google Search Console : sitemap et suivi des clics par article vers `/diagnostic`.
- Photos réelles de La Réunion pour remplacer ou compléter les couvertures générées.
