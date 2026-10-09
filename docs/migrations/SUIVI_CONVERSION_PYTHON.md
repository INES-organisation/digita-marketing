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
| 2 | Formulaires publics : demande d'audit (accueil), chatbot, outils IA (audit SEO, meta, ROI, calendrier), connexion/inscription, suivi analytics | ✅ fait : **60 réponses sur 60 identiques au PHP** |
| 3 | Espace élève et paiement : inscription aux formations, leçons, quiz, certificats, avis, Stripe, commandes, factures, espace client projets | ✅ fait |
| 4 | Administration : tableau de bord, articles, formations, médias, projets, campagnes, newsletters, webhooks | ✅ fait : avec les phases 2 et 3, **293 réponses identiques au PHP sur 295**, les 2 autres échouent des deux côtés (§6) |
| 5 | Mise en ligne : base sur le VPS, conteneur, nginx, certificat, DNS, redirection de l'ancien domaine | ⏳ préparé, rien n'est déployé |

Toutes les routes de `public/index.php` sont converties. Le site PHP reste la version de production
jusqu'à la bascule.

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
│   ├── routes/          un module par contrôleur PHP (pages, blog, formations, learning, payment, projects, admin, outils, auth, leads, chatbot, analytics)
│   ├── services/        e-mail (SMTP), IA (OpenAI, audit SEO, ROI), agents du chatbot, Stripe (API REST), Webox
│   ├── security.py      CSRF et limitation des tentatives (middlewares PHP)
│   ├── models/          requêtes des modèles PHP (articles, formations, quiz, certificats, commandes, factures, projets) adaptées à PostgreSQL
│   ├── sessions.py      sessions côté serveur (table web_sessions), comme $_SESSION
│   ├── php.py           équivalents des fonctions PHP utilisées par les vues
│   ├── render.py        rendu des vues avec layout (ViewHelper::render)
│   └── templates/       vues Jinja (même chemin que les .php d'origine)
├── tools/
│   ├── php2jinja.py, fixups.py, convert_all.sh, templates.txt   conversion des vues
│   ├── migrate_mysql_to_pg.py, verify_migration.py              données
│   ├── parity.py, post_parity.py, parity_ci.sh                  comparaison PHP/Python (pages, formulaires)
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

Les formulaires et API sont comparés ensuite par `python/tools/post_parity.py` : 295 envois (demande
d'audit, connexion, inscription avec champs manquants, jeton CSRF absent ou faux, compte existant,
6ᵉ tentative bloquée en 429 ; chatbot et ses réponses de secours, historique, rendez-vous et créneaux ;
les 4 outils dont un audit SEO complet d'une page de test ; analytics ; parcours élève complet sur une
formation gratuite : inscription, 20 leçons, quiz réussi et raté, avis, certificat ; paiement sans Stripe :
codes promo valides, expirés, épuisés, commande offerte à 100 %, commandes, factures, annulation ;
projets : devis AJAX, brief avec champs manquants ou complets, espace client, projet d'un autre client,
messages et pièce jointe refusée, webhook Webox en visiteur et en administrateur ; administration :
accès refusé aux visiteurs et aux clients, toutes les pages, filtres et pagination, création, modification
et suppression d'articles et de formations, contacts lus et répondus, export CSV, médias, projets (statut,
messages, notes, tâches, prix, génération Webox), déconnexion) donnent le même statut, la même
redirection, le même JSON ou la même page HTML dans les deux versions ; les lignes écrites en base
sont identiques. Les données de test (formation gratuite, quiz, codes promo, projet Webox, administrateur)
sont dans `python/tools/fixtures_forms.sql`, appliqué aux deux bases. Les mots de passe sont hachés en
`$2y$` comme PHP : un compte créé d'un côté se connecte de l'autre.

## 5. Routes (public/index.php)

