# -----------------------------
# Base Python slim
# -----------------------------
FROM python:3.11-slim

# -----------------------------
# Variables environnementales
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV PORT=10000
ENV BABEL_TRANSLATION_DIRECTORIES=./translations
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# -----------------------------
# Installer les dépendances système
# -----------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-osd \
        tesseract-ocr-fra \
        tesseract-ocr-eng \
        tesseract-ocr-deu \
        tesseract-ocr-spa \
        tesseract-ocr-ita \
        tesseract-ocr-por \
        tesseract-ocr-rus \
        tesseract-ocr-ara \
        tesseract-ocr-chi-sim \
        tesseract-ocr-chi-tra \
        poppler-utils \
        libreoffice \
        libglib2.0-0 \
        libgl1 \
        fonts-dejavu-core \
        ghostscript \
        gettext \
        git \
        curl \
        wget \
        libgpg-error-l10n \
        fonts-droid-fallback \
        gstreamer1.0-plugins-base \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Créer le dossier de travail
# -----------------------------
WORKDIR /app

# -----------------------------
# Copier requirements
# -----------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    ln -sf /usr/bin/python3 /usr/bin/python

# -----------------------------
# Copier tout le projet
# -----------------------------
COPY . .

# -----------------------------
# Initialiser / mettre à jour les traductions Babel
# -----------------------------
RUN echo "🔧 Extraction et mise à jour des traductions..." && \
    mkdir -p translations && \
    pybabel extract -F babel.cfg -o messages.pot . 2>/dev/null || echo "⚠️ Aucun texte extrait" && \
    LANGUAGES="en es de it pt ar zh ja ru nl" && \
    for lang in $LANGUAGES; do \
        if [ ! -d "translations/$lang/LC_MESSAGES" ]; then \
            echo "🌍 Création de la langue: $lang"; \
            pybabel init -i messages.pot -d translations -l $lang 2>/dev/null || echo "⚠️ Échec création $lang"; \
        else \
            echo "🔄 Mise à jour de: $lang"; \
            pybabel update -i messages.pot -d translations -l $lang 2>/dev/null || echo "⚠️ Échec mise à jour $lang"; \
        fi; \
    done && \
    echo "✅ Compilation des fichiers .po en .mo..." && \
    pybabel compile -d translations

# -----------------------------
# Rendre les scripts exécutables
# -----------------------------
RUN chmod +x scripts/*.sh 2>/dev/null || echo "⚠️ Aucun script trouvé"

# -----------------------------
# Correction des pourcentages
# -----------------------------
RUN echo "🔧 Correction des pourcentages dans les .po..." && \
    if [ -d "translations" ]; then \
        python scripts/fix_percent.py; \
    else \
        echo "⚠️ Dossier translations introuvable"; \
    fi

# -----------------------------
# Créer les dossiers temporaires
# -----------------------------
RUN mkdir -p /tmp/pdf_fusion_pro/conversion_temp \
    /tmp/pdf_fusion_pro/uploads \
    /tmp/pdf_fusion_pro/logs \
    /app/data/contacts \
    /app/data/ratings \
    /app/data/logs \
    /app/uploads \
    /app/temp

# -----------------------------
# Définir les permissions
# -----------------------------
RUN chmod -R 755 /app/data /app/uploads /app/temp /tmp/pdf_fusion_pro

# -----------------------------
# Exposer le port
# -----------------------------
EXPOSE 10000

# -----------------------------
# Health check
# -----------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:10000/health || exit 1

# -----------------------------
# Commande de lancement Gunicorn
# -----------------------------
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "4", "--threads", "8", "--timeout", "300", "--worker-class", "gthread", "--access-logfile", "-", "--error-logfile", "-"]
