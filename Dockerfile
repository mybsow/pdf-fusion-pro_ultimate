# -----------------------------
# IMAGE DE BASE
# -----------------------------
FROM python:3.11-slim

# -----------------------------
# VARIABLES D'ENVIRONNEMENT
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# INSTALLATION DES DÉPENDANCES
# -----------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-osd \
        tesseract-ocr-fra \
        tesseract-ocr-eng \
        poppler-utils \
        libreoffice \
        unoconv \
        libglib2.0-0 \
        libgl1 \
        fonts-dejavu-core \
        ghostscript \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# TRAVAIL DANS LE REPERTOIRE APP
# -----------------------------
WORKDIR /app

# -----------------------------
# INSTALLATION DES DÉPENDANCES PYTHON
# -----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------
# COPIE DE L'APPLICATION
# -----------------------------
COPY . .

# -----------------------------
# EXPOSER LE PORT
# -----------------------------
EXPOSE 10000

# -----------------------------
# CMD GUNICORN
# -----------------------------
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--threads", "2", "--timeout", "180"]

