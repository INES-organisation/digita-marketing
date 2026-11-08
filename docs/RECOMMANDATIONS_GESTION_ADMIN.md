# Gestion professionnelle de DIGITA, connectée à INES : état et recommandations (8 novembre 2026)

> **État au 08/11/2026 (soir) :** P1 1, 2, 3, 6, 7 et 8 livrés dans DIGITA ; P1 4 et 5 livrés (route des ventes, livre des recettes, plafonds et déclarations dans INES, PR INES #83, et envoi depuis DIGITA). Détail : [SUIVI_BOUTIQUE_FACTURATION_RGPD.md](SUIVI_BOUTIQUE_FACTURATION_RGPD.md). Restent les P2 et P3.

Revue en lecture seule du code de DIGITA (admin, espace client, paiements) et d'INES. Aucune modification n'a été faite pendant la revue.

## Principe de répartition proposé

| Domaine | Source de vérité | DIGITA fait | INES fait |
|---|---|---|---|
| Prix, produits, contenus (blog, formations, boutique) | DIGITA | Catalogue, pages, livraison des accès et téléchargements | Relit les prix (/api/catalogue) |
| Leads, CRM, affaires, réponses | INES | Formulaires, copie de secours locale | CRM, affaires, réponses, relances |
| Rendez-vous | INES Booking | Prise de rendez-vous sur le site | Agenda |
| Devis, factures, avoirs, livre des recettes, URSSAF | INES (une seule série de numéros) | Envoie chaque vente payée et chaque remboursement | Documents, comptabilité, déclarations |
| Newsletter automatique | DIGITA | Envoi du lundi, désabonnement | Envoi technique, journal, liste noire |
| Campagnes e-mailing | INES (Listmonk) | Rien : page factice à retirer | Campagnes |
| Comptes et connexion | INES (SSO) + compte local | Connexion, mot de passe | Identité unique |

## État de l'admin DIGITA

- **Fonctionne :** Messages (fiche, lu/répondu, réponse e-mail et WhatsApp), Newsletter (abonnés, export, aperçu de la lettre), Boutique (produits, ventes, fichiers), Articles, Médias, Projets (suivi), mot de passe.
- **Partiel :** Dashboard (pas de chiffre d'affaires ni de commandes ni de rendez-vous, « taux de conversion » sans signification), Formations (modules et leçons en lecture seule, pas de quiz ni de codes promo ; la suppression d'une formation efface les inscriptions des acheteurs), Projets (prix saisi à la main, pas de devis ni de paiement, pas d'e-mail au client).
- **Factice ou cassé :**
  - Campagnes : données de démonstration écrites en dur, liens en 404.
  - Webhooks : rien n'est enregistré.
  - Analytics : requêtes sur des colonnes et tables qui n'existent pas, et aucune visite n'est enregistrée.
  - Webhook Webox : exige une session admin, donc ne peut pas être appelé.
- **Absent :**
  - toutes les commandes et factures (formations comprises) ;
  - les utilisateurs ;
  - les rendez-vous (stockés mais jamais affichés) ;
  - les conversations du chatbot ;
  - les codes promo ;
  - l'export ou la suppression RGPD d'une personne ;
  - un journal des actions ;
  - la double authentification.

## Bugs constatés

1. **Redirection après connexion :** tout le monde est envoyé vers /admin/dashboard, puis les clients sont renvoyés à l'accueil. Le retour prévu vers la page d'origine (`redirect_after_login`) n'est jamais lu. Conséquence : un client qui se connecte pour acheter un pack perd le fil de son achat.
2. **Lien mort** dans l'espace client : « Optimiser mon score » pointe vers /intelligence/chatbot, qui n'existe pas.
3. **Numéro de facture attribué dès la création de la commande** (avant le paiement), calculé par comptage. Les paiements abandonnés créent des trous dans la numérotation, et un doublon reste possible : la facture échouerait alors après le paiement.
4. **Formulaires de l'admin sans jeton CSRF** (risque limité par le cookie de session SameSite=Lax).

## Obligations légales (micro-entrepreneur vendant en ligne)

| Obligation | État |
|---|---|
| Numérotation continue des factures | À corriger (point 3 ci-dessus). Deux séries existent (DIGITA « DM- », INES « FAC- ») pour la même entreprise. |
| Mentions de la facture | Il manque le nom et l'adresse de l'acheteur (seul l'e-mail figure). Pour un client pro : pénalités et indemnité de 40 €. Pas de facture figée ni de PDF archivé. |
| Conservation 10 ans | Risque : supprimer un utilisateur pourrait effacer ses factures (cascade à vérifier en base). |
| Livre des recettes, plafond de CA, URSSAF | Absents. Dans INES, ces pages sont des maquettes, et les ventes de DIGITA n'y arrivent pas. |
| Accord exprès / rétractation | Conforme pour la boutique. Absent pour les formations payantes. |
| Consentement newsletter | Pas de case à cocher ni de preuve (date, IP, texte). Pas d'en-tête List-Unsubscribe. |
| Droits RGPD | Aucun outil d'export ou d'effacement. Les durées de conservation annoncées ne sont appliquées par aucune purge. |
| Cookies | Conforme (cookie de session seul). |
| Médiateur | Adhésion CM2C en cours. |

## Recommandations

### P1 : conformité et fiabilité (à faire en premier)

| # | Quoi | Où | Effort |
|---|---|---|---|
| 1 | Redirection après connexion vers la page d'origine (sinon : admin pour l'admin, /espace-client pour un client) | DIGITA | S |
| 2 | Numéro de facture attribué au paiement seulement, par une séquence en base, sans trou ni doublon | DIGITA | S |
| 3 | Facture complète et figée : nom, adresse (et SIREN pour un pro) demandés avant le paiement, mentions pro, PDF archivé, pas de suppression en cascade | DIGITA | M |
| 4 | Chaque vente payée et chaque remboursement envoyés à INES (recette ou facture), pour qu'INES tienne le livre des recettes unique. Il faut une route INES accessible par clé API. | INES (route) + DIGITA (appel) | M |
| 5 | Livre des recettes réel, alerte de plafond de CA, récapitulatif pour la déclaration URSSAF | INES | M |
| 6 | Accord exprès au paiement d'une formation, comme pour la boutique | DIGITA | S |
| 7 | Droits RGPD : recherche par e-mail, export, effacement ou anonymisation (factures conservées), purge automatique selon les durées annoncées, propagée à INES | DIGITA + INES | M |
| 8 | Retirer le factice : pages Campagnes et Webhooks, carte « Nouvelle campagne », lien /intelligence/chatbot | DIGITA | S |

### P2 : gestion au quotidien

| # | Quoi | Où | Effort |
|---|---|---|---|
| 9 | Page « Commandes et factures » : toutes les ventes, filtres, facture, renvoi des liens, remboursement et avoir | DIGITA (+ avoirs INES) | M |
| 10 | Dashboard utile : CA du mois et de l'année, commandes, rendez-vous à venir, leads de la semaine | DIGITA | S |
| 11 | Analytics : mesure d'audience sans cookie qui fonctionne, ou retrait de la page | DIGITA | S-M |
| 12 | Newsletter : case de consentement et preuve, List-Unsubscribe, synchronisation des abonnés et désinscriptions avec INES (Listmonk / liste noire) | DIGITA + INES | M |
| 13 | Messages : remonter le statut lu/répondu dans INES, pour n'avoir qu'une seule boîte de réception de référence | DIGITA → INES | S-M |
| 14 | Projets : devis et affaire créés dans INES depuis le brief, statut de paiement lu depuis INES, e-mail au client à chaque message, webhook Webox sécurisé par secret | DIGITA + INES | M |
| 15 | Sécurité : jeton CSRF sur l'admin, changements d'état en POST, journal des connexions et actions, connexion admin par SSO INES ou 2FA | DIGITA | M |
| 16 | Rendez-vous et utilisateurs visibles dans l'admin (lecture, avec lien vers INES) | DIGITA | S |

### P3 : confort

| # | Quoi | Où | Effort |
|---|---|---|---|
| 17 | Éditeur des modules, leçons et quiz des formations ; codes promo | DIGITA | L |
| 18 | Conversations du chatbot lisibles dans l'admin | DIGITA | S |
| 19 | Coordonnées de l'entreprise centralisées en un seul endroit (aujourd'hui répétées dans une dizaine de gabarits) | DIGITA | S |
| 20 | Prix de la boutique modifiables depuis l'admin (/api/catalogue reste la référence pour INES) | DIGITA | M |
| 21 | Clé TinyMCE pour l'éditeur d'articles | DIGITA | S |

## Côté INES (pour information, Anthony s'en occupe)

- Pages « livre des recettes » et « déclarations sociales » en maquette.
- Pas de route d'ingestion de facture par clé API.
- La facturation compte les brouillons dans la numérotation et permet de supprimer une facture quel que soit son statut.
- Les demandes RGPD sont fictives.

## Points non vérifiés

- Schéma PostgreSQL exact en production (cascade des factures, colonnes lues par Analytics).
- Plantage effectif de la page Analytics.
- Fusion des étiquettes par INES sur /contacts/ingest.
- Consultation de la liste noire par l'envoi transactionnel d'INES.
