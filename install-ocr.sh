#!/bin/bash
# install-ocr.sh - Installation forcée des dépendances OCR

echo "🔧 Installation des dépendances OCR..."

# Packages système
apt-get update
apt-get install -y \
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
    libgl1-mesa-glx

# Packages Python OCR
pip install pytesseract==0.3.10
pip install pdf2image==1.16.3
pip install Pillow==10.0.0
pip install opencv-python-headless==4.8.1.78
pip install pandas==2.1.4

echo "✅ Installation terminée"
