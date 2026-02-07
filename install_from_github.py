#!/usr/bin/env python3
"""
Installation OCR simplifiée pour Render
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Exécute une commande shell"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            if result.stdout:
                print(f"   Sortie: {result.stdout[:100]}")
            return True
        else:
            print(f"❌ {description}")
            if result.stderr:
                print(f"   Erreur: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("=" * 50)
    print("🚀 INSTALLATION OCR RAPIDE POUR RENDER")
    print("=" * 50)
    
    # 1. Mettre à jour apt
    run_command("apt-get update", "Mise à jour apt")
    
    # 2. Installer Tesseract DEPUIS LES DÉPÔTS (pas de compilation)
    print("📦 Installation Tesseract depuis les dépôts...")
    run_command("apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils", 
                "Installation Tesseract OCR")
    
    # 3. Vérifier l'installation
    print("✅ Vérification installation...")
    run_command("which tesseract", "Chemin Tesseract")
    run_command("tesseract --version", "Version Tesseract")
    run_command("which pdftoppm", "Chemin Poppler")
    
    # 4. Installer packages Python OCR
    print("🐍 Installation packages Python OCR...")
    run_command("pip install --upgrade pip", "Mise à jour pip")
    
    # Installer chaque package séparément
    packages = [
        "pytesseract==0.3.10",
        "pdf2image==1.16.3", 
        "Pillow==10.0.0",
        "opencv-python-headless==4.8.1.78",
        "pandas==2.1.4"
    ]
    
    for package in packages:
        run_command(f"pip install {package}", f"Installation {package}")
    
    # 5. Vérification finale
    print("=" * 50)
    print("🧪 VÉRIFICATION FINALE")
    print("=" * 50)
    
    # Tester les imports
    test_packages = [
        ("pytesseract", "pytesseract"),
        ("pdf2image", "pdf2image"),
        ("Pillow", "PIL.Image"),
        ("OpenCV", "cv2"),
        ("pandas", "pandas")
    ]
    
    for name, import_name in test_packages:
        try:
            if import_name == "PIL.Image":
                from PIL import Image
                print(f"✅ {name}: OK (Pillow)")
            else:
                __import__(import_name.split('.')[0])
                print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    print("=" * 50)
    print("✅ INSTALLATION OCR TERMINÉE")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())
