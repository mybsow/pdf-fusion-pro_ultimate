#!/bin/bash
set -ex

echo "🚀 Build personnalisé pour PDF Fusion Pro..."

# 1. Désactiver Poetry (Render l'utilise par défaut)
export POETRY_VIRTUALENVS_CREATE=false

# 2. Installer Python 3.11 explicitement
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev

# 3. Installer les dépendances système OCR
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libsm6 \
    libxext6

# 4. Utiliser Python 3.11 explicitement
python3.11 -m pip install --upgrade pip setuptools wheel

# 5. Installer les packages compatibles avec Python 3.11
python3.11 -m pip install \
    Flask==3.0.0 \
    Werkzeug==3.0.1 \
    gunicorn==21.2.0 \
    PyPDF2==3.0.1 \
    PyMuPDF==1.26.7 \
    pytesseract==0.3.13 \
    Pillow==10.1.0 \
    pandas==2.1.4 \
    openpyxl==3.1.5 \
    numpy==1.26.4 \
    requests==2.32.3 \
    pdf2image==1.17.0 \
    opencv-python-headless==4.13.0.92

# 6. Installer le reste depuis requirements.txt si existe
if [ -f "requirements.txt" ]; then
    python3.11 -m pip install -r requirements.txt
fi

echo "✅ Build réussi avec Python 3.11 !"
