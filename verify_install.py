#!/usr/bin/env python3
# verify_install.py

import sys
print(f"🐍 Python version: {sys.version}")

def test_import(module_name):
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {module_name:<15} version: {version}")
        return True
    except ImportError as e:
        print(f"❌ {module_name:<15} Erreur: {e}")
        return False

print("\n" + "="*50)
print("📦 VÉRIFICATION DES IMPORTS")
print("="*50)

# Test des imports critiques
critical_modules = [
    'flask',
    'flask_babel',
    'babel',
    'pytesseract',
    'pdf2image',
    'PIL',
    'cv2',
    'pandas',
    'numpy',
    'fitz',  # PyMuPDF
    'reportlab',
    'docx',
    'openpyxl',
    'xlsxwriter',
    'pypdf'
]

all_ok = True
for module in critical_modules:
    if not test_import(module):
        all_ok = False

print("\n" + "="*50)
if all_ok:
    print("✅ TOUS LES IMPORTS RÉUSSIS !")
else:
    print("❌ CERTAINS IMPORTS ONT ÉCHOUÉ")

print("="*50)
