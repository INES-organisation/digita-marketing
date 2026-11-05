"""Anciennes adresses d'articles et de formations → adresse actuelle (redirection 301).

Le site PHP supprimait les lettres accentuées des slugs (« stratégie » → « stratgie ») ; une seconde
génération avait recréé 90 articles sous la bonne adresse : Google indexait les deux (05/11/2026).
Chaque slug corrigé ou changé dans l'admin garde ici son ancienne adresse, pour ne perdre ni les
liens ni le référencement acquis. Table : database/migrations/2026_11_05_slug_redirects.sql."""
import logging
import re
import unicodedata

from . import db

log = logging.getLogger("digita.redirects")


def slugify(text):
    """« Stratégie NFT : Guide Complet » → « strategie-nft-guide-complet » (accents translittérés)."""
    s = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def target(kind, slug):
    """Slug actuel d'une ancienne adresse, ou None."""
    try:
        row = db.fetch("SELECT new_slug FROM slug_redirects WHERE kind = ? AND old_slug = ?", [kind, slug])
    except Exception as e:  # noqa: BLE001 — sans la table, une adresse inconnue reste une 404
        log.warning("Redirections indisponibles : %s", e)
        return None
    return row["new_slug"] if row else None


def record(kind, old, new):
    """old → new, en raccourcissant les chaînes (a → old devient a → new) et sans boucle."""
    if not old or old == new:
        return
    db.execute("DELETE FROM slug_redirects WHERE kind = ? AND old_slug = ?", [kind, new])
    db.execute("UPDATE slug_redirects SET new_slug = ? WHERE kind = ? AND new_slug = ?", [new, kind, old])
    db.execute("INSERT INTO slug_redirects (kind, old_slug, new_slug) VALUES (?, ?, ?) "
               "ON CONFLICT (kind, old_slug) DO UPDATE SET new_slug = EXCLUDED.new_slug", [kind, old, new])