| Groupe | Routes | État |
|---|---|---|
| Accueil | `/` | ✅ |
| Pages fixes | `/a-propos`, `/services`, `/catalogue`, `/contact`, `/support`, `/tarifs`, `/boutique`, `/solutions`, `/outils`, redirections `/solution` et `/formation` | ✅ |
| Pages légales | `/mentions-legales`, `/politique-confidentialite`, `/conditions-generales`, `/cookies` | ✅ |
| Blog | `/blog`, `/blog/search`, `/blog/categorie/:slug`, `/blog/:slug` | ✅ |
| Formations (public) | `/formations`, `/formations/search`, `/formations/categorie/:slug`, `/formations/:slug`, `/formations/:slug/landing`, `/certificat/verifier` | ✅ |
| Outils (affichage) | `/outils/audit-seo`, `/outils/meta-generator`, `/outils/roi-calculator`, `/outils/calendrier-editorial` | ✅ |
| Outils (traitement IA) | POST des 4 outils, `POST /api/roi-calculate` | ✅ |
| Connexion | `/connexion`, `/inscription` (affichage et traitement : CSRF, limitation des tentatives, mots de passe bcrypt compatibles PHP) | ✅ |
| Leads | `POST /api/audit-request` | ✅ |
| Chatbot, rendez-vous | `/api/chatbot/message`, `history`, `qualify`, `appointment`, `slots` | ✅ |
| Analytics | `/api/analytics/pageview`, `/api/analytics/conversion` | ✅ |
| Espace élève | `/mes-formations`, inscription, leçons, quiz, avis, certificats | ✅ |
| Paiement | checkout, Stripe (webhook), promo, commandes, factures | ✅ |
| Projets clients | `/projets/brief`, `/espace-client/*`, `/api/project-quote`, `/webhook/webox` | ✅ |
| Administration | 39 routes `/admin/*` | ✅ |

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
- **Accueil, fenêtre « Audit gratuit » (`templates/home.php`, `#auditForm`)** : les champs n'ont pas
  d'attribut `name` et le script affiche seulement le message de succès, sans rien envoyer. Les demandes
  saisies dans cette fenêtre sont perdues, en PHP comme en Python (le rendu est reproduit à l'identique).
  Le formulaire de `conversion-modal.php`, lui, envoie bien vers `/api/audit-request`. À corriger après bascule.
- E-mails : le PHP utilisait `mail()` d'OVH. Sur le VPS, l'envoi passe par SMTP (`MAIL_HOST`, `MAIL_PORT`,
  `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`) ; sans ces variables, la demande est enregistrée en base
  et l'e-mail est seulement journalisé.
- Connexion : comme en MySQL, l'e-mail est comparé sans tenir compte de la casse.
- **Audit SEO** : le PHP analysait n'importe quelle adresse, y compris interne. Sur le VPS le conteneur voit
  les services d'INES : la version Python refuse les adresses privées ou locales (y compris après
  redirection) et affiche « Impossible d'accéder à l'URL (HTTP 0) ». Seul écart volontaire.
- Analytics : le contrôleur PHP exige un administrateur connecté (`requireAdmin()` dans le constructeur),
  donc les visites des visiteurs ne sont jamais enregistrées (redirection vers `/connexion`). Reproduit tel quel.
- Chatbot : l'extraction du brief client teste une variable PHP jamais définie et ne s'exécute jamais.
  Reproduit tel quel. Sans `OPENAI_API_KEY`, le chatbot répond avec ses messages de secours.
- Erreur inattendue : même message générique que le PHP, mais avec le code HTTP 500 (le PHP renvoyait 200).
- Base : les ENUM MySQL deviennent des contraintes CHECK, les colonnes `ON UPDATE CURRENT_TIMESTAMP`
  sont mises à jour par déclencheur, les colonnes JSON passent en `jsonb` (même texte que MySQL).
- **Paiement PHP en panne** : `Formation::find()` n'existe pas, donc le checkout PHP plante (« Une erreur est
  survenue ») dès qu'on ouvre `/formations/checkout/:id`. Le SDK Stripe n'est par ailleurs chargé
  nulle part dans le code PHP. La version Python corrige les deux : elle lit la formation et appelle
  l'API Stripe directement. La comparaison ajoute `find()` à la copie PHP de référence pour tester le reste.
- `sprint3_migration.sql` échoue en bloc sur une base existante (`product_name` existe déjà) : la colonne
  `order_items.product_type` et `users.username` manquent alors. La base PostgreSQL les contient.
- Sessions : le PHP gardait `$_SESSION` sur le serveur ; la version Python fait pareil (table
  `web_sessions`, cookie `DIGITASESSID` qui ne contient qu'un identifiant aléatoire, sessions inactives
  supprimées après 24 h). Les comptes connectés devront se reconnecter une fois après la bascule.
- Projets clients : le webhook Webox (`/webhook/webox`) exige un administrateur connecté, comme en PHP
  (`requireAdmin()` dans le constructeur) ; Webox ne peut donc pas l'appeler. Reproduit tel quel.
- Pièces jointes des projets : enregistrées dans `public/uploads/projects/<id>/`, qui est un volume Docker
  (`digita-uploads`) pour survivre aux mises à jour de l'image.
- **Faille dans l'admin PHP (à corriger sur OVH sans attendre)** : l'envoi d'image des articles et des
  formations ne vérifie que le type annoncé par le navigateur et garde l'extension du fichier. Un fichier
  `x.php` envoyé comme `image/png` est enregistré dans `public/uploads/articles/` (vérifié sur la copie
  locale), et aucun `.htaccess` n'empêche Apache d'exécuter un `.php` existant à cet endroit. Il faut un compte administrateur, mais un mot de passe admin volé suffit
  pour prendre la main sur l'hébergement. La version Python n'accepte que les extensions d'image
  (jpg, jpeg, png, gif, webp ; svg, pdf, mp4, webm en plus pour la médiathèque) et ne sert jamais de `.php`.
