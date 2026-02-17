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
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Créer le dossier de travail
# -----------------------------
WORKDIR /app

# -----------------------------
# Copier et installer requirements
# -----------------------------
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir unoconv && \
    ln -sf /usr/bin/python3 /usr/bin/python

# -----------------------------
# Copier la configuration Babel
# -----------------------------
COPY babel.cfg .

# -----------------------------
# Initialiser les traductions
# -----------------------------
RUN mkdir -p translations && \
    # Extraire les textes
    echo "📤 Extraction des textes à traduire..." && \
    pybabel extract -F babel.cfg -o messages.pot . || true && \
    # Liste des langues supportées
    LANGUAGES="en es de it pt ar zh ja ru nl" && \
    for lang in $LANGUAGES; do \
        if [ ! -d "translations/$lang" ]; then \
            echo "🌍 Création de la langue: $lang" && \
            pybabel init -i messages.pot -d translations -l $lang || true; \
        else \
            echo "🔄 Mise à jour de: $lang" && \
            pybabel update -i messages.pot -d translations -l $lang || true; \
        fi \
    done && \
    # Compiler les traductions
    echo "🔨 Compilation des traductions..." && \
    pybabel compile -d translations || true && \
    # Afficher le résultat
    echo "✅ Traductions initialisées !"

# -----------------------------
# Copier l’application
# -----------------------------
COPY . .

# -----------------------------
# Rendre les scripts exécutables
# -----------------------------
RUN chmod +x scripts/*.sh 2>/dev/null || true

# -----------------------------
# Créer dossier temporaire pour AppConfig
# -----------------------------
RUN mkdir -p /tmp/pdf_fusion_pro/conversion_temp \
    /tmp/pdf_fusion_pro/uploads \
    /tmp/pdf_fusion_pro/logs

# -----------------------------
# Exposer le port
# -----------------------------
EXPOSE 10000

# -----------------------------
# Commande de lancement Gunicorn
# -----------------------------
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "4", "--threads", "8", "--timeout", "300", "--worker-class", "gthread"]
