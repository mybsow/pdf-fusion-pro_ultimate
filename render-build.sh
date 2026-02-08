#!/bin/bash
set -ex

echo "=========================================="
echo "🚀 BUILD AVEC INSTALLATION DEPUIS GITHUB"
echo "=========================================="

# 1. Installer les dépendances de compilation
apt-get update
apt-get install -y \
    git \
    build-essential \
    autoconf \
    automake \
    libtool \
    pkg-config \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    zlib1g-dev \
    libicu-dev \
    libpango1.0-dev \
    libcairo2-dev

# 2. Cloner et compiler Tesseract depuis GitHub
echo "🔧 Compilation Tesseract depuis GitHub..."
cd /tmp

# Option A: Tesseract stable
git clone --depth 1 https://github.com/tesseract-ocr/tesseract.git
cd tesseract
./autogen.sh
./configure
make
make install
ldconfig

# 3. Installer les données de langue depuis GitHub
echo "🌍 Installation langues OCR..."
cd /tmp
git clone --depth 1 https://github.com/tesseract-ocr/tessdata.git
mkdir -p /usr/local/share/tessdata
cp tessdata/*.traineddata /usr/local/share/tessdata/
# Langue française
wget -O /usr/local/share/tessdata/fra.traineddata \
    https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata

# 4. Vérifier Tesseract
echo "✅ Vérification Tesseract..."
tesseract --version
tesseract --list-langs

# 5. Installer Poppler depuis sources (optionnel mais recommandé)
echo "📄 Installation Poppler..."
apt-get install -y poppler-utils

# 6. Installer les packages Python
echo "🐍 Installation packages Python..."
pip install --upgrade pip
pip install pytesseract pdf2image Pillow opencv-python-headless

echo "=========================================="
echo "✅ BUILD RÉUSSI AVEC GITHUB !"
echo "=========================================="
