FROM ubuntu:22.04

# Éviter les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    poppler-utils \
    libreoffice \
    unoconv \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Créer un répertoire pour l'application
WORKDIR /app

# Copier les fichiers de l'application
COPY . .

# Installer les dépendances Python AVEC VERSIONS EXACTES
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
    Flask==3.0.0 \
    gunicorn==21.2.0 \
    pytesseract==0.3.10 \
    pdf2image==1.16.3 \
    Pillow==10.0.0 \
    opencv-python-headless==4.8.1.78 \
    pandas==2.1.4 \
    PyPDF2==3.0.1 \
    PyMuPDF==1.23.8 \
    reportlab==4.0.4 \
    python-docx==1.1.0

# Port exposé
EXPOSE 10000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "app:app"]
