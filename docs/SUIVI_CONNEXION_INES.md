# Suivi — Site DIGITA connecté à INES (rendez-vous, CRM, chatbot, outils, Solutions)

**Ouvert le :** 25/10/2026
**Objectif :** que chaque point de contact du site fonctionne réellement et aboutisse dans INES (CRM, Booking, Planning), sans promesse que le système ne tient pas.
**Lié à :** [ACCROCHES_TAGLINES_SEO.md](ACCROCHES_TAGLINES_SEO.md) §19-§21, [SUIVI_CONVERSION_PYTHON.md](migrations/SUIVI_CONVERSION_PYTHON.md)

---

## 1. État constaté le 25/10/2026 (tests en production)

| Élément | État | Constat |
| --- | --- | --- |
| Envoi des prospects au CRM INES (`/api/v1/contacts/ingest`) | ⚠️ | Fonctionne aujourd'hui, mais **0 prospect DIGITA dans le CRM** : le message de contact réel du 21/10 n'était jamais arrivé (envoi en arrière-plan, aucune nouvelle tentative, journaux perdus au redéploiement). Rattrapé à la main le 25/10. |
| Rendez-vous du chatbot (`/api/chatbot/slots`, `/api/chatbot/appointment`) | ❌ | Créneaux codés en dur (9 h-17 h tous les jours), table locale `appointments`, **aucun lien avec INES**. Le widget du chat n'appelle d'ailleurs jamais ces routes. |
| INES Booking (`/booking`) | ⚠️ | Un type de rendez-vous existe : « Appel stratégique » (`appel-strat-gique`, 30 min, mardi et jeudi 9 h-18 h). 0 réservation. API publique de disponibilités et de réservation disponible. |
| INES Planning (`/planning`) | ❌ | Module séparé : une réservation Booking n'y apparaît pas, et un événement du planning ne bloque pas les créneaux Booking. API réservée aux utilisateurs connectés. |
| Chatbot | ⚠️ | Répond via l'IA d'INES, mais : ne connaît ni les offres ni les prix (« le prix dépend… »), ne capte pas les coordonnées (la qualification n'est jamais appelée), conversation perdue à chaque changement de page, pas de prise de rendez-vous. |
| Audit SEO | ✅ | Fonctionne (ex. lp48.digita.buzz : 85/100). Pas d'appel à l'action après le résultat. |
| Générateur de meta descriptions | ❌ | L'IA renvoie un texte Markdown complet (titre, liste, « 158/160 ✓ ») au lieu de la seule description : compteur à 520 caractères, copie inutilisable. |
| Calendrier éditorial | ⚠️ | Fonctionne mais dates en **janvier 2025** et Markdown brut affiché. |
| Calculateur de ROI | ✅ | Fonctionne. |
| Liens des pages Solutions et Outils | ✅ | Tous valides. |
| Page Solutions | ⚠️ | Reprend les services (site, marketing, e-commerce) au lieu de packs clés en main. |

## 2. Plan

### Lot A — Digita (ce dépôt)

| # | Tâche | Statut |
| --- | --- | --- |
| A1 | Pied de page : « Diagnostic gratuit » sous le séparateur | ✅ |
| A2 | Envoi au CRM INES fiable : 3 tentatives, journal d'erreur | ✅ |
| A3 | Créneaux réels INES Booking sur `/diagnostic` (choix du jour et de l'heure, téléphone obligatoire), réservation dans INES, e-mail de confirmation avec lien d'annulation (`/rendez-vous/annuler` : la page demande une confirmation, un aperçu de lien n'annule rien). Pas de créneau à moins de 2 h ni au-delà de 3 semaines. Si INES ne répond pas, la demande devient une demande de rappel (rien n'est perdu). | ✅ |
| A4 | API du chatbot (`slots`, `appointment`) branchée sur INES Booking | ✅ |
| A5 | Chatbot : connaissance des offres et prix réels, du diagnostic et du téléphone ; capture automatique des coordonnées → CRM INES ; conversation conservée entre les pages ; bouton « Réserver un appel » dans le chat | ✅ |
| A6 | Générateur de meta : une seule description propre | ✅ |
| A7 | Calendrier éditorial : dates à partir d'aujourd'hui, tableau lisible | ✅ |
| A8 | Outils : appel à l'action « diagnostic » après chaque résultat | ✅ |
| A9 | Page Solutions refaite en packs clés en main (§3), bouton « Parler de ce pack » → `/diagnostic?pack=…` (le pack suit jusqu'au CRM) | ✅ |
| A10 | Fenêtre de diagnostic de l'accueil : lien « choisissez vous-même votre créneau » | ✅ |

### Lot B — INES (dépôt INES)

| # | Tâche | Statut |
| --- | --- | --- |
| B1 | Une réservation Booking crée l'événement correspondant dans le Planning (même identifiant) ; l'annulation le supprime | ✅ |
| B2 | Les événements du Planning bloquent les créneaux Booking qu'ils chevauchent (un événement sans heure bloque la journée) ; refus d'une réservation sur un créneau occupé | ✅ |
| B2b | Créneaux passés : filtrés côté site (préavis de 2 h, heure de La Réunion). La page publique INES `/booking` affiche encore les heures déjà passées du jour (serveur en UTC) | ⏳ |
| B3 | Brancher les prospects du site sur l'agent « Acquisition 24/7 » (premier message, relance J+2) | ⏳ phase 2 |
| B4 | A/B test des pages externes (voir ACCROCHES §19.3) | ⏳ phase 2 |

## 3. Packs Solutions (proposition — prix à valider)

Les packs combinent des services du catalogue (`services_catalog.py`). Les prix des composants affichés sont ceux du catalogue ; **le prix de chaque pack n'est pas affiché** (« tarif établi après le diagnostic gratuit ») tant qu'il n'est pas validé.

| Pack | Pour qui | Contenu |
| --- | --- | --- |
| Système d'acquisition automatique | Toute TPE/PME qui veut des demandes régulières | Landing page de vente, campagnes Meta/Google, CRM avec relances automatiques, assistant IA 24/7, tableau de bord |
| Boutique e-commerce prête à vendre | Commerçants qui lancent une niche | Boutique optimisée SEO, fiches produits, paiement et livraison, campagne de lancement |
| Prise de rendez-vous automatisée | Santé, beauté, bien-être, services | Site + agenda en ligne, rappels e-mail/SMS contre les rendez-vous manqués, collecte d'avis Google |
| Devis et relances automatiques | Artisans, BTP | Formulaire de devis qualifié, CRM, relances automatiques, suivi des chantiers signés |
| Visibilité locale 974 | Commerces et services de proximité | Site vitrine, fiche Google Business optimisée, avis clients, référencement local |

**Décision attendue :** prix de lancement de chaque pack (ou garder « sur devis »).

## 4. Configuration à vérifier dans INES

- `/booking` → type « Appel stratégique » : jours et heures réels de disponibilité (aujourd'hui mardi et jeudi 9 h-18 h), dates bloquées (congés). Le site lit ces règles en direct.
- Variable `INES_BOOKING_SLUG` du conteneur Digita (par défaut `appel-strat-gique`) si le type est renommé.

## 5. Journal

| Date | Étape |
| --- | --- |
| 25/10/2026 | État des lieux en production (§1) ; prospect du 21/10 rattrapé dans le CRM INES ; plan ouvert. |
| 25/10/2026 | Lots A et B1-B2 livrés : tests Digita (56) et INES (test_booking_planning_sync + Planning + Booking) verts, déployés sur les deux conteneurs. |
| 25/10/2026 | Vérifié en production de bout en bout : réservation depuis `/diagnostic` → créneau dans INES Booking, événement « appel » dans le Planning (même id), contact « Lead DIGITA » dans le CRM, créneau retiré des disponibilités ; annulation par le lien de l'e-mail → réservation annulée, événement du Planning supprimé, créneau de nouveau proposé. Données de test supprimées. Chatbot : prix réels cités. Générateur de meta : description seule. |
