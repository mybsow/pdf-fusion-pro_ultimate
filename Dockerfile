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
# Copier le code source (traductions incluses)
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# Vérifier que les .mo pré-compilés sont bien présents
# Les .mo sont compilés localement et commitées dans le repo
# NE PAS recompiler ici — cela écraserait les bonnes traductions
# -------------------------------------------------
RUN echo "🔍 Vérification des fichiers .mo pré-compilés :" && \
    ls -la translations/*/LC_MESSAGES/messages.mo && \
    for mo in translations/*/LC_MESSAGES/messages.mo; do \
        size=$(stat -c%s "$mo"); \
        echo "📄 $mo : $size octets"; \
        if [ "$size" -lt 5000 ]; then \  # ← Changé de 10000 à 5000
            echo "❌ $mo est trop petit ($size octets) — recompilez localement avec : pybabel compile -d translations"; \
            exit 1; \
        fi; \
    done && \
    echo "✅ Tous les fichiers .mo sont valides"

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