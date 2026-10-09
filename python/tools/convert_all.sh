#!/bin/bash
# Régénère les templates Jinja depuis les vues PHP puis applique les corrections manuelles.
set -euo pipefail
cd "$(dirname "$0")/../.."
FILES=$(cat python/tools/templates.txt)
python/.venv/bin/python python/tools/php2jinja.py $FILES
python/.venv/bin/python python/tools/fixups.py