- **Page Analytics de l'admin en panne, en PHP comme en Python** : elle lit `orders.total_amount` et la table
  `user_formations`, qui n'existent pas dans la base. Reproduit tel quel (message d'erreur générique).
- Admin : les pages « Campagnes » et « Webhooks » sont des maquettes en PHP (données écrites en dur, rien
  n'est enregistré). Reproduit tel quel.
- Admin, génération Webox : sans `WEBOX_API_URL`, le PHP appelle `http://localhost:8000`. Sur le VPS il faut
  l'adresse de Webox (réseau INES), sinon l'admin affiche « Erreur Webox ».
- Médiathèque : le type d'un fichier (image, vidéo, PDF) est déduit de son extension, le PHP lisait son contenu.
- Dates : comme MySQL, les dates enregistrées s'arrêtent à la seconde (valeurs par défaut, `NOW()` et
  déclencheurs), pour que deux écritures dans la même seconde gardent le même ordre d'affichage.
- Le workflow `deploy.yml` envoie le dépôt sur OVH par FTP : `python/` y est désormais exclu.

## 7. Ce qu'il faut avant la mise en ligne (bloquants)

1. **Export récent de la base OVH** (phpMyAdmin → Exporter → SQL, structure + données). L'export du dépôt
   date du 10 février 2026 et ne contient que 19 tables sur 43.
2. **Dossier `public/uploads` d'OVH** s'il existe (images de l'admin, pièces jointes des projets), à copier
   dans le volume `digita-uploads`.
3. **DNS de digita.buzz** (zone OVH) : `A digita.buzz → 37.187.219.225` et `A www → 37.187.219.225`.
   Ne pas toucher à `lp48.digita.buzz`.
4. **Feu vert explicite** avant toute action sur le VPS (rien n'a été déployé).
5. Adresse et clé de l'API Webox (`WEBOX_API_URL`, `WEBOX_API_KEY`) si la génération de sites est utilisée.
6. Clés de production Stripe (`STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY`, `STRIPE_WEBHOOK_SECRET`, avec le
   webhook Stripe à repointer vers `https://digita.buzz/webhook/stripe`), SMTP (`MAIL_*`) et OpenAI.

## 8. Procédure de mise en ligne (à exécuter seulement après feu vert)

Sur le VPS (`ssh ines-vps`) :

```bash
# 1. Code
sudo git clone https://github.com/INES-organisation/digita-marketing.git /opt/digita
cd /opt/digita && git checkout <branche ou main après merge>
cp python/deploy/.env.example python/deploy/.env   # remplir le mot de passe de la base, SMTP, OpenAI

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
| 09/10/2026 | Phase 2 : demande d'audit, connexion et inscription converties, 24/24 réponses identiques au PHP. |
| 09/10/2026 | Phase 2 terminée : chatbot, rendez-vous, outils IA et analytics ; 60/60 réponses identiques, pages toujours à 1 300/1 302. |
| 09/10/2026 | Phase 3 : espace élève (leçons, quiz, avis, certificats), paiement (promo, commandes, factures, Stripe par API) et projets clients (brief, devis, espace client, messages, webhook Webox) ; 194/194 réponses identiques, pages toujours à 1 300/1 302. |
| 09/10/2026 | Phase 4 : administration (39 routes : tableau de bord, contacts, newsletter, articles, formations, médias, analytics, projets, campagnes) ; 293/295 réponses identiques, 2 en erreur des deux côtés ; pages toujours à 1 300/1 302. Faille d'envoi de fichiers PHP relevée. |
| 09/10/2026 | Déploiement sur le VPS (sans clés de production) avec les données de février du dépôt : 43 tables vérifiées, conteneur sain. Base OVH et uploads pas encore récupérés (accès FTP refusé), DNS pas encore basculé. La copie vers PostgreSQL ne demande plus de droit superutilisateur. |
| 09/10/2026 | Mise en ligne : DNS de digita.buzz et www basculé vers le VPS, certificat Let's Encrypt (jusqu'au 07/01/2027), bloc nginx ajouté à ines-nginx (branche INES claude/project-thread-ew9z9f, pas encore fusionnée). Hébergement OVH arrêté : aucune base plus récente que l'export du 10/02 n'existe, les données saisies sur OVH après cette date (contacts, abonnés, comptes, commandes) sont perdues. Clés de production toujours vides. |
