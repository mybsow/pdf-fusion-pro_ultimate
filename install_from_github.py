#!/usr/bin/env python3
"""
Installation OCR depuis GitHub
"""

import os
import sys
import subprocess
import urllib.request
import tarfile
import zipfile

def run_command(cmd, description):
    """Exécute une commande shell"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def install_tesseract_from_github():
    """Installe Tesseract depuis GitHub"""
    
    # Option 1: Depuis les releases (binaires)
    print("⬇️ Téléchargement Tesseract depuis GitHub Releases...")
    
    # URL pour Tesseract 5.3.3 (Linux x86_64)
    tesseract_url = "https://github.com/tesseract-ocr/tesseract/archive/refs/tags/5.3.3.tar.gz"
    
    # Télécharger
    urllib.request.urlretrieve(tesseract_url, "/tmp/tesseract.tar.gz")
    
    # Extraire
    with tarfile.open("/tmp/tesseract.tar.gz", "r:gz") as tar:
        tar.extractall("/tmp")
    
    # Compiler
    os.chdir("/tmp/tesseract-5.3.3")
    run_command("./autogen.sh", "Autogen Tesseract")
    run_command("./configure", "Configure Tesseract")
    run_command("make", "Compilation Tesseract")
    run_command("make install", "Installation Tesseract")
    run_command("ldconfig", "Mise à jour cache bibliothèques")
    
    # Télécharger les langues
    print("🌍 Téléchargement langues OCR...")
    lang_urls = [
        ("https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata", "eng.traineddata"),
        ("https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata", "fra.traineddata"),
    ]
    
    tessdata_dir = "/usr/local/share/tessdata"
    os.makedirs(tessdata_dir, exist_ok=True)
    
    for url, filename in lang_urls:
        urllib.request.urlretrieve(url, os.path.join(tessdata_dir, filename))
        print(f"✅ {filename} téléchargé")

def main():
    print("=" * 50)
    print("🚀 INSTALLATION OCR DEPUIS GITHUB")
    print("=" * 50)
    
    # 1. Dépendances système
    run_command("apt-get update", "Mise à jour apt")
    run_command("apt-get install -y git build-essential autoconf automake libtool", "Dépendances compilation")
    
    # 2. Installer Tesseract
    install_tesseract_from_github()
    
    # 3. Installer Poppler
    run_command("apt-get install -y poppler-utils", "Installation Poppler")
    
    # 4. Installer packages Python
    run_command("pip install --upgrade pip", "Mise à jour pip")
    run_command("pip install pytesseract==0.3.10 pdf2image==1.16.3 Pillow==10.0.0", "Packages Python OCR")
    
    # 5. Vérification
    print("=" * 50)
    print("🧪 VÉRIFICATION...")
    run_command("tesseract --version", "Version Tesseract")
    run_command("tesseract --list-langs", "Langues disponibles")
    run_command("which pdftoppm", "Vérification Poppler")
    
    print("=" * 50)
    print("✅ INSTALLATION TERMINÉE")
    print("=" * 50)

if __name__ == "__main__":
    main()
