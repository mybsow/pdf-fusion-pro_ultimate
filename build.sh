#!/bin/bash
set -ex

echo "🚀 BUILD PDF FUSION PRO - OCR INSTALLATION"

# 1. FORCER l'installation root (Render est root)
echo "🔧 Mise à jour système..."
apt-get update -y

# 2. Installer Tesseract avec toutes les langues
echo "📦 Installation Tesseract OCR complet..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    poppler-utils \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev

# 3. Vérifier l'installation SYSTÈME
echo "✅ Vérification installation système..."
echo "=== TESSERACT ==="
which tesseract && tesseract --version || echo "Tesseract non trouvé"
echo ""
echo "=== LANGAGES INSTALLÉS ==="
ls -la /usr/share/tesseract-ocr/ || echo "Répertoire non trouvé"
echo ""
echo "=== POPPLER ==="
which pdftoppm && pdftoppm -v 2>&1 | head -1 || echo "Poppler non trouvé"

# 4. Installer packages Python
echo "🐍 Installation Python packages..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# 5. Test Python OCR
echo "🧪 Test Python OCR..."
python -c "
import subprocess
import sys

# Test système
print('=== SYSTÈME ===')
try:
    result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
    print(f'Tesseract PATH: {result.stdout.strip() if result.stdout else \"NOT FOUND\"}')
    
    result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
    print(f'Tesseract Version: {result.stdout.split(\"\\n\")[0] if result.stdout else \"UNKNOWN\"}')
except Exception as e:
    print(f'Erreur système: {e}')

print('\\n=== PYTHON ===')
try:
    import pytesseract
    print(f'✅ pytesseract: {pytesseract.__version__}')
    
    # Test configuration
    print(f'Tesseract cmd: {pytesseract.get_tesseract_version()}')
except Exception as e:
    print(f'❌ pytesseract: {e}')
    
print('\\n=== AUTRES PACKAGES ===')
for pkg in ['pdf2image', 'PIL', 'cv2', 'pandas', 'PyPDF2']:
    try:
        __import__(pkg if pkg != 'PIL' else 'PIL.Image')
        print(f'✅ {pkg}: OK')
    except ImportError as e:
        print(f'❌ {pkg}: {e}')
"

echo "✅ BUILD COMPLÈTE !"
