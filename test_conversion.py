#!/usr/bin/env python3
"""
Script de test pour vérifier que toutes les dépendances fonctionnent
"""

import sys
import subprocess

def check_package(package_name, import_name=None):
    """Vérifie si un package est installé"""
    import_name = import_name or package_name.replace('-', '_')
    try:
        __import__(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name}")
        return False

def check_system_command(command):
    """Vérifie si une commande système est disponible"""
    try:
        result = subprocess.run(['which', command], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print(f"✅ {command}: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {command}: Non trouvé")
            return False
    except Exception:
        print(f"❌ {command}: Erreur de vérification")
        return False

def main():
    print("🧪 Vérification des dépendances...")
    print("-" * 50)
    
    packages = [
        ("Flask", "flask"),
        ("Werkzeug", "werkzeug"),
        ("pypdf", "pypdf"),
        ("PyMuPDF", "fitz"),
        ("Pillow", "PIL"),
        ("pytesseract", "pytesseract"),
        ("pdf2image", "pdf2image"),
        ("pandas", "pandas"),
        ("openpyxl", "openpyxl"),
        ("python-docx", "docx"),
        ("reportlab", "reportlab"),
        ("img2pdf", "img2pdf"),
        ("opencv-python-headless", "cv2"),
        ("numpy", "numpy"),
        ("python-magic", "magic"),
    ]
    
    all_ok = True
    for display_name, import_name in packages:
        if not check_package(display_name, import_name):
            all_ok = False
    
    print("-" * 50)
    print("🖥️  Vérification des commandes système...")
    
    commands = [
        "tesseract",
        "pdftoppm",
        "libreoffice",
        "unoconv"
    ]
    
    for cmd in commands:
        if not check_system_command(cmd):
            all_ok = False
    
    print("-" * 50)
    if all_ok:
        print("🎉 Toutes les dépendances sont installées correctement !")
        return 0
    else:
        print("⚠️  Certaines dépendances sont manquantes.")
        print("   Exécutez: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
