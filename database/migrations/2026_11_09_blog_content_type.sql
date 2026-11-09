-- Types de contenu du blog (plan de contenu du 09/11/2026) : guide, pas-a-pas, comparatif, actualite,
-- definition, modele. NULL = article d'origine, non classé. Idempotent.
ALTER TABLE blog_articles ADD COLUMN IF NOT EXISTS content_type VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_blog_articles_content_type ON blog_articles(content_type);
UPDATE blog_articles SET content_type = 'guide' WHERE slug IN ('agent-ia-repondre-clients-24h', 'automatiser-devis-artisan', 'boutique-en-ligne-reunion', 'budget-publicite-facebook-reunion', 'chatbot-whatsapp-entreprise', 'chatgpt-tpe-usages', 'newsletter-tpe', 'nom-de-domaine-entreprise', 'prise-rendez-vous-en-ligne', 'prix-site-internet-reunion', 'site-internet-artisan');
UPDATE blog_articles SET content_type = 'comparatif' WHERE slug IN ('instagram-ou-facebook-reunion', 'site-vitrine-ou-page-facebook');
UPDATE blog_articles SET content_type = 'pas-a-pas' WHERE slug IN ('audit-seo-lire-rapport', 'avis-google-entreprise', 'creer-logo-entreprise', 'fiche-google-reunion', 'gite-reunion-haute-saison', 'page-facebook-piratee', 'relances-automatiques-devis-factures', 'repondre-clients-pendant-les-fetes', 'rgpd-tpe-essentiel', 'saison-cyclonique-entreprise');
UPDATE blog_articles SET content_type = 'definition' WHERE slug IN ('landing-page-definition', 'lexique-ia-tpe', 'lexique-marketing-digital');
UPDATE blog_articles SET content_type = 'modele' WHERE slug IN ('bilan-digital-fin-annee', 'idees-publications-reseaux-sociaux', 'temps-perdu-taches-repetitives');
UPDATE blog_articles SET content_type = 'actualite' WHERE slug IN ('facture-electronique-tpe');
