# -------------------------------------------------
# Base Python slim
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# Variables d’environnement
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

# -------------------------------------------------
# Dépendances système (WeasyPrint, LibreOffice, Tesseract, unoconv)
# -------------------------------------------------
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
        ghostscript \
        fonts-dejavu-core \
        fonts-droid-fallback \
        libglib2.0-0 \
        libgl1 \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        gettext \
        curl \
        wget \
        git \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Installer unoconv via pip
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
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    ln -sf /usr/bin/python3 /usr/bin/python

# -------------------------------------------------
# Copier config Babel & scripts
# -------------------------------------------------
# NE COPIEZ PAS les fichiers .mo existants !
COPY translations ./translations
COPY babel.cfg .
COPY messages.pot .
COPY scripts ./scripts

# -------------------------------------------------
# Copier le projet
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# Génération intelligente des traductions (Babel)
# -------------------------------------------------
RUN mkdir -p translations && \
    echo "🔎 Vérification des sources Babel..." && \
    find . -type f \( -name "*.py" -o -name "*.html" -o -name "babel.cfg" \) -print0 \
        | sort -z | xargs -0 md5sum > .sources.md5 && \
    if [ ! -f translations/.sources.md5 ] || ! cmp -s .sources.md5 translations/.sources.md5; then \
        echo "🌍 Changements détectés → extraction traductions"; \
        pybabel extract -F babel.cfg -o messages.pot .; \
        LANGUAGES="en es de it pt ar zh ja ru nl"; \
        for lang in $LANGUAGES; do \
            if [ ! -d "translations/$lang/LC_MESSAGES" ]; then \
                pybabel init -i messages.pot -d translations -l $lang; \
            else \
                pybabel update -i messages.pot -d translations -l $lang; \
            fi; \
        done; \
        python scripts/fix_placeholders.py; \
        python scripts/fix_percent.py; \
        pybabel compile -d translations -f; \
        cp .sources.md5 translations/.sources.md5; \
    else \
        echo "♻️ Aucune modification → compilation forcée des .mo"; \
        python scripts/fix_placeholders.py; \
        python scripts/fix_percent.py; \
        pybabel compile -d translations -f; \
    fi

# -------------------------------------------------
# Créer dossiers runtime
# -------------------------------------------------
RUN mkdir -p \
    /tmp/pdf_fusion_pro/conversion_temp \
    /tmp/pdf_fusion_pro/uploads \
    /tmp/pdf_fusion_pro/logs \
    /app/data/contacts \
    /app/data/ratings \
    /app/data/logs \
    /app/uploads \
    /app/temp && \
    chmod -R 755 /app /tmp/pdf_fusion_pro

# -------------------------------------------------
# Exposer port
# -------------------------------------------------
EXPOSE 10000

# -------------------------------------------------
# Healthcheck
# -------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:10000/health || exit 1

# -------------------------------------------------
# Gunicorn (optimisé mémoire Render)
# -------------------------------------------------
CMD ["gunicorn", "app:application", "--bind", "0.0.0.0:10000", "--workers", "2", "--threads", "2", "--timeout", "300", "--worker-class", "gthread", "--access-logfile", "-", "--error-logfile", "-"]