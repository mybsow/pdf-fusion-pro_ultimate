#!/usr/bin/env python3
# scripts/fix_placeholders.py

import re
import os
import sys

# Mapping des placeholders à corriger
FIXES = {
    # Italien
    'nomefile': 'filename',
    'nome': 'name',
    # Allemand
    'Dateiname': 'filename',
    # Japonais
    'ファイル名': 'filename',
    # Russe
    'хостинг': 'hosting',
    # Néerlandais
    'bestandsnaam': 'filename',
    # Chinois
    '文件名': 'filename',
}

def fix_placeholders_in_file(po_file):
    """Corrige les placeholders mal traduits dans un fichier .po"""
    
    if not os.path.exists(po_file):
        return 0
    
    with open(po_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    fixed_count = 0
    
    # Corriger %(xxx)s -> %(yyy)s
    for wrong, correct in FIXES.items():
        pattern = f'%\\({wrong}\\)s'
        replacement = f'%({correct})s'
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            fixed_count += count
            print(f"   🔧 {wrong} -> {correct} ({count} fois)")
    
    # Sauvegarder
    with open(po_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    return fixed_count

def main():
    print("🔧 Correction des placeholders dans les fichiers .po")
    print("=" * 55)
    
    total_fixed = 0
    po_files = [
        "translations/it/LC_MESSAGES/messages.po",
        "translations/de/LC_MESSAGES/messages.po",
        "translations/ja/LC_MESSAGES/messages.po",
        "translations/ru/LC_MESSAGES/messages.po",
        "translations/nl/LC_MESSAGES/messages.po",
        "translations/zh/LC_MESSAGES/messages.po",
    ]
    
    for po_file in po_files:
        if os.path.exists(po_file):
            print(f"\n📁 {po_file}")
            fixed = fix_placeholders_in_file(po_file)
            total_fixed += fixed
            if fixed == 0:
                print("   ✓ Aucune correction nécessaire")
    
    print(f"\n✅ Total: {total_fixed} placeholders corrigés")

if __name__ == "__main__":
    main()