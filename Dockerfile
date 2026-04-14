# -------------------------------------------------
# Base Python slim
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# Variables d'environnement
# -------------------------------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
ENV PORT=10000
ENV BABEL_TRANSLATION_DIRECTORIES=./translations
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# =================================================
# OPTIMISATIONS MÉMOIRE POUR RENDER FREE
# =================================================
ENV PYTHONMALLOC=malloc
ENV MALLOC_ARENA_MAX=1
ENV PYTHONTRACEMALLOC=0
ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1

# -------------------------------------------------
# Dépendances système
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-fra \
        tesseract-ocr-eng \
        poppler-utils \
        libreoffice-core \
        ghostscript \
        fonts-dejavu-core \
        libglib2.0-0 \
        libcairo2 \
        libpango-1.0-0 \
        curl \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Configurer LibreOffice
# -------------------------------------------------
RUN mkdir -p /tmp/libreoffice_cache && \
    echo "[Bootstrap]\nForceSaving=true\nHideLogo=true\nQuickStart=0\nMemory=64\nCache=32\n" > /tmp/libreoffice_cache/sofficerc
ENV SAL_USE_VCLPLUGIN=svp

# -------------------------------------------------
# Installer unoconv
# -------------------------------------------------
RUN pip install --no-cache-dir unoconv

# -------------------------------------------------
# Dossier de travail
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# Installer requirements
# -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
# Copier le code source
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# Vérifier les fichiers .mo
# -------------------------------------------------
RUN echo "🔍 Vérification des fichiers .mo..." && \
    ls translations/*/LC_MESSAGES/messages.mo 2>/dev/null || echo "⚠️ Aucun .mo trouvé"

# -------------------------------------------------
# Dossiers runtime
# -------------------------------------------------
RUN mkdir -p /app/temp /app/uploads /app/data && \
    chmod -R 755 /app

# -------------------------------------------------
# Exposer port
# -------------------------------------------------
EXPOSE 10000

# -------------------------------------------------
# Healthcheck
# -------------------------------------------------
HEALTHCHECK --interval=60s --timeout=10s --start-period=90s --retries=3 \
  CMD curl -f http://localhost:10000/health || exit 1

# -------------------------------------------------
# Démarrage direct (sans script)
# -------------------------------------------------
CMD ["gunicorn", "app:application", "--bind", "0.0.0.0:10000", "--workers", "1", "--threads", "1", "--timeout", "300", "--max-requests", "20", "--access-logfile", "-", "--error-logfile", "-"]