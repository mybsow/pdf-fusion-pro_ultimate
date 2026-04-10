#!/usr/bin/env python3
# scripts/fix_all_quotes.py

import os
import re
import subprocess

LANGUAGES = ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl', 'ar', 'zh', 'ja', 'ru']

def fix_quotes_in_file(po_file):
    """Corrige les guillemets non échappés dans un fichier .po"""
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    for line in lines:
        if line.startswith('msgstr "'):
            # Extraire le contenu
            match = re.match(r'msgstr "(.*)"$', line.rstrip())
            if match:
                content = match.group(1)
                # Vérifier s'il y a des guillemets non échappés
                if '"' in content and not '\\"' in content:
                    # Échapper les guillemets
                    new_content = content.replace('"', '\\"')
                    new_line = f'msgstr "{new_content}"\n'
                    new_lines.append(new_line)
                    modified = True
                    print(f"    Corrigé: {content[:50]}...")
                    continue
        new_lines.append(line)
    
    if modified:
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    
    return modified

def main():
    print("🔧 CORRECTION DES GUILLEMETS DANS TOUTES LES LANGUES")
    print("====================================================")
    print()
    
    for lang in LANGUAGES:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if not os.path.exists(po_file):
            continue
        
        print(f"📝 Vérification de {lang}...")
        if fix_quotes_in_file(po_file):
            print(f"  ✅ {lang}: guillemets corrigés")
        else:
            print(f"  ✓ {lang}: aucun problème")
        print()
    
    print("📦 Recompilation...")
    subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'])
    
    print()
    print("✨ Terminé!")

if __name__ == "__main__":
    main()