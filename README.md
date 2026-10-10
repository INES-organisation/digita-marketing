# Digita Marketing

Site de l'agence Digita Marketing (https://digita.buzz) : vitrine, blog, formations en ligne,
espace élève, paiement, projets clients et administration.

Application Python (FastAPI + Jinja2) dans `python/`, base PostgreSQL. L'ancienne version PHP
(hébergement OVH) a été retirée après conversion ; elle reste dans l'historique git
(dernier commit PHP : `920b9dd`).

- `python/digita/` : application (routes, modèles, templates, services)
- `public/` : fichiers statiques servis tels quels
- `python/deploy/` : déploiement sur le VPS INES (conteneur `digita-web`, nginx, import de données)
- `database/` : exports et migrations MySQL d'origine (source de l'import PostgreSQL)
- `docs/migrations/SUIVI_CONVERSION_PYTHON.md` : historique de la conversion et procédure de mise en ligne

Tests : `cd python && pip install -r requirements-dev.txt && pytest -q`
