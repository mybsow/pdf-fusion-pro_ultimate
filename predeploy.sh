#!/bin/bash
# predeploy.sh - Script exécuté avant le déploiement

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
    unoconv

# Installer pip packages MANUELLEMENT
/usr/bin/python3 -m pip install --upgrade pip
/usr/bin/python3 -m pip install pytesseract==0.3.10
/usr/bin/python3 -m pip install pdf2image==1.16.3
/usr/bin/python3 -m pip install Pillow==10.0.0
/usr/bin/python3 -m pip install opencv-python-headless==4.8.1.78
/usr/bin/python3 -m pip install pandas==2.1.4

echo "✅ Installation OCR terminée"
