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
# Installer requirements
# -----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    ln -sf /usr/bin/python3 /usr/bin/python

# -----------------------------
# Copier babel.cfg et scripts avant le reste
# -----------------------------
COPY babel.cfg .
COPY scripts ./scripts

# -----------------------------
# Copier tout le projet
# -----------------------------
COPY . .

# -----------------------------
# Génération intelligente des traductions
# -----------------------------
RUN mkdir -p translations && \
    echo "🔧 Vérification des fichiers pour Babel..." && \
    # Calculer un hash des fichiers sources .py, .html et babel.cfg
    find . -type f \( -name "*.py" -o -name "*.html" \) -o -name "babel.cfg" | sort | xargs md5sum > .sources.md5 && \
    if [ ! -f translations/.sources.md5 ] || ! cmp -s .sources.md5 translations/.sources.md5; then \
        echo "🌍 Changements détectés : extraction et mise à jour des traductions"; \
        echo "🔍 Extraction des chaînes avec babel.cfg..."; \
        # Afficher les erreurs pour diagnostic
        pybabel extract -F babel.cfg -o messages.pot . || echo "⚠️ Échec de l'extraction - mais on continue"; \
        \
        # Vérifier si messages.pot a été créé
        if [ -f messages.pot ]; then \
            echo "✅ Fichier messages.pot créé avec succès"; \
            wc -l messages.pot; \
            \
            LANGUAGES="en es de it pt ar zh ja ru nl"; \
            for lang in $LANGUAGES; do \
                echo "🔄 Traitement de $lang..."; \
                if [ ! -d "translations/$lang/LC_MESSAGES" ]; then \
                    echo "   Initialisation de $lang..."; \
                    pybabel init -i messages.pot -d translations -l $lang 2>&1 || echo "⚠️ Init $lang échoué"; \
                else \
                    echo "   Mise à jour de $lang..."; \
                    pybabel update -i messages.pot -d translations -l $lang 2>&1 || echo "⚠️ Update $lang échoué"; \
                fi; \
            done; \
            \
            echo "🔧 Compilation des traductions (les erreurs sont ignorées)..."; \
            pybabel compile -d translations -f 2>&1 || true; \
        else \
            echo "⚠️ messages.pot non créé - utilisation des fichiers existants"; \
            # Compiler quand même les fichiers existants
            pybabel compile -d translations -f 2>&1 || true; \
        fi; \
        \
        cp .sources.md5 translations/.sources.md5; \
    else \
        echo "✅ Traductions déjà à jour, compilation simple..."; \
        pybabel compile -d translations -f 2>&1 || true; \
    fi
# Correction intelligente des placeholders
RUN echo "🔧 Correction des placeholders dans les traductions..." && \
    python scripts/fix_placeholders.py
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
