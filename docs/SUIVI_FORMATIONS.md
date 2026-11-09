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

Prix et format de vente : à fixer par Anthony.

## Production des vidéos

On reprend la chaîne de la formation DGT Système d'INES (`backend/scripts/dgt_videos/build.py` dans le dépôt
INES, documentée dans `SUIVI_WORKSPACE_DGT_SYSTEME.md` §12.3) :

1. un script par scène (texte lu, éléments à l'écran) ;
2. la voix : OpenAI `gpt-4o-mini-tts`, voix « coral », consignes de formatrice en français. La synthèse se
   lance dans le conteneur backend d'INES en production, pour que la clé API reste sur le serveur ;
3. la composition HyperFrames en 1920 × 1080, calée sur la durée de chaque piste audio (ffprobe), rendue avec
   `npx hyperframes@0.8.136 render` (Node 22 ou plus) ;
4. ffmpeg : volume normalisé à −16 LUFS, `faststart`, sous-titres VTT ;
5. l'envoi vers le stockage (MinIO dans INES ; l'emplacement côté DIGITA reste à choisir).

Pour DIGITA, on change l'habillage (noir et or, logo DIGITA) et on ajoute des **captures vidéo autonomes** :
Playwright enregistre des parcours sur des pages publiques (une recherche Google, une fiche d'établissement,
un outil de test de vitesse), intégrés ensuite dans la composition.

Limites :

- pas de connexion aux comptes d'Anthony ou de clients : les écrans connectés (Google Business Profile,
  Search Console) seront des enregistrements faits par Anthony ou des schémas ;
- pas de visage ni d'avatar généré, sauf décision contraire d'Anthony.

## À régler avant la mise en vente

- Pas de Qualiopi : la formation n'est pas finançable par le CPF ou les OPCO, il ne faut pas le laisser
  entendre.
- Consentement exprès pour le contenu numérique livré immédiatement (renonciation au droit de rétractation,
  recommandation n° 6) et mise à jour des CGV.
- Éditeur de leçons dans l'admin (recommandation n° 17), ou import des leçons par migration SQL en attendant.

## Prochaines étapes

1. Plan détaillé du pilote (modules, leçons, durée) à valider par Anthony.
2. Scripts des scènes, puis une première vidéo test (voix et rendu) avant de produire le reste.
3. Import des leçons, page de vente, mise en ligne.
