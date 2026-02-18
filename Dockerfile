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
# Copier et installer requirements
# -----------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir unoconv Flask-Babel Babel && \
    ln -sf /usr/bin/python3 /usr/bin/python

# -----------------------------
# Copier la configuration Babel
# -----------------------------
COPY babel_new.cfg .

# -----------------------------
# Initialiser les traductions (première passe)
# -----------------------------
RUN mkdir -p translations && \
    echo "🔧 ÉTAPE 1: Extraction des textes à traduire..." && \
    pybabel extract -F babel_new.cfg -o messages.pot . 2>/dev/null || echo "⚠️  Aucun nouveau texte extrait" && \
    echo "" && \
    echo "🔧 ÉTApE 2: Création/Mise à jour des catalogues de langue..." && \
    LANGUAGES="en es de it pt ar zh ja ru nl" && \
    for lang in $LANGUAGES; do \
        if [ ! -d "translations/$lang" ]; then \
            echo "   🌍 Création de la langue: $lang"; \
            pybabel init -i messages.pot -d translations -l $lang 2>/dev/null || echo "   ⚠️  Échec création $lang"; \
        else \
            echo "   🔄 Mise à jour de: $lang"; \
            pybabel update -i messages.pot -d translations -l $lang 2>/dev/null || echo "   ⚠️  Échec mise à jour $lang"; \
        fi \
    done && \
    echo ""

# -----------------------------
# Copier l’application
# -----------------------------
COPY . .

# -----------------------------
# Rendre les scripts exécutables
# -----------------------------
RUN chmod +x scripts/*.sh 2>/dev/null || echo "⚠️  Aucun script trouvé"

# ========== CORRECTION DES POURCENTAGES ==========
# -----------------------------
# Corriger les pourcentages dans les traductions
# -----------------------------
RUN echo "🔧 ÉTAPE 3: Correction des pourcentages dans les fichiers .po..." && \
    if [ -d "translations" ]; then \
        python scripts/fix_percent.py; \
    else \
        echo "⚠️  Dossier translations introuvable"; \
    fi

# ========== MISE À JOUR FORCÉE DES TRADUCTIONS ==========
# -----------------------------
# EXTRAIRE À NOUVEAU APRÈS AVOIR COPIÉ TOUS LES TEMPLATES
# -----------------------------
RUN echo "🔧 ÉTAPE 4: Extraction forcée de TOUS les textes des templates..." && \
    pybabel extract -F babel_new.cfg -o messages.pot . && \
    echo "" && \
    echo "🔧 ÉTAPE 5: Mise à jour forcée de toutes les langues..." && \
    LANGUAGES="en es de it pt ar zh ja ru nl" && \
    for lang in $LANGUAGES; do \
        echo "   🔄 Mise à jour forcée de: $lang"; \
        pybabel update -i messages.pot -d translations -l $lang; \
    done && \
    echo ""

# ========== COMPILATION FINALE ==========
# -----------------------------
# Compiler les traductions
# -----------------------------
RUN echo "🔧 ÉTAPE 6: Compilation finale des traductions..." && \
    if [ -d "translations" ] && [ "$(ls -A translations)" ]; then \
        pybabel compile -d translations; \
    else \
        echo "⚠️  Aucune traduction à compiler"; \
    fi && \
    echo "" && \
    echo "🔧 ÉTAPE 7: Vérification des fichiers compilés..." && \
    find translations -name "*.mo" -exec ls -la {} \; && \
    echo "" && \
    echo "📊 STATISTIQUES DES TRADUCTIONS" && \
    echo "================================" && \
    for lang in $LANGUAGES; do \
        if [ -f "translations/$lang/LC_MESSAGES/messages.po" ]; then \
            total=$(grep -c "msgid" "translations/$lang/LC_MESSAGES/messages.po" 2>/dev/null || echo "0"); \
            translated=$(grep -c "msgstr" "translations/$lang/LC_MESSAGES/messages.po" 2>/dev/null || echo "0"); \
            echo "   🌍 $lang : $total messages, $translated traduits"; \
        fi \
    done && \
    echo "" && \
    echo "✅ Initialisation des traductions terminée !"

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
