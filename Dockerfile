FROM python:3.11-slim

# 1. Éviter les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive

# 2. Installer les dépendances système
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    tesseract-ocr-deu \
    tesseract-ocr-ita \
    poppler-utils \
    libreoffice \
    unoconv \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Créer le répertoire de l'application
WORKDIR /app

# 4. Copier les fichiers
COPY . .

# 5. Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
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
    python-docx==1.1.0 \
    openpyxl==3.1.2 \
    numpy==1.24.4

# 6. Port exposé
EXPOSE 10000

# 7. Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "app:app"]
