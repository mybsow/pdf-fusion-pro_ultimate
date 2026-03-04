#!/usr/bin/env python3
"""
Script pour corriger les dernières erreurs (msgid vides)
"""

import os
import re

def fix_empty_msgid(po_file, line_num):
    """Corrige une entrée avec msgid vide"""
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    idx = line_num - 1
    modified = False
    
    # Vérifier si c'est bien un msgid vide
    if idx < len(lines) and lines[idx].strip() == 'msgid ""':
        print(f"\n📁 {po_file}:{line_num} - msgid vide trouvé")
        
        # Vérifier les lignes autour
        start = max(0, idx - 5)
        end = min(len(lines), idx + 5)
        for i in range(start, end):
            print(f"  {i+1}: {lines[i].strip()}")
        
        # Option 1: Supprimer cette entrée si c'est un doublon
        # Chercher si c'est une partie d'un en-tête
        is_header = False
        for i in range(max(0, idx-10), idx):
            if '"Content-Type:' in lines[i] or '"Project-Id-Version:' in lines[i]:
                is_header = True
                break
        
        if is_header:
            print("  ✅ C'est un en-tête de fichier, on le garde")
            # S'assurer que le msgstr qui suit est correct
            if idx + 1 < len(lines) and lines[idx+1].startswith('msgstr "'):
                if lines[idx+1].strip() == 'msgstr ""':
                    # Remplacer par un msgstr avec au moins un espace
                    lines[idx+1] = 'msgstr " "\n'
                    print("  ✅ msgstr vide corrigé")
                    modified = True
        else:
            # Option 2: Supprimer l'entrée complète
            print("  🗑️ Suppression de l'entrée vide")
            # Trouver la fin de cette entrée
            end_idx = idx + 1
            while end_idx < len(lines) and not lines[end_idx].startswith('msgid '):
                end_idx += 1
            
            # Supprimer les lignes de idx à end_idx-1
            del lines[idx:end_idx]
            modified = True
    
    if modified:
        backup = po_file + '.empty.bak'
        with open(backup, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  💾 Backup: {backup}")
        return True
    
    return False

def main():
    # Liste des erreurs
    errors = [
        ('translations/pt/LC_MESSAGES/messages.po', 5362),
        ('translations/it/LC_MESSAGES/messages.po', 5367),
        ('translations/de/LC_MESSAGES/messages.po', 5378),
        ('translations/ja/LC_MESSAGES/messages.po', 5247),
        ('translations/ru/LC_MESSAGES/messages.po', 5369),
        ('translations/ar/LC_MESSAGES/messages.po', 5311),
        ('translations/nl/LC_MESSAGES/messages.po', 5374),
        ('translations/zh/LC_MESSAGES/messages.po', 5245),
        ('translations/en/LC_MESSAGES/messages.po', 5329)
    ]
    
    print("🔍 CORRECTION DES MSGID VIDES")
    print("=" * 50)
    
    fixed = 0
    for po_file, line_num in errors:
        if os.path.exists(po_file):
            if fix_empty_msgid(po_file, line_num):
                fixed += 1
        else:
            print(f"⚠️ Fichier non trouvé: {po_file}")
    
    print("\n" + "=" * 50)
    print(f"✅ {fixed} fichiers corrigés sur {len(errors)}")
    
    if fixed > 0:
        print("\n🔄 Recompilez maintenant:")
        print("   pybabel compile -d translations")

if __name__ == "__main__":
    response = input("⚠️  Ce script va modifier les fichiers .po. Continuer? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        main()
    else:
        print("Annulé.")