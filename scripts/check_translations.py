#!/usr/bin/env python3
# scripts/check_translations.py

import os
import sys
from pathlib import Path

def check_translations():
    """Vérifie que les traductions sont correctement installées"""
    
    print("🔍 VÉRIFICATION DES TRADUCTIONS")
    print("=" * 40)
    
    # Vérifier que le dossier translations existe
    trans_dir = Path("translations")
    if not trans_dir.exists():
        print("❌ Dossier 'translations' introuvable")
        return False
    
    print(f"✅ Dossier translations trouvé")
    
    # Vérifier les langues installées
    languages = [d for d in trans_dir.iterdir() if d.is_dir()]
    if not languages:
        print("❌ Aucune langue trouvée")
        return False
    
    print(f"📚 Langues trouvées: {', '.join([l.name for l in languages])}")
    
    # Vérifier les fichiers compilés
    all_ok = True
    for lang in languages:
        mo_file = lang / "LC_MESSAGES" / "messages.mo"
        if mo_file.exists():
            print(f"✅ {lang.name}: traductions compilées")
        else:
            print(f"⚠️  {lang.name}: fichier .mo manquant")
            all_ok = False
    
    # Tester l'import Flask-Babel
    try:
        from flask_babel import Babel
        print("✅ Flask-Babel importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur Flask-Babel: {e}")
        all_ok = False
    
    print("=" * 40)
    return all_ok

if __name__ == "__main__":
    success = check_translations()
    sys.exit(0 if success else 1)
