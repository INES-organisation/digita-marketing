# Image du site Digita (Python). Contexte de build : racine du dépôt digita-marketing
#   docker build -f python/Dockerfile -t digita-web .
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DIGITA_PUBLIC_DIR=/app/public

WORKDIR /app
COPY python/requirements.txt python/requirements.txt
RUN pip install --no-cache-dir -r python/requirements.txt

# Fichiers statiques (CSS, JS, images…) servis tels quels, comme sur l'hébergement PHP.
COPY public/ public/
# Les scripts PHP de public/ ne sont jamais servis (voir digita/main.py:static_file).
COPY python/digita python/digita

RUN useradd --system --uid 1001 digita && chown -R digita /app
USER digita
WORKDIR /app/python
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
CMD ["uvicorn", "digita.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
