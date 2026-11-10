# Suivi des formations

État au 9 novembre 2026. Le plan (types, pilote, étapes) se trouve dans le Claude Doc « Plan de contenu :
articles d'origine et formations ». Ce fichier décrit les décisions prises et la façon de produire une formation.

## Situation actuelle

- Le catalogue contient 382 formations générées automatiquement (fiches à 97 €, sans vrai contenu). Elles sont
  déjà masquées : `/formations` affiche « Bientôt » et propose la formation sur mesure (390 € la journée,
  120 € l'heure).
- Le moteur existe (`formation_modules`, `formation_lessons`, parcours et progression), mais l'admin n'a pas
  encore d'éditeur de leçons (recommandation n° 17 de `RECOMMANDATIONS_GESTION_ADMIN.md`).

## Formation pilote : « Être trouvé sur Google en 30 jours »

Choisie le 9 novembre 2026 parce que :

- c'est le besoin le plus fréquent des TPE de La Réunion, et le sujet le plus couvert par le blog (fiche
  Google, avis, audit SEO, site artisan, nom de domaine), ce qui donne une base vérifiée ;
- tout se montre sur des pages publiques (recherche Google, fiches, outils gratuits), donc se filme sans
  se connecter à un compte ;
- elle mène naturellement au diagnostic gratuit et aux offres SEO et fiche Google de la grille.

Prix et format de vente (9 novembre 2026) : version enrichie haut de gamme, 99 à 149 €, leçon 1 gratuite, voix « marin » pour le moment. Détail dans `docs/formations/PILOTE_GOOGLE_30_JOURS.md`.

## Production des vidéos

On reprend la chaîne de la formation DGT Système d'INES (`backend/scripts/dgt_videos/build.py` dans le dépôt
INES, documentée dans `SUIVI_WORKSPACE_DGT_SYSTEME.md` §12.3) :

1. un script par scène (texte lu, éléments à l'écran) ;
2. la voix : OpenAI `gpt-4o-mini-tts`, avec consignes de formatrice en français. La DGT utilise « coral » ; pour DIGITA, Anthony veut une autre voix (9 novembre 2026) : extraits à écouter avec marin, cedar et ash. Choix d'Anthony le 9 novembre 2026 : **marin**. La synthèse se
   lance dans le conteneur backend d'INES en production, pour que la clé API reste sur le serveur ;
3. la composition HyperFrames en 1920 × 1080, calée sur la durée de chaque piste audio (ffprobe), rendue avec
   `npx hyperframes@0.8.136 render` (Node 22 ou plus) ;
4. ffmpeg : volume normalisé à −16 LUFS, `faststart`, sous-titres VTT ;
5. l'envoi vers le stockage (MinIO dans INES ; l'emplacement côté DIGITA reste à choisir).

Pour DIGITA, on change l'habillage (noir et or, logo DIGITA) et on ajoute des **captures vidéo autonomes** :
Playwright enregistre des parcours sur des pages publiques (une recherche Google, une fiche d'établissement,
un outil de test de vitesse), intégrés ensuite dans la composition.

Écrans connectés :

- Claude ne saisit jamais les mots de passe d'Anthony ni de clients, et n'ouvre pas de session à leur place ;
- INES et digita.buzz connectés : un compte de démonstration avec des données fictives ;
- outils tiers (Google Business Profile, Search Console, Meta) : enregistrés dans la session d'Anthony,
  ouverte par lui, avec l'extension Claude in Chrome ; sinon par Anthony à partir d'un script, ou remplacés
  par des schémas ;
- pas de cookies de session des utilisateurs gardés sur un serveur ;
- pas de visage ni d'avatar généré, sauf décision contraire d'Anthony.

## Prototype et proposition INES (9 novembre 2026)

- Prototype sur l'iMac d'Anthony : une visite de digita.buzz de 48 s, scénario JSON, capture Playwright
  1280 × 720 avec curseur visible, voix macOS provisoire, assemblage ffmpeg. Le code n'est pas commité.
