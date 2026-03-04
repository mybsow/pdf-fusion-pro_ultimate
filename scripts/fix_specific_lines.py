#!/usr/bin/env python3
"""
Script pour corriger les erreurs après pybabel update
"""

import os
import re

def fix_po_file(po_file):
    print(f"\n📁 Correction de {po_file}")
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Chercher les paires msgid/msgstr
        if line.startswith('msgid "') and i + 1 < len(lines) and lines[i+1].startswith('msgstr "'):
            msgid = line
            msgstr = lines[i+1]
            
            # Extraire les placeholders du msgid
            id_placeholders = re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', msgid)
            str_placeholders = re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', msgstr)
            
            # Vérifier si les placeholders correspondent
            if id_placeholders and set(id_placeholders) != set(str_placeholders):
                print(f"  Ligne {i+1}: Placeholders incorrects")
                print(f"    msgid: {msgid.strip()}")
                print(f"    msgstr: {msgstr.strip()}")
                print(f"    Attendu: {id_placeholders}")
                print(f"    Trouvé: {str_placeholders}")
                
                # Remplacer les placeholders dans msgstr par ceux de msgid
                new_msgstr = msgstr
                for ph in id_placeholders:
                    if ph not in new_msgstr:
                        # Ajouter au début
                        new_msgstr = new_msgstr.replace('msgstr "', f'msgstr "{ph} ')
                
                lines[i+1] = new_msgstr
                modified = True
                print(f"    ✅ Corrigé")
        
        i += 1
    
    if modified:
        backup = po_file + '.postupdate.bak'
        with open(backup, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  💾 Backup: {backup}")
        return True
    
    print("  ✓ Aucune modification nécessaire")
    return False

def main():
    langs = ['pt', 'it', 'de', 'ja', 'ru', 'ar', 'fr', 'nl', 'zh', 'es', 'en']
    
    print("🔍 CORRECTION POST-UPDATE")
    print("=" * 50)
    
    fixed = 0
    for lang in langs:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_file):
            if fix_po_file(po_file):
                fixed += 1
    
    print("\n" + "=" * 50)
    print(f"✅ {fixed} fichiers corrigés")
    print("\n🔄 Recompilez maintenant:")
    print("   pybabel compile -d translations")

if __name__ == "__main__":
    response = input("⚠️  Ce script va modifier les fichiers .po. Continuer? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        main()
    else:
        print("Annulé.")