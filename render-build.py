#!/usr/bin/env python3
# render-build.py - Script de build exécuté par Render

import os
import sys
import subprocess

def run_command(cmd, description):
    """Exécute une commande shell"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} réussi")
            if result.stdout:
                print(f"Sortie: {result.stdout[:200]}")
        else:
            print(f"❌ {description} échoué")
            print(f"Erreur: {result.stderr}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Exception: {e}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("🚀 BUILD PERSONNALISÉ POUR RENDER")
    print("=" * 50)
    
    # 1. Installer les dépendances système
    run_command(
        "apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils libreoffice",
        "Installation dépendances système"
    )
    
    # 2. Vérifier Tesseract
    run_command("which tesseract", "Vérification Tesseract")
    run_command("tesseract --version", "Version Tesseract")
    
    # 3. Mettre à jour pip
    run_command("python -m pip install --upgrade pip", "Mise à jour pip")
    
    # 4. Installer les packages OCR
    packages = [
        "pytesseract==0.3.10",
        "pdf2image==1.16.3",
        "Pillow==10.0.0",
        "opencv-python-headless==4.8.1.78",
        "pandas==2.1.4"
    ]
    
    for package in packages:
        run_command(f"pip install {package}", f"Installation {package}")
    
    # 5. Installer requirements.txt si existe
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt", "Installation requirements.txt")
    
    print("=" * 50)
    print("✅ BUILD TERMINÉ AVEC SUCCÈS")
    print("=" * 50)

if __name__ == "__main__":
    main()
