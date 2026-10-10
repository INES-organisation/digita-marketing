"""Configuration lue dans l'environnement (fichier .env chargé par docker compose)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # racine du dépôt
PUBLIC_DIR = Path(os.getenv("DIGITA_PUBLIC_DIR", ROOT / "public"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://ines:ines@127.0.0.1/digita")
APP_ENV = os.getenv("APP_ENV", "production")
APP_URL = os.getenv("APP_URL", "https://digita.buzz")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@digita.fr")

# Tri reproductible (tests de parité) : remplace ORDER BY RAND() par l'identifiant.
DETERMINISTIC = os.getenv("DIGITA_DETERMINISTIC") == "1"

CONSTANTS = {
    "APP_URL": APP_URL,
    "SITE_URL": APP_URL,
    "BASE_URL": APP_URL.rstrip("/"),
    "ENVIRONMENT": APP_ENV,
    "ADMIN_EMAIL": ADMIN_EMAIL,
}
