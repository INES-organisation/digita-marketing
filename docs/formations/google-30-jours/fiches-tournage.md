# Fiches de tournage : démonstrations sur de vrais écrans

État au 9 novembre 2026. Ces fiches complètent les scripts `lecon-01.md` à `lecon-15.md`. Elles listent
les démonstrations à filmer sur de vrais écrans, pour remplacer ou compléter un schéma. La voix off reste
celle du script : les captures sont muettes, et la voix « marin » est calée dessus au montage.

## Répartition

| N° | Leçon, scène | Démonstration | Qui tourne | Durée visée |
| --- | --- | --- | --- | --- |
| D1 | L3, scène 3 | Audit SEO gratuit de digita.buzz | Claude seul (page publique) | 60 s |
| D2 | L13, scène 2 | PageSpeed Insights, onglet Mobile | Claude seul (page publique) | 60 s |
| D3 | L4, scène 3 | Revendiquer ou créer une fiche | Anthony (son compte Google) | 90 s |
| D4 | L5, scènes 2 à 4 | Catégorie, zone desservie, horaires exceptionnels | Anthony | 2 min |
| D5 | L6, scènes 3 et 4 | Services et description de la fiche | Anthony | 90 s |
| D6 | L7, scène 4 | Ajouter une photo à la fiche | Anthony | 60 s |
| D7 | L8, scène 2 | Copier le lien « Demander des avis » | Anthony | 45 s |
| D8 | L9, scènes 2 à 4 | Répondre à un avis, signaler un avis | Anthony | 90 s |
| D9 | L11, scène 3 | Le champ « Site web » de la fiche | Anthony | 30 s |
| D10 | L14, scènes 2 et 3 | Search Console : ajout d'une propriété, rapport Performances | Anthony | 2 min |

Total : environ 13 minutes de captures, dont 11 pour Anthony, en une seule séance (D3 à D9 sur la fiche
Google, puis D10 sur la Search Console). Après montage (zooms, pauses calées sur la voix), on compte
environ 20 à 25 minutes de démonstrations en plus dans la formation.

Restent en schéma, sans capture :

- les pages de résultats Google : L1 scène 2, L2, L4 scène 2, L6 scène 2 (suggestions de recherche),
  L10 scène 3 (doublons). Une capture de google.com montrerait de vraies entreprises sans leur accord, et
  un robot y tombe sur une page de consentement ou une vérification anti-robot ;
- les fiches d'autres entreprises : on n'en montre aucune.

## Règles pour tous les tournages

- **Uniquement le compte et la fiche de DIGITA**, jamais ceux d'un client.
- **Ne rien enregistrer par erreur.** Dans un formulaire, on montre le champ puis on clique sur
  « Annuler », sauf si la modification est réellement voulue pour la fiche de DIGITA.
- **Pas de voix pendant la capture.** La narration est ajoutée au montage.
- Le floutage est fait au montage, mais ce qui ne s'affiche pas n'a pas à être flouté : fermer les autres
  onglets, masquer les favoris, activer « Ne pas déranger » (pas de notification à l'écran).

### Réglages d'enregistrement (Mac)

1. Chrome dans une fenêtre seule, à 1440 × 900 environ, zoom de la page à 110 %.
2. `Cmd + Maj + 5`, « Enregistrer la partie sélectionnée », sélectionner la fenêtre de Chrome. Options :
   « Afficher les clics de souris » activé, micro désactivé.
3. Bouger la souris lentement et marquer **une pause de 2 secondes après chaque clic** : le montage cale la
   voix sur ces pauses.
4. Un fichier par démonstration, nommé `D3-revendiquer.mov`, `D4-reglages.mov`, etc., déposé dans
   `~/Desktop/formation-google-captures/`.

## Les fiches

### D1. Audit SEO gratuit de digita.buzz (Claude seul)

- **Leçon** : L3, scène 3 « Votre site : l'audit gratuit ».
- **Page** : https://digita.buzz/outils/audit-seo (publique).
- **Site testé** : une page qui appartient à DIGITA, jamais le site d'un tiers. Le script parle d'un
  « site fictif » : l'adresse est présentée comme un exemple.
- **Clics** : ouvrir la page → cliquer dans le champ d'adresse → saisir l'adresse → lancer l'audit →
  attendre le rapport → faire défiler les 10 lignes → zoom sur les lignes HTTPS, affichage mobile et titre
  de la page.
- **Durée** : 60 s.
- **À flouter** : rien.
- **Essai du 10 novembre 2026** (captures image par image, Playwright, 1440 × 900) : score 95/100. L'essai
  a révélé deux défauts, corrigés dans la PR #28 : l'audit affichait « &amp; » au lieu de « & » (et
  comptait ces caractères en trop), et la meta description de l'accueil faisait 192 caractères. **Filmer
  D1 après la mise en ligne de la PR #28**, pour que le rapport montré soit propre.

### D2. PageSpeed Insights (Claude seul)

- **Leçon** : L13, scène 2 « Mesurer avec PageSpeed Insights ».
- **Page** : https://pagespeed.web.dev (publique). Bandeau de cookies : refuser les cookies non
  essentiels. Si la page bloque le robot, on garde le schéma.
- **Site testé** : `digita.buzz` ou une page de DIGITA.
- **Clics** : saisir l'adresse → « Analyser » → onglet « Mobile » → zoom sur l'évaluation des Core Web
  Vitals (LCP, INP, CLS) → descendre jusqu'aux recommandations.
