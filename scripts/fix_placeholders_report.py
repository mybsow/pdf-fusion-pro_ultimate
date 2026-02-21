#!/usr/bin/env python3
# scripts/fix_placeholders_report.py

import re
from pathlib import Path
import sys
import subprocess

PLACEHOLDER_PATTERN = re.compile(r'%\([^)]+\)[sdfiuxXo]')

def fix_placeholders_in_file(filepath):
    modified = 0
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        new_line = PLACEHOLDER_PATTERN.sub(lambda m: m.group(0), line)  # placeholder reste
        if new_line != line:
            modified += 1
        new_lines.append(new_line)
    if modified > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    return modified

def main():
    trans_dir = Path('translations')
    if not trans_dir.exists():
        print("❌ Dossier translations introuvable")
        return 1

    total_files = 0
    total_modifications = 0

    print("🔧 Correction des placeholders avec rapport")
    print("="*50)

    for lang_dir in sorted(trans_dir.iterdir()):
        po_file = lang_dir / 'LC_MESSAGES' / 'messages.po'
        if po_file.exists():
            total_files += 1
            modified = fix_placeholders_in_file(po_file)
            if modified > 0:
                print(f"✅ {po_file}: {modified} lignes corrigées")
                total_modifications += modified

    print("="*50)
    print(f"📊 Résumé global:")
    print(f"   - {total_files} fichiers analysés")
    print(f"   - {total_modifications} corrections appliquées")
    
    if total_modifications > 0:
        print("🔨 Recompilation des traductions...")
        subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'], check=False)
    else:
        print("✅ Aucune correction nécessaire")

    return 0

if __name__ == "__main__":
    sys.exit(main())
