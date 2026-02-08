FROM python:3.11-slim

# Désactiver Poetry
ENV POETRY_VIRTUALENVS_CREATE=false
ENV PIP_NO_CACHE_DIR=1

# Installer Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Vérifier Tesseract
RUN tesseract --version

# Créer le répertoire de l'app
WORKDIR /app

# Copier les fichiers
COPY . .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install \
    Flask==3.0.0 \
    gunicorn==21.2.0 \
    pytesseract==0.3.10 \
    pdf2image==1.16.3 \
    Pillow==10.0.0 \
    opencv-python-headless==4.8.1.78 \
    pandas==2.1.4 \
    PyPDF2==3.0.1 \
    PyMuPDF==1.23.8

# Port
EXPOSE 10000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "app:app"]
