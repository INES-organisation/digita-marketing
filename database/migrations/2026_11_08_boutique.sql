-- Boutique DIGITA : vente en ligne des packs de master prompts et des workflows IA (python/digita/boutique.py).
-- Appliquer : python tools/apply_sql.py <url> ../database/migrations/2026_11_08_boutique.sql
-- Idempotent : peut être rejoué sans risque.

-- Produit acheté (identifiant de boutique.py) sur chaque ligne de commande de la boutique
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS product_slug VARCHAR(80);

-- Preuve de l'accord exprès du client (contenu numérique : renonciation à la rétractation,
-- art. L221-28 13° ; service : exécution avant la fin du délai, art. L221-25)
ALTER TABLE orders ADD COLUMN IF NOT EXISTS consent_text TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS consent_at TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS consent_ip VARCHAR(45);

-- Liens de téléchargement personnels (un par fichier acheté), limités en durée et en nombre
CREATE TABLE IF NOT EXISTS shop_downloads (
    token VARCHAR(64) PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT,
    product_slug VARCHAR(80) NOT NULL,
    file_name VARCHAR(120) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    downloads INT NOT NULL DEFAULT 0,
    max_downloads INT NOT NULL DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_shop_downloads_order ON shop_downloads (order_id);
