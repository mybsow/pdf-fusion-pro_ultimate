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
# Initialiser les traductions
# -----------------------------
COPY babel.cfg .
RUN mkdir -p translations && \
    # Extraire les textes (ignorer les erreurs s'il n'y a pas de nouveaux textes)
    pybabel extract -F babel.cfg -o messages.pot . 2>/dev/null || true && \
    # Compiler les traductions si elles existent
    if [ -d "translations" ] && [ "$(ls -A translations)" ]; then \
        pybabel compile -d translations; \
    else \
        echo "⚠️  Aucune traduction trouvée, création des dossiers..."; \
        mkdir -p translations/en/LC_MESSAGES \
                 translations/es/LC_MESSAGES \
                 translations/de/LC_MESSAGES \
                 translations/it/LC_MESSAGES \
                 translations/pt/LC_MESSAGES \
                 translations/ar/LC_MESSAGES \
                 translations/zh/LC_MESSAGES \
                 translations/ja/LC_MESSAGES \
                 translations/ru/LC_MESSAGES \
                 translations/nl/LC_MESSAGES; \
    fi

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