- Proposition « INES : enregistrement d'écrans pour les formations » (Claude Doc,
  https://claude.ai/artifact/J21Nx6vnhGP3Hy1Gr23E4F) : capture sur le serveur des pages publiques et des
  comptes de démonstration (réutilise `site_capture.py`, le worker `celery-worker-video`, HyperFrames et
  MinIO, sans nouvelle dépendance), puis une extension Chrome pour les écrans connectés des outils tiers.
  Cinq lots (A à E), en attente des décisions d'Anthony.

## À régler avant la mise en vente

- Pas de Qualiopi : la formation n'est pas finançable par le CPF ou les OPCO, il ne faut pas le laisser
  entendre.
- Consentement exprès pour le contenu numérique livré immédiatement (renonciation au droit de rétractation,
  recommandation n° 6) et mise à jour des CGV.
- Éditeur de leçons dans l'admin (recommandation n° 17), ou import des leçons par migration SQL en attendant.

## Prochaines étapes

Plan détaillé du pilote et script de la leçon 1 : `docs/formations/PILOTE_GOOGLE_30_JOURS.md` (9 novembre 2026, à valider).

1. Plan détaillé du pilote (modules, leçons, durée) à valider par Anthony.
2. Scripts des scènes, puis une première vidéo test (voix et rendu) avant de produire le reste.
3. Import des leçons, page de vente, mise en ligne.

## Formation DGT-Système (vendue sur INES) : fiche vitrine préparée le 10 novembre 2026

Décision d'Anthony (9 et 10 novembre 2026) : DGT-Système reste dans son workspace INES (lecteur de
cours, examen, projet, attestation). DIGITA ne montre qu'une fiche, et l'achat (197 €, paiement unique,
Stripe d'INES) se fait sur INES.

- Prix et lien : `grille.FORMATIONS_INES` (`DGT_SYSTEME`), jamais en dur dans le gabarit.
- Page : `/formations/dgt-systeme` (`routes/formations.py`, `formations/dgt-systeme-content.html`), carte
  en tête de `/formations`. Textes : « parcours avec attestation INES », avec la mention que ce n'est pas
  une certification reconnue par l'État, voix de synthèse annoncée, crédits INES annoncés, aucun chiffre
  de résultat.
- **Masquée** tant que `visible` vaut `False` (la page redirige vers `/formations`). On la rend visible
  quand la page INES `/formation/dgt-systeme` et le workspace sont corrigés : mot « certifiante »,
  chiffres non sourcés, prix barré, bouton d'achat et liens cassés des pages du Page Builder. Liste
  complète dans le dépôt INES :
  `docs/user/Produit et parcours/Workspaces/PLAN_DGT_SYSTEME_ET_RESTE_A_FAIRE_INES.md`.
- Test : `test_dgt_fiche_is_hidden_until_ines_page_is_fixed_then_links_to_ines` (`tests/test_site.py`).

## Méthode de capture et de rendu validée (10 novembre 2026)

- **Captures de pages réelles** : screencast CDP de Chromium, une image à chaque changement d'affichage,
  avec son horodatage réel, puis assemblage en 30 i/s par ffmpeg (concat). Ne pas utiliser l'enregistreur
  vidéo de Playwright, qui s'étire d'environ 9 % sous charge. Script sur l'iMac :
  `~/Desktop/formation-google-lecon-1/sources/capture.js`.
- **Rendu des leçons** : image par image à horloge fixe (`render.js`). Les sous-titres sont alignés mot par
  mot (whisper sur le serveur, puis recalage sur les pauses avec `silencedetect`, script `align.py`). Sources
  dans `~/Desktop/formation-google-lecon-1/sources/` (pas encore versionnées).
- **Voix** : la synthèse peut omettre une phrase (deux fois sur trois pour la scène 5 de la leçon 1). Après
  chaque génération, retranscrire, comparer au script, et régénérer la phrase manquante.
  Un seuil de couverture par phrase (75 %) ne suffit pas : la synthèse coupe parfois la **fin** d'une phrase
  (L2 scène 3, L12 scène 4, le 10 novembre). Contrôle retenu : les derniers mots de chaque phrase doivent
  être entendus. Les écarts restants viennent souvent de la retranscription (« la fiche » entendu
  « l'affiche ») : on les vérifie à l'écoute, un par un.
- **Bornes des sous-titres** : whisper prolonge souvent le dernier mot d'un groupe (jusqu'à 0,64 s de trop
  sur L2). Les bornes sont recalées sur les pauses réelles de l'audio final (`silencedetect`), encadrées
  par le premier et le dernier mot. Résultat sur L2 : 0,13 s d'écart maximal à l'apparition, 0,19 s à la
  disparition.
  Garde-fou ajouté : un sous-titre n'apparaît jamais plus de 0,15 s après le premier mot entendu (une
  micro-pause après le premier mot avait retardé un sous-titre de 0,7 s sur L12), et en début de piste il
  démarre avec la voix.
