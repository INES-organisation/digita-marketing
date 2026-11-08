-- Factures conformes (revue du 08/11/2026) : numérotation continue attribuée au paiement, coordonnées
-- de l'acheteur, facture figée, conservation 10 ans, envoi des ventes à INES (livre des recettes).
-- Appliquer : python tools/apply_sql.py <url> ../database/migrations/2026_11_08_factures.sql (idempotent)

-- Compteur par année : DM-2026-0001, DM-2026-0002… sans trou (numéro pris dans la même instruction
-- que l'insertion de la facture : si l'insertion échoue, le compteur n'avance pas)
CREATE TABLE IF NOT EXISTS invoice_counters (
    year INT PRIMARY KEY,
    last_number INT NOT NULL
);

-- Coordonnées de facturation saisies au paiement (le nom et l'adresse existaient déjà)
ALTER TABLE orders ADD COLUMN IF NOT EXISTS billing_company VARCHAR(150);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS billing_siret VARCHAR(20);

-- Facture figée : vendeur et lignes copiés au moment de l'émission ; suivi de l'envoi à INES
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS snapshot TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS ines_synced_at TIMESTAMP;

-- Conservation 10 ans : supprimer un compte ou une commande ne doit plus effacer de facture
ALTER TABLE invoices ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS invoices_invoices_ibfk_2;
ALTER TABLE invoices ADD CONSTRAINT invoices_invoices_ibfk_2 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS invoices_invoices_ibfk_1;
ALTER TABLE invoices ADD CONSTRAINT invoices_invoices_ibfk_1 FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT;

-- RGPD : dernière connexion, pour effacer les comptes inactifs depuis 3 ans (politique de confidentialité)
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;
