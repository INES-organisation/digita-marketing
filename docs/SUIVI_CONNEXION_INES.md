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
| B3 | Brancher les prospects du site sur l'agent « Acquisition 24/7 » | ✅ lot C |
| B4 | A/B test des pages externes (voir ACCROCHES §19.3) | ⏳ phase 2 |

## 3. Offres de la page Solutions (26/10/2026)

**Systèmes d'acquisition IA 24/7** (`digita/solutions.py` → `OFFERS`, moteur : agent d'acquisition INES) :

| Offre | Mise en service | Abonnement | Fonctions INES utilisées |
| --- | --- | --- | --- |
| Standardiste Messenger & Insta 24/7 | 490 € à 890 € HT | 149 € à 249 € HT/mois (300 conversations) | Messenger, Instagram, qualification, RDV au Planning, alertes SMS/e-mail |
| Commercial & Standardiste IA Complet | 1 200 € à 2 400 € HT | 390 € à 590 € HT/mois (500 conversations, 200 min d'appels) | + accueil vocal Twilio, rappel par SMS, devis brouillon `/facturation` |
| Machine à Leads Clé en Main | 1 500 € HT | 990 € à 1 800 € HT/mois + budget Meta | Lead Ads + premier contact SMS/e-mail immédiat + qualification par SMS |

**Autres packs** (`PACKS`) : Boutique e-commerce prête à vendre, Visibilité locale 974 (prix du pack établi après diagnostic). Les packs « Système d'acquisition », « Prise de RDV » et « Devis et relances » sont retirés : couverts par les offres ci-dessus.

**Argumentaire publié** : uniquement des faits et calculs vérifiables (35 h contre 168 h par semaine ; 2 000 € ÷ 149 € = plus d'un an d'abonnement ; 5 000 € ≈ 12,8 mois à 390 €).
**Non publiés, à sourcer avant usage écrit** : « plus de 60 % des prospects écrivent le soir ou le week-end », « 8 prospects sur 10 contactent un concurrent sans réponse sous 15 minutes », « un télésecrétariat coûte 1 200 € à 2 500 €/mois ». Utilisables à l'oral en rendez-vous, pas sur le site ni dans les publicités sans source (Code de la consommation, art. L121-2).
**À vérifier** : disponibilité de numéros Twilio en +262 (La Réunion) — sinon « numéro dédié » (métropole) ; le site dit « numéro dédié », sans « local ».

## 4. Configuration à vérifier dans INES

- `/booking` → type « Appel stratégique » : jours et heures réels de disponibilité (aujourd'hui mardi et jeudi 9 h-18 h), dates bloquées (congés). Le site lit ces règles en direct.
- Variable `INES_BOOKING_SLUG` du conteneur Digita (par défaut `appel-strat-gique`) si le type est renommé.

## 6. Lot C — système d'acquisition complet (26/10/2026)

### 6.1 Ce qui existait dans INES (vérifié dans le code et en production)

| Brique | État trouvé |
| --- | --- |
| Agent d'acquisition 24/7 (`/crm/acquisition`) : Messenger, Instagram, Lead Ads, téléphone Twilio | Code complet, **jamais configuré** pour DIGITA (aucune configuration, aucune conversation) |
| Lead Ads | Contact + affaire + alerte, mais **aucun recontact du prospect** (promis par l'offre « Machine à leads ») |
| Heure des RDV de l'agent | **Europe/Paris figé** : décalage de 3 h pour La Réunion |
| SMS entrants | Inexistants : l'agent ne pouvait pas poursuivre une conversation par SMS |
| Devis brouillon `/facturation` | Inexistant (promis par l'offre « Commercial IA ») |
| Notifications in-app | Bloc « Affaires » **cassé** (champs `name`/`status` inexistants, erreur avalée : aucune affaire jamais notifiée) ; rien pour les prospects des sites, les conversations de l'agent ni les RDV Booking |
| Campagnes e-mail INES (`/api/email-automation`) | Destinataires saisis à la main, fournisseur à configurer : non retenu pour la newsletter DIGITA |

### 6.2 Livré

| # | Tâche | Dépôt | Statut |
| --- | --- | --- | --- |
| C1 | Canal « Site web » : `POST /api/v1/external/acquisition/leads` (clé API) → contact (sans doublon, recherche par e-mail/téléphone), affaire, alerte e-mail/SMS du propriétaire | INES | ✅ |
| C2 | Premier contact automatique (`outreach`) des leads web et **Lead Ads** : SMS (Twilio) + e-mail (réponse au propriétaire), lien de réservation | INES | ✅ |
| C3 | SMS entrants (`/webhooks/twilio/sms`, branché automatiquement sur le numéro) : l'agent poursuit la qualification par SMS | INES | ✅ |
| C4 | Devis brouillon dans `/facturation` pour chaque nouveau lead (option, TVA réglable) | INES | ✅ |
| C5 | Fuseau horaire de l'agent réglable (Indian/Reunion) ; lien de réservation donné par l'agent | INES | ✅ |
| C6 | Notifications in-app : affaires (réparé), nouveaux prospects (sites + agent), conversations non lues, RDV réservés/annulés | INES | ✅ |
| C7 | Écran `/crm/acquisition` : fuseau, lien de réservation, premier contact, devis brouillon, TVA, canaux Site web et SMS ; enregistrement qui n'écrase plus les réglages absents | INES | ✅ |
| C8 | Digita → agent INES : diagnostic (premier contact par SMS seulement, Digita envoie déjà son e-mail), contact (SMS + e-mail), RDV / chatbot / brief projet (sans relance) ; repli sur la fiche CRM simple si l'agent est désactivé | Digita | ✅ |
| C9 | Newsletter : seulement le contenu de la semaine (plus d'envoi sans nouveauté), marque DIGITA, bloc diagnostic ; désinscription marquée dans le CRM (tag `newsletter-desabonne`) ; expéditeur des e-mails « DIGITA » | Digita | ✅ |
| C10 | Page Solutions : les 3 offres d'acquisition, argumentaire vérifiable, 2 packs ; chatbot informé des offres et prix | Digita | ✅ |
| C11 | Configuration de l'agent pour DIGITA en production (fuseau Réunion, lien `/diagnostic`, alertes e-mail, canal site web) | INES (prod) | ✅ |
| C12 | Webhook Brevo réparé : un hard bounce, une ouverture ou un clic plantaient (date avec fuseau sur colonne sans fuseau) — adresses jamais blacklistées, suivi de délivrabilité vide. Trouvé pendant le test du 26/10 | INES | ✅ |

### 6.3 Reste à faire par vous (comptes externes)

1. **Page Facebook DIGITA → INES** : `/crm/acquisition` → « Connecter Facebook » puis choisir la page (Messenger, Instagram, Lead Ads). Nécessite votre connexion Facebook.
2. **Twilio** (appels + SMS) : créer le compte, acheter un numéro, saisir SID et token dans `/agents-perso/settings`, puis rattacher le numéro dans `/crm/acquisition` (les webhooks appel et SMS se règlent tout seuls). Sans Twilio : pas de SMS (premier contact par e-mail seulement), pas d'accueil vocal, pas d'alerte SMS.
3. **Numéro d'alerte SMS** dans `/crm/acquisition` une fois Twilio actif.
4. **Prix exacts** dans les fourchettes, au cas par cas, pendant le diagnostic.

### 6.4 Limites connues

- L'agent réserve dans le Planning en évitant les chevauchements, mais ne lit pas les horaires du type de rendez-vous Booking : préciser les horaires dans « Activité, horaires… » de `/crm/acquisition` (fait pour DIGITA).
- Un e-mail de réponse du prospect arrive dans votre boîte (Reply-To), pas dans la conversation de l'agent ; seuls les SMS poursuivent la conversation automatiquement.

## 5. Journal

| Date | Étape |
| --- | --- |
| 25/10/2026 | État des lieux en production (§1) ; prospect du 21/10 rattrapé dans le CRM INES ; plan ouvert. |
| 25/10/2026 | Lots A et B1-B2 livrés : tests Digita (56) et INES (test_booking_planning_sync + Planning + Booking) verts, déployés sur les deux conteneurs. |
| 26/10/2026 | Lot C livré (§6) : tests INES (acquisition, notifications, devis, booking, planning : 76) et Digita (58) verts. |
| 25/10/2026 | Vérifié en production de bout en bout : réservation depuis `/diagnostic` → créneau dans INES Booking, événement « appel » dans le Planning (même id), contact « Lead DIGITA » dans le CRM, créneau retiré des disponibilités ; annulation par le lien de l'e-mail → réservation annulée, événement du Planning supprimé, créneau de nouveau proposé. Données de test supprimées. Chatbot : prix réels cités. Générateur de meta : description seule. |
