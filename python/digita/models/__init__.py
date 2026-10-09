"""Modèles : mêmes requêtes que les modèles PHP, adaptées à PostgreSQL."""
import unicodedata

from .. import config


def collate_key(s):
    """Approxime la collation MySQL utf8mb4_unicode_ci (casse et accents ignorés)."""
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def sort_by_name(rows, key="name"):
    return sorted(rows, key=lambda r: collate_key(r[key]))


def rand_order(alias):
    # ORDER BY RAND() en production ; ordre fixe pour les tests de parité.
    return f"{alias}.id" if config.DETERMINISTIC else "RANDOM()"


def like_ci(column):
    """LIKE insensible à la casse et aux accents, comme MySQL en utf8mb4_unicode_ci."""
    return f"unaccent(lower({column})) LIKE unaccent(lower(?))"
