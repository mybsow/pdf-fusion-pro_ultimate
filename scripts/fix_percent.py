#!/usr/bin/env python3
# scripts/fix_percent.py

import re
from pathlib import Path
import sys
import subprocess

def fix_percent_in_file(filepath):
    """Remplace tous les % simples par %% dans les chaînes de traduction"""
    print(f"🔧 Traitement de {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    modified = False
    new_lines = []
    
    for line in lines:
        if line.startswith('msgstr "') or line.startswith('msgid "'):
            # Compter les % dans la chaîne
            if '%' in line and '%%' not in line:
                # Remplacer % par %% mais attention aux % déjà échappés
                new_line = re.sub(r'(?<!%)%(?!%)', '%%', line)
                if new_line != line:
                    modified = True
                    line = new_line
                    print(f"  ✅ Corrigé: {line[:50]}...")
        new_lines.append(line)
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

def main():
    print("🔧 CORRECTION DES POURCENTAGES DANS LES TRADUCTIONS")
    print("=" * 50)
    
    trans_dir = Path('translations')
    if not trans_dir.exists():
        print("❌ Dossier translations introuvable")
        return 1
    
    fixed_count = 0
    total_files = 0
    
    for lang_dir in sorted(trans_dir.iterdir()):
        if lang_dir.is_dir():
            po_file = lang_dir / 'LC_MESSAGES' / 'messages.po'
            if po_file.exists():
                total_files += 1
                if fix_percent_in_file(po_file):
                    fixed_count += 1
    
    print(f"\n📊 Récapitulatif:")
    print(f"   - {total_files} fichiers trouvés")
    print(f"   - {fixed_count} fichiers corrigés")
    
    # Recompiler automatiquement
    if fixed_count > 0:
        print("\n🔨 Recompilation des traductions...")
        result = subprocess.run(['pybabel', 'compile', '-d', 'translations'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Compilation réussie !")
        else:
            print("❌ Erreur de compilation:")
            print(result.stderr)
            return 1
    else:
        print("\n✅ Aucune correction nécessaire")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