- **Durée** : 60 s.
- **À flouter** : rien.

### D3. Revendiquer ou créer une fiche (Anthony)

- **Leçon** : L4, scène 3 « Revendiquer ou créer ».
- **Page** : https://www.google.com/business/ → « Gérer maintenant ».
- **Clics** : se connecter (avant de lancer la capture) → « Gérer maintenant » → saisir le nom de
  l'entreprise → montrer la liste des suggestions → choisir « Ajouter votre établissement » ou la fiche
  existante → montrer l'étape de la catégorie → **arrêter avant toute validation** (fermer ou « Retour »).
- **Durée** : 90 s.
- **À flouter** : l'adresse e-mail du compte (en haut à droite), le téléphone et l'adresse personnels
  s'ils apparaissent.

### D4. Catégorie, zone desservie et horaires exceptionnels (Anthony)

- **Leçon** : L5, scènes 2 à 4.
- **Page** : la fiche de DIGITA → « Modifier le profil ».
- **Clics** :
  1. « Infos sur l'établissement » → « Catégorie » : montrer la catégorie principale et les suggestions en
     tapant les premières lettres → « Annuler » ;
  2. « Emplacement et zones » → « Zone desservie » : montrer la liste des communes → « Annuler » ;
  3. « Horaires » → « Horaires exceptionnels » → « Ajouter une date » : montrer le 20 décembre →
     « Annuler » (ou enregistrer si la date est réellement à ajouter).
- **Durée** : 2 min (trois passages de 40 s, séparés au montage).
- **À flouter** : l'e-mail du compte ; l'adresse si elle est personnelle.

### D5. Services et description (Anthony)

- **Leçon** : L6, scènes 3 et 4.
- **Page** : fiche de DIGITA → « Modifier les services », puis « Modifier le profil » → « Description ».
- **Clics** : ouvrir la liste des services → montrer l'ajout d'un service personnalisé (taper le nom, sans
  enregistrer) → « Annuler » → ouvrir « Description » → faire défiler le texte → « Annuler ».
- **Durée** : 90 s.
- **À flouter** : l'e-mail du compte.

### D6. Ajouter une photo (Anthony)

- **Leçon** : L7, scène 4 « Retoucher et publier ».
- **Page** : fiche de DIGITA → « Ajouter une photo ».
- **Clics** : « Ajouter une photo » → choisir une photo préparée à l'avance (bureau, équipe, réalisation de
  DIGITA) → montrer l'aperçu → publier seulement si la photo est réellement voulue sur la fiche, sinon
  « Annuler ».
- **Durée** : 60 s.
- **À flouter** : le nom des autres fichiers visibles dans la fenêtre de sélection (préparer un dossier ne
  contenant que la photo).

### D7. Le lien « Demander des avis » (Anthony)

- **Leçon** : L8, scène 2 « Votre lien d'avis ».
- **Page** : fiche de DIGITA → « Demander des avis ».
- **Clics** : « Demander des avis » → montrer le lien → « Copier » → fermer. Le QR code est créé au
  montage, ou filmé par Claude dans un outil public.
- **Durée** : 45 s.
- **À flouter** : rien (le lien d'avis est public).

### D8. Répondre à un avis, signaler un avis (Anthony)

- **Leçon** : L9, scènes 2 à 4.
- **Page** : fiche de DIGITA → « Lire les avis ».
- **Clics** : ouvrir un avis réel de la fiche → « Répondre » → montrer la zone de réponse (taper le début
  du modèle 1 du kit, sans publier) → « Annuler » → sur le même avis, ouvrir le menu (trois points) →
  montrer « Signaler l'avis » → fermer sans signaler.
- **Durée** : 90 s.
- **À flouter** : **le nom et la photo de l'auteur de l'avis**, et le texte de l'avis s'il identifie une
  personne.

### D9. Le champ « Site web » (Anthony)

- **Leçon** : L11, scène 3.
- **Page** : fiche de DIGITA → « Modifier le profil » → « Contact ».
- **Clics** : faire défiler jusqu'à « Site web » → cliquer dans le champ → montrer l'adresse →
  « Annuler ». Peut se tourner à la suite de D4.
- **Durée** : 30 s.
- **À flouter** : le numéro de téléphone s'il est personnel.

### D10. Search Console (Anthony)

- **Leçon** : L14, scènes 2 et 3.
- **Page** : https://search.google.com/search-console.
- **Clics** :
  1. menu des propriétés → « Ajouter une propriété » → montrer les deux choix « Domaine » et « Préfixe de
     l'URL » → fermer sans valider ;
  2. propriété `digita.buzz` → « Performances » → montrer les courbes « Clics » et « Impressions » →
     onglet « Requêtes » → onglet « Pages ».
- **Durée** : 2 min.
- **À flouter** : l'e-mail du compte, **la liste des autres propriétés** (les sites de clients ne doivent
  pas apparaître) et, si on préfère, les chiffres exacts.

## Après le tournage

1. Anthony dépose les fichiers dans `~/Desktop/formation-google-captures/`.
2. Claude fait le montage sur l'iMac : coupes, zooms sur la zone utile, mise en valeur du curseur,
   floutage, voix « marin » calée sur les pauses, sous-titres alignés mot par mot, habillage DIGITA.
3. Chaque leçon concernée est rendue avec sa démonstration et vérifiée par retranscription avant d'être
   envoyée à Anthony.

Les noms de menus de Google Business Profile et de la Search Console changent parfois : suivre l'intitulé
le plus proche à l'écran.
