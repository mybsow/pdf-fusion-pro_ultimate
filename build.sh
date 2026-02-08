#!/bin/bash
# build.sh
set -ex

echo "🚀 BUILD SCRIPT"

# Désactiver Poetry
export POETRY_VIRTUALENVS_CREATE=false

# Installer Tesseract
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils

# Packages Python
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ BUILD COMPLETE"