- **Règle finale du calage (10 novembre 2026)** : `silencedetect` prenait les respirations de la voix de
  synthèse (−40 à −50 dB) pour de la parole. Le calage et le contrôle se font désormais sur l'énergie du son
  (toutes les 20 ms, seuil relatif au niveau de la voix). Si whisper place le premier mot dans un silence,
  le sous-titre démarre avec la parole qui suit ; sinon au début du segment de parole qui le contient, sans
  empiéter sur le groupe précédent ; même principe pour la fin. Seuil : 30 dB sous le 90e centile de
  l'énergie de la voix.

## Leçons produites (10 novembre 2026)

Fichiers sur l'iMac : `~/Desktop/formation-google-lecons/lecon-NN.mp4`, chacun avec son `.vtt`. Rien n'est
publié.

| Leçon | Durée | Son | Sous-titres | Phrases vérifiées |
| --- | --- | --- | --- | --- |
| L2 · Les 3 critères de Google | 2 min 26 | −16,0 LUFS | 36 | 25 |
| L3 · État des lieux en 15 min (avec la capture D1, page Boutique) | 2 min 08 | −15,9 LUFS | 32 | 25 |
| L10 · Ce qui fait disparaître une fiche | 1 min 30 | −16,0 LUFS | 20 | 17 |
| L12 · Une page par service | 1 min 38 | −16,1 LUFS | 21 | 14 |
| L13 · Un site rapide sur téléphone (PageSpeed en schéma) | 1 min 37 | −15,7 LUFS | 23 | 17 |
| L15 · Le plan des mois suivants | 1 min 40 | −16,5 LUFS | 26 | 19 |

Contrôles :
- Voix : 117 phrases retranscrites ; on régénère si une phrase est couverte à moins de 90 % ou si ses deux
  derniers mots manquent (3 fins de phrase coupées sur 33 pistes, toutes régénérées).
- Synchronisation sur la parole réelle de l'audio final (150 sous-titres mesurables sur 158) : apparition
  0,03 à 0,07 s avant la voix, disparition au plus 0,17 s après.
- Schémas seulement, aucune capture de google.com ni de vraies entreprises ; exemples marqués « Exemple (cas
  fictif) ».

Moteur réutilisable (non versionné pour l'instant) : `~/Desktop/formation-google-lecons/moteur/`
(`lessons.py` scènes en JSON, `scene.html` schémas, `render.js` rendu image par image, `align.py`,
`speech.py`, `verify.py`, `capture.js`). La voix est générée dans `ines-celery-worker-video` sur le serveur
INES. L3 cale la capture D1 par `video:at:16.5` (le clic sur « Analyser » tombe sur « lancez le test »).

Reste : leçons 4 à 9, 11 et 14, après les captures d'Anthony (D3 à D10). La leçon 1 a été produite le
9 novembre avec l'ancienne méthode : à refaire avec ce moteur pour l'homogénéité.
