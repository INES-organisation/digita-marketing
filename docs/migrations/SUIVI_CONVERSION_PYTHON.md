# Suivi de la conversion PHP → Python et mise en ligne sur digita.buzz

**Démarré le :** 9 octobre 2026
**Branche :** `claude/project-thread-0x6ahi`
**Cible :** https://digita.buzz, sur le VPS d'INES (`37.187.219.225`, `/opt/digita`)
**Référence :** `INES/docs/analyses/ANALYSE_CONVERSION_PHP_VERS_PYTHON.md`, `INES/docs/user/FACTION/DIGITA/INFRASTRUCTURE_ET_DOMAINES_DIGITA.md`

---

## 1. État d'avancement

| Phase | Contenu | État |
|---|---|---|
| 0 | Données : MySQL → PostgreSQL, vérification ligne à ligne | ✅ fait (sur l'export de février) |
| 1 | Pages publiques : accueil, pages fixes, blog, catégories, articles, formations, landings, pages légales, outils (formulaires), connexion/inscription (formulaires) | ✅ fait : **1 300 pages sur 1 302 identiques au HTML PHP** |
| 2 | Formulaires publics : demande d'audit (accueil), chatbot, outils IA (audit SEO, meta, ROI, calendrier), connexion/inscription, suivi analytics | ⏳ à faire |
| 3 | Espace élève et paiement : inscription aux formations, leçons, quiz, certificats, avis, Stripe, commandes, factures, espace client projets | ⏳ à faire |
| 4 | Administration : tableau de bord, articles, formations, médias, projets, campagnes, newsletters, webhooks | ⏳ à faire |
| 5 | Mise en ligne : base sur le VPS, conteneur, nginx, certificat, DNS, redirection de l'ancien domaine | ⏳ préparé, rien n'est déployé |

Tant que les phases 2 à 4 ne sont pas faites, les routes concernées répondent par un message
« fonctionnalité en cours de migration » (HTTP 501). Le site PHP reste la version de production.

## 2. Choix techniques

| Sujet | Choix | Pourquoi |
|---|---|---|
| Framework | FastAPI + templates Jinja2 rendus côté serveur | Même stack que Webox et INES (FastAPI). Le rendu serveur garde le HTML et le SEO identiques ; une réécriture en React (piste de l'analyse INES) changerait le rendu. |
| Templates | Générés depuis les vues PHP (`python/tools/php2jinja.py`), puis corrigés (`python/tools/fixups.py`) | Reproduit fidèlement chaque vue, y compris les particularités PHP (saut de ligne avalé après `?>`, vérité PHP, `htmlspecialchars`, `require_once`). |
| Base de données | PostgreSQL, base `digita` dans le conteneur `ines-postgres` existant | Pas de serveur MySQL en plus sur un VPS déjà chargé (RAM). Extension `unaccent` pour garder une recherche insensible aux accents comme MySQL. |
| Dépôt | Le code reste dans `digita-marketing` (dossier `python/`) | Conversion progressive : le PHP reste déployable sur OVH tant que le Python n'est pas complet. Le passage en monorepo INES pourra se faire ensuite. |
| Déploiement | Conteneur `digita-web` (≈ 145 Mo de RAM), projet compose séparé branché sur le réseau d'INES, servi par `ines-nginx` | N'affecte ni INES ni les pages Page Builder (`lp48.digita.buzz`). |

## 3. Arborescence

```
python/
├── digita/
│   ├── main.py          routeur (même ordre et mêmes règles que public/index.php)
│   ├── routes/          un module par contrôleur PHP (pages, blog, formations, outils, auth)
│   ├── models/          requêtes de Article.php / Formation.php adaptées à PostgreSQL
│   ├── php.py           équivalents des fonctions PHP utilisées par les vues
│   ├── render.py        rendu des vues avec layout (ViewHelper::render)
│   └── templates/       vues Jinja (même chemin que les .php d'origine)
├── tools/
│   ├── php2jinja.py, fixups.py, convert_all.sh, templates.txt   conversion des vues
│   ├── migrate_mysql_to_pg.py, verify_migration.py              données
│   ├── parity.py, parity_ci.sh                                  comparaison HTML PHP/Python
├── deploy/              docker-compose, nginx, import de l'export OVH
├── tests/               tests unitaires
└── Dockerfile
```

Après une modification d'une vue PHP : `bash python/tools/convert_all.sh` régénère les templates.

## 4. Comment l'identité est vérifiée

`python/tools/parity_ci.sh` (lancé par la CI « Parité PHP / Python » sur chaque PR) :

1. importe `database/production_data_full.sql` et les migrations dans MySQL ;
2. copie la base vers PostgreSQL et vérifie chaque table ligne à ligne (empreinte SHA-256) ;
3. lance le site PHP et le site Python sur la même base ;
4. télécharge les 1 302 URL publiques (30 pages fixes, 18 catégories × 2, 472 articles, 382 formations + 382 landings) et compare le HTML.

Seules différences tolérées par la comparaison : le paramètre anti-cache `?v=<time()>`, l'hôte local,
le jeton CSRF (aléatoire) et `dateModified` du jour (mis à jour à chaque vue d'article, comme en MySQL).

Dernier résultat : **1 300 identiques, 0 différente** (hors `/portfolio` et `/equipe`, voir §6).

## 5. Routes (public/index.php)

| Groupe | Routes | État |
|---|---|---|
| Accueil | `/` | ✅ |
| Pages fixes | `/a-propos`, `/services`, `/catalogue`, `/contact`, `/support`, `/tarifs`, `/boutique`, `/solutions`, `/outils`, redirections `/solution` et `/formation` | ✅ |
| Pages légales | `/mentions-legales`, `/politique-confidentialite`, `/conditions-generales`, `/cookies` | ✅ |
| Blog | `/blog`, `/blog/search`, `/blog/categorie/:slug`, `/blog/:slug` | ✅ |
| Formations (public) | `/formations`, `/formations/search`, `/formations/categorie/:slug`, `/formations/:slug`, `/formations/:slug/landing`, `/certificat/verifier` | ✅ |
| Outils (affichage) | `/outils/audit-seo`, `/outils/meta-generator`, `/outils/roi-calculator`, `/outils/calendrier-editorial` | ✅ |
| Outils (traitement IA) | POST des 4 outils, `POST /api/roi-calculate` | ⏳ phase 2 |
| Connexion | GET `/connexion`, `/inscription` ✅ — POST ⏳ phase 2 | partiel |
| Leads | `POST /api/audit-request`, chatbot (`/api/chatbot/*`), analytics (`/api/analytics/*`) | ⏳ phase 2 |
| Espace élève | `/mes-formations`, inscription, leçons, quiz, avis, certificats | ⏳ phase 3 |
| Paiement | checkout, Stripe (webhook), promo, commandes, factures | ⏳ phase 3 |
| Projets clients | `/projets/brief`, `/espace-client/*`, `/api/project-quote`, `/webhook/webox` | ⏳ phase 3 |
| Administration | 39 routes `/admin/*` | ⏳ phase 4 |

## 6. Écarts connus et défauts déjà présents dans le PHP

- `/portfolio` et `/equipe` : les templates `templates/portfolio.php` et `templates/team.php` n'existent pas ;
  en production PHP affiche « Une erreur est survenue… ». La version Python affiche le même message.
  À décider : retirer ces liens ou créer les pages.
- Formulaires qui pointent vers des routes inexistantes (404 en PHP comme en Python) :
  `POST /contact`, `/newsletter/subscribe`, `/formations/enroll/:id`, `/boutique/search`, `/solutions/search`.
- Ordre des articles à date de publication égale : MySQL le laisse indéterminé ; la version Python
  départage par identifiant décroissant (ordre stable). Le contenu affiché est le même, l'ordre de
  quelques articles publiés à la même seconde peut différer du site actuel.
- `ORDER BY RAND()` (articles et formations liés) est conservé (aléatoire) en production.
- La table `users` de l'export ne contient pas `username`, alors que le code PHP l'utilise (avis de
  formations, commandes, projets). L'export de production doit le confirmer.
- Le workflow `deploy.yml` envoie le dépôt sur OVH par FTP : `python/` y est désormais exclu.

## 7. Ce qu'il faut avant la mise en ligne (bloquants)

1. **Export récent de la base OVH** (phpMyAdmin → Exporter → SQL, structure + données). L'export du dépôt
   date du 10 février 2026 et ne contient que 19 tables sur 43.
2. **Dossier `public/uploads` d'OVH** s'il existe (images envoyées depuis l'admin).
3. **DNS de digita.buzz** (zone OVH) : `A digita.buzz → 37.187.219.225` et `A www → 37.187.219.225`.
   Ne pas toucher à `lp48.digita.buzz`.
4. **Feu vert explicite** avant toute action sur le VPS (rien n'a été déployé).
5. Pour les phases 2-3 : clés de production Stripe, SMTP et OpenAI (actuellement dans le `.env` OVH).

## 8. Procédure de mise en ligne (à exécuter seulement après feu vert)

Sur le VPS (`ssh ines-vps`) :

```bash
# 1. Code
sudo git clone https://github.com/INES-organisation/digita-marketing.git /opt/digita
cd /opt/digita && git checkout <branche ou main après merge>
cp python/deploy/.env.example python/deploy/.env   # remplir mot de passe, SECRET_KEY

# 2. Base « digita » dans ines-postgres (utilisateur dédié, propriétaire de sa base)
docker exec -i ines-postgres psql -U ines -d ines_db -c "CREATE ROLE digita LOGIN PASSWORD '…'" \
  -c "CREATE DATABASE digita OWNER digita"

# 3. Données : export OVH → PostgreSQL, avec vérification ligne à ligne
bash python/deploy/import_ovh_dump.sh ~/export_ovh.sql

# 4. Conteneur
docker compose -f python/deploy/docker-compose.yml --env-file python/deploy/.env up -d --build
docker exec digita-web python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/healthz').read())"

# 5. HTTPS (une fois le DNS propagé) puis nginx
cd /opt/ines && bash scripts/add-custom-domain.sh digita.buzz
#    ajouter python/deploy/nginx-digita.conf dans monitoring/nginx/nginx.conf (dépôt INES), puis :
docker exec ines-nginx nginx -t && docker exec ines-nginx nginx -s reload
```

Après bascule : redirection 301 de `digita.tonyalpha80.com` vers `https://digita.buzz` (`.htaccess` OVH).

Retour arrière : retirer le bloc nginx et recharger nginx (le site OVH n'est pas modifié).

## 9. Journal

| Date | Étape |
|---|---|
| 09/10/2026 | Base PHP de référence montée en local (export février + migrations), 1 302 pages aspirées. |
| 09/10/2026 | Données copiées vers PostgreSQL, 43 tables, contrôle ligne à ligne OK. |
| 09/10/2026 | Phase 1 : app FastAPI + 44 templates, 1 300/1 302 pages identiques ; image Docker testée (≈ 145 Mo RAM). |
