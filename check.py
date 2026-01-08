#!/usr/bin/env python3
import os
import sys

def check_file(filepath, must_contain=None):
    """Vérifie si un fichier existe et contient certains textes"""
    if not os.path.exists(filepath):
        return False, f"✗ {filepath} n'existe pas"
    
    if must_contain:
        with open(filepath, 'r') as f:
            content = f.read()
            for text in must_contain:
                if text not in content:
                    return False, f"✗ {filepath} ne contient pas '{text}'"
    
    return True, f"✓ {filepath}"

def main():
    print("="*60)
    print("VÉRIFICATION DE LA STRUCTURE PDF FUSION PRO")
    print("="*60)
    
    checks = [
        ('app.py', ['Flask', 'create_app']),
        ('config.py', ['AppConfig']),
        ('utils/__init__.py', None),
        ('utils/stats_manager.py', ['StatisticsManager', 'stats_manager']),
        ('utils/middleware.py', ['setup_middleware']),
        ('blueprints/__init__.py', None),
        ('blueprints/pdf/__init__.py', ['pdf_bp', 'Blueprint']),
        ('blueprints/pdf/routes.py', ['pdf_bp']),
        ('blueprints/api/__init__.py', ['api_bp']),
        ('blueprints/legal/__init__.py', ['legal_bp']),
        ('blueprints/stats/__init__.py', ['stats_bp']),
    ]
    
    all_ok = True
    for filepath, must_contain in checks:
        ok, message = check_file(filepath, must_contain)
        print(message)
        if not ok:
            all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ TOUS LES FICHIERS SONT CORRECTS")
        print("\nEssayez de lancer l'application :")
        print("  python app.py")
    else:
        print("❤️‍🩹 CERTAINS FICHIERS ONT DES PROBLÈMES")
        print("\nCorrigez les fichiers marqués '✗' avant de continuer.")
    
    # Test d'import
    print("\n" + "="*60)
    print("TEST D'IMPORT DES BLUEPRINTS...")
    try:
        sys.path.insert(0, os.getcwd())
        from blueprints.pdf import pdf_bp
        print("✅ SUCCÈS: pdf_bp importé correctement")
    except ImportError as e:
        print(f"❌ ÉCHEC: Impossible d'importer pdf_bp")
        print(f"   Erreur: {e}")

if __name__ == '__main__':
    main()