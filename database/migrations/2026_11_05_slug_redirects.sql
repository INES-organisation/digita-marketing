-- Anciennes adresses des articles et formations → adresse actuelle (301), voir python/digita/redirects.py.
-- Appliquer : python tools/apply_sql.py <url> ../database/migrations/2026_11_05_slug_redirects.sql
CREATE TABLE IF NOT EXISTS slug_redirects (
    kind VARCHAR(20) NOT NULL,
    old_slug VARCHAR(255) NOT NULL,
    new_slug VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (kind, old_slug)
);
