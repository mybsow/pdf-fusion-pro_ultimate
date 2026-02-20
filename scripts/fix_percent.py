#!/usr/bin/env python3
# scripts/fix_percent.py - Version corrigée

import re
from pathlib import Path
import sys
import subprocess

def needs_fix(line):
    """Vérifie si la ligne a des % non échappés qui ne sont pas des placeholders"""
    # Ignorer les placeholders courants
    if re.search(r'%[s,d,f,i,u,x,X,o,e,E,g,G]', line):
        return False
    # Chercher des % simples non échappés
    return '%' in line and '%%' not in line

def fix_percent_in_file(filepath):
    """Corrige intelligemment les % problématiques"""
    print(f"🔧 Traitement de {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    modified = False
    new_lines = []
    
    for line in lines:
        if (line.startswith('msgstr "') or line.startswith('msgid "')) and needs_fix(line):
            # Remplacer % par %% mais préserver les placeholders
            new_line = re.sub(r'(?<!%)%(?!%)(?![sdfiuxXoEeGg])', '%%', line)
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
    print("🔧 CORRECTION INTELLIGENTE DES POURCENTAGES")
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
    
    # Recompiler si nécessaire
    if fixed_count > 0:
        print("\n🔨 Recompilation des traductions...")
        result = subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Compilation réussie !")
        else:
            print("⚠️ Compilation avec avertissements (normal)")
            print(result.stderr)
    else:
        print("\n✅ Aucune correction nécessaire")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
