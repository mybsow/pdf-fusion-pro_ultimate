# -----------------------------
# Base Python slim
# -----------------------------
FROM python:3.11-slim

# -----------------------------
# Variables environnementales
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# Installer les dépendances système
# -----------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-osd \
        tesseract-ocr-fra \
        tesseract-ocr-eng \
        poppler-utils \
        libreoffice \
        libglib2.0-0 \
        libgl1 \
        fonts-dejavu-core \
        ghostscript \
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
    pip install --no-cache-dir unoconv   # Version Python si nécessaire

# -----------------------------
# Copier l’application
# -----------------------------
COPY . .

# -----------------------------
# Exposer le port
# -----------------------------
EXPOSE 10000

# -----------------------------
# Commande de lancement
# -----------------------------
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--threads", "2", "--timeout", "180"]
