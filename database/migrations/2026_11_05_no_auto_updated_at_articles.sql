-- updated_at des articles et formations = date de la dernière modification du contenu (<lastmod> du
-- sitemap). Le déclencheur repris de MySQL (ON UPDATE CURRENT_TIMESTAMP) la remettait au jour pour un
-- simple +1 vue, une inscription ou une note ; les mises à jour de l'admin fixent déjà updated_at = NOW().
DROP TRIGGER IF EXISTS blog_articles_updated_at_on_update ON blog_articles;
DROP TRIGGER IF EXISTS formations_updated_at_on_update ON formations;
