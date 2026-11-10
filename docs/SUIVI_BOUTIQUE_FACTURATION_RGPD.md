# Suivi : boutique, facturation, RGPD et gestion de l'admin (8 novembre 2026)

**Ouvert et livré le :** 08/11/2026
**Lié à :** [AUDIT_COHERENCE_PAGES.md](AUDIT_COHERENCE_PAGES.md) (audit des pages, 6 lots), [RECOMMANDATIONS_GESTION_ADMIN.md](RECOMMANDATIONS_GESTION_ADMIN.md) (revue de l'admin et priorités), [SUIVI_CONNEXION_INES.md](SUIVI_CONNEXION_INES.md) §8 (ventes vers le livre des recettes INES)

## 1. Boutique (/boutique)

| Élément | Où | Détail |
|---|---|---|
| Produits et prix | `python/digita/boutique.py` | Source unique : 4 packs de master prompts (29 €, lot des 4 à 79 €) et les 10 « Workflows Entreprise » d'INES vendus installés (490 € à 1 290 €, calés sur la grille « Automatisation » de /tarifs), maintenance 49 €/mois. `OPEN = True`. Matériel : lien vers MultiProShop. |
| Fichiers vendus | `python/digita/boutique_files/` | Pour chaque pack : PDF mis en page (couverture DIGITA, sommaire, prompts encadrés, variables surlignées) + version texte (Markdown) pour copier-coller. Le lot des 4 livre les 8 fichiers. Hors de `public/` : jamais servis directement. |
| Régénérer les PDF | `python/tools/build_boutique_pdfs.py` | Après toute modification d'un `.md` : `pip install markdown playwright` puis `python tools/build_boutique_pdfs.py [chemin/vers/chrome]`, et committer les PDF. |
| Pages | `routes/shop.py`, `templates/app/Views/boutique/` | `/boutique` (liste), `/boutique/<produit>` (fiche ; les anciennes adresses PHP renvoient en 301 vers /solutions), `/boutique/commander/<produit>` (récapitulatif), `/telecharger/<jeton>`. |
| Commande | `routes/shop.py`, `models/shop.py` | Connexion obligatoire. Coordonnées de facturation (nom et adresse obligatoires, société et SIRET facultatifs). Deux cases : CGV, et accord exprès (pack : renonciation à la rétractation, art. L221-28 13° ; workflow : exécution avant la fin du délai, art. L221-25). Texte coché, date et IP enregistrés dans `orders.consent_*`. Ligne de commande : `product_type = 'pack'` (seule valeur adaptée autorisée par la contrainte de la table) et `product_slug`. |
| Paiement | `services/stripe.py` | Stripe Checkout via INES (`create_checkout`), validé au retour sur /paiement/succes et par le rattrapage nocturne `reconcile-orders`. |
| Livraison | `models/shop.py`, `services/email.py` | Liens personnels (`shop_downloads`) valables 30 jours, 5 téléchargements, renouvelables depuis « Mes commandes ». E-mail « Votre commande DIGITA » avec les liens ; pour un workflow, annonce du rendez-vous de lancement. Fiche client dans INES taguée `client` et `boutique:<produit>`. |
| Liste d'attente | `routes/leads.py` | `POST /boutique/prevenir` (utilisée quand `OPEN = False`) : message de contact + lead INES tagué `liste-attente-boutique`. |

## 2. Factures (conformité)

- **Numérotation :** le numéro est attribué au paiement seulement (plus à la création de la commande), par un compteur annuel `invoice_counters`. Format : DM-2026-0001, DM-2026-0002… Le numéro est pris dans la même instruction SQL que l'insertion de la facture : la série est continue, sans trou ni doublon (`models/invoice.py`).
- **Facture figée :** vendeur, acheteur et lignes sont copiés dans `invoices.snapshot` à l'émission ; /facture/:id s'affiche à partir de cette copie. La facture porte le nom, l'adresse, la société et le SIRET de l'acheteur, et les mentions pour les clients pros (pénalités de retard, indemnité de 40 €).
- **Conservation 10 ans :** supprimer un compte détache ses factures (`ON DELETE SET NULL`) au lieu de les effacer ; une commande facturée ne peut plus être supprimée (`ON DELETE RESTRICT`).
- **Formations payantes :** mêmes coordonnées de facturation et accord exprès que la boutique (renonciation à la rétractation pour un contenu numérique), jeton CSRF ajouté au formulaire.
- **Livre des recettes :** chaque facture payée est envoyée à INES (`POST /api/v1/external/sales`, voir SUIVI_CONNEXION_INES.md §8). Nature « prestation » : pour une micro-entreprise, les formations, contenus numériques et installations sont des prestations de services (BIC, 21,2 %). `invoices.ines_synced_at` garde la trace ; le rattrapage nocturne renvoie ce qui a échoué.

## 3. RGPD

- **Admin › RGPD** (`/admin/rgpd`, `models/privacy.py`) : recherche par e-mail dans toutes les tables qui contiennent des données personnelles, export JSON à remettre à la personne, effacement après confirmation (l'adresse est à recopier). Les commandes et factures sont conservées 10 ans, détachées du compte. Le contact du CRM INES est à supprimer à la main dans INES.
- **Purge automatique** (dans le rattrapage nocturne `reconcile-orders`) :
  - messages de contact, rendez-vous, qualifications et conversations du chat de plus de 3 ans ;
  - journaux techniques (`page_views`, `tool_usage`, `conversions`) de plus de 12 mois ;
  - jetons de réinitialisation expirés ;
  - comptes sans connexion ni commande depuis 3 ans (`users.last_login_at`, mis à jour à chaque connexion).

## 4. Admin et espace client

| Changement | Détail |
|---|---|
| Messages | Fiche d'un message (`/admin/contacts/<id>`) : texte complet, ouverture = « Lu », réponse par e-mail pré-remplie ou WhatsApp (numéro converti en +262), « Répondu », précédent/suivant. Statuts en français. |
| Newsletter | Encadré « La lettre DIGITA » : envoi du lundi 10 h, contenu de la prochaine lettre ou « pas d'envoi », aperçu exact (`/admin/newsletters/apercu`). Historique des envois : INES, Communications › Journal, « digita/newsletter ». |
| Boutique | `/admin/boutique` : produits, prix, ventes, chiffre d'affaires, dernières commandes avec la date de l'accord exprès, lecture et téléchargement des fichiers. |
| Mot de passe | `/mon-compte/mot-de-passe` pour l'admin et les clients (mot de passe actuel exigé, 8 caractères minimum). |
| Connexion | Retour à la page d'origine (`redirect_after_login`), sinon /admin/dashboard pour l'admin et /espace-client pour un client. |
| Dashboard | « Ventes en ligne du mois » (et de l'année) à la place du « taux de conversion » ; raccourcis Boutique et RGPD. |
| Retirés | Pages Campagnes (données de démonstration) et Webhooks (factices) : redirections vers la newsletter et le dashboard. Lien mort « Optimiser mon score » de l'espace client → diagnostic. |

## 5. Base de production (migrations appliquées le 08/11/2026, avec l'accord d'Anthony)

| Fichier | Contenu |
|---|---|
| `database/migrations/2026_11_08_boutique.sql` | `order_items.product_slug`, `orders.consent_text/consent_at/consent_ip`, table `shop_downloads` |
| `database/migrations/2026_11_08_factures.sql` | table `invoice_counters`, `orders.billing_company/billing_siret`, `invoices.snapshot/ines_synced_at`, contraintes de conservation des factures, `users.last_login_at` |

Application : envoyées par l'entrée standard dans le conteneur `digita-web` (même découpage que `tools/apply_sql.py`). Les deux sont idempotentes. Avant la migration des factures, la production n'avait ni facture ni commande.

## 6. Reste à faire

| Qui | Quoi |
|---|---|
| Anthony | Un achat test réel (puis remboursement dans Stripe) pour valider le circuit complet : facture DM-2026-0001, e-mail, téléchargement, fiche INES, ligne du livre des recettes. |
| Anthony | Vérifier que les 10 workflows tournent en production dans INES avant la première commande d'installation. |
| Anthony | Médiateur : l'adhésion à CM2C est en attente. Donner l'adresse du contrat pour l'indiquer dans les CGV (art. 18). |
| À faire (P2) | Page « Commandes et factures » de l'admin (remboursements et avoirs envoyés à INES en `kind: refund`), mesure d'audience sans cookie, consentement newsletter et synchronisation avec INES, sécurité de l'admin (CSRF, journal, 2FA ou SSO), statut des messages remonté dans INES. Voir RECOMMANDATIONS_GESTION_ADMIN.md. |

## 7. Journal

| Date | Étape |
|---|---|
| 08/11/2026 | Audit de cohérence des pages et 6 lots livrés (voir AUDIT_COHERENCE_PAGES.md). |
| 08/11/2026 | Boutique ouverte : packs (Markdown puis PDF), 10 workflows, paiement, téléchargements, admin Boutique ; migration boutique appliquée ; tests 108 puis 109. |
| 08/11/2026 | Admin : messages, newsletter, mot de passe ; revue de l'admin et recommandations (RECOMMANDATIONS_GESTION_ADMIN.md) ; tests 111. |
| 08/11/2026 | P1 de la revue : connexion, factures conformes, accord exprès des formations, RGPD, retrait du factice ; migration factures appliquée ; tests 116. |
| 08/11/2026 | INES : PR INES-organisation/INES#83 fusionnée et déployée (route des ventes, livre des recettes réel, plafonds, déclarations URSSAF, numérotation des factures INES). Vérifié en production que la route accepte la clé de DIGITA (réponse 422 sur un envoi volontairement incomplet, rien d'enregistré). |

## Packs de prompts : section « Dans INES » (9 et 10 novembre 2026)

- 9/11 : chaque pack (`python/digita/boutique_files/pack-*.md`, PDF régénérés) indique que les prompts
  s'utilisent aussi dans le chat d'INES, et que les fonctions d'IA d'INES consomment des crédits, y
  compris avec le compte gratuit.
- 10/11 : INES permet enfin d'enregistrer ses propres prompts (PR INES #117 : vue « Mes prompts » de
  `/codex/templates`, prompts privés, bouton « Enregistrer » sur la bibliothèque). Les packs expliquent
  le chemin : « Templates » → « Mes prompts » → « Nouveau prompt » → « Enregistrer ». Libellés relevés
  dans le code de la PR (`MyPromptsPanel.tsx`).
- **À ne mettre en ligne sur digita.buzz qu'une fois la PR INES #117 déployée**, sinon les acheteurs
  chercheraient un bouton qui n'existe pas encore.
- PDF : `tools/build_boutique_pdfs.py` (Playwright). Si le paquet Python Playwright manque, générer le
  HTML avec `build_html` et imprimer avec Playwright pour Node (même rendu A4, même pied de page).
