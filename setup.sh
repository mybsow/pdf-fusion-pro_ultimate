#!/bin/bash
set -e

echo "🔧 Installation des dépendances système..."
apt-get update
apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev

echo "📦 Installation des dépendances Python..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "📁 Création des dossiers..."
mkdir -p data/contacts data/ratings uploads temp logs temp_uploads

echo "✅ Installation terminée !"