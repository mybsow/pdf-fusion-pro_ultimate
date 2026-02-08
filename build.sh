#!/bin/bash
set -ex

echo "🚀 BUILD PDF FUSION PRO - OCR INSTALLATION"

# 1. Installer Tesseract OCR (système)
echo "🔧 Installation Tesseract..."
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils

# 2. Vérifier
echo "✅ Vérification..."
which tesseract || echo "Tesseract non trouvé"
tesseract --version || echo "Impossible d'exécuter tesseract"
which pdftoppm || echo "Poppler non trouvé"

# 3. Installer packages Python
echo "🐍 Installation Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Vérification Python
echo "🧪 Vérification finale..."
python -c "
import sys
print('Python:', sys.version)

try:
    import pytesseract
    print('✅ pytesseract:', pytesseract.__version__)
except ImportError as e:
    print('❌ pytesseract:', e)

try:
    from pdf2image import convert_from_path
    print('✅ pdf2image: OK')
except ImportError as e:
    print('❌ pdf2image:', e)

try:
    from PIL import Image
    print('✅ Pillow:', Image.__version__)
except ImportError as e:
    print('❌ Pillow:', e)
"

echo "✅ BUILD COMPLÈTE !"
