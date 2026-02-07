#!/bin/bash
# predeploy.sh - Installation FORCÉE des dépendances OCR sur Render

echo "=========================================="
echo "🔧 INSTALLATION OCR FORCÉE - PDF Fusion Pro"
echo "=========================================="

# 1. Mettre à jour le système
echo "📦 Mise à jour du système..."
apt-get update -y

# 2. Installer Tesseract OCR et dépendances système
echo "🔧 Installation Tesseract OCR..."
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

# 3. Vérifier l'installation de Tesseract
echo "✅ Vérification Tesseract..."
which tesseract && tesseract --version
ls -la /usr/bin/tesseract || ls -la /usr/local/bin/tesseract

# 4. Mettre à jour pip
echo "📦 Mise à jour pip..."
python -m pip install --upgrade pip setuptools wheel

# 5. Installer les packages Python OCR AVANT tout le reste
echo "🐍 Installation packages Python OCR..."
python -m pip install --no-cache-dir \
    pytesseract==0.3.10 \
    pdf2image==1.16.3 \
    Pillow==10.0.0 \
    opencv-python-headless==4.8.1.78 \
    pandas==2.1.4

# 6. Vérifier l'installation des packages
echo "✅ Vérification packages installés..."
python -c "
try:
    import pytesseract
    print('✅ pytesseract importé')
except ImportError as e:
    print('❌ pytesseract NON importé:', e)

try:
    from pdf2image import convert_from_path
    print('✅ pdf2image importé')
except ImportError as e:
    print('❌ pdf2image NON importé:', e)

try:
    from PIL import Image
    print('✅ Pillow importé')
except ImportError as e:
    print('❌ Pillow NON importé:', e)

try:
    import cv2
    print('✅ OpenCV importé')
except ImportError as e:
    print('❌ OpenCV NON importé:', e)

try:
    import pandas
    print('✅ pandas importé - version:', pandas.__version__)
except ImportError as e:
    print('❌ pandas NON importé:', e)
"

echo "=========================================="
echo "✅ INSTALLATION OCR TERMINÉE"
echo "=========================================="
