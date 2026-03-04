#!/usr/bin/env python3
import os
import re

def smart_fix_po_file(po_file):
    """Corrige intelligemment les problèmes de formatage"""
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Détecter les lignes msgstr
        if line.startswith('msgstr "') and i > 0:
            # Vérifier la ligne msgid précédente
            msgid_line = lines[i-1] if i-1 >= 0 else ""
            
            # Corriger les doubles pourcentages
            if '100%' in line and not '100%%' in line:
                line = line.replace('100%', '100%%')
                modified = True
                print(f"  ✅ 100% corrigé dans {po_file}:{i+1}")
            
            # Vérifier la cohérence des placeholders avec msgid
            if msgid_line.startswith('msgid "'):
                # Extraire les placeholders du msgid
                id_placeholders = set(re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', msgid_line))
                # Extraire les placeholders du msgstr
                str_placeholders = set(re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', line))
                
                # Vérifier si des placeholders manquent
                missing = id_placeholders - str_placeholders
                if missing:
                    print(f"  ⚠️ Placeholders manquants dans {po_file}:{i+1} - {missing}")
                    # Option: ajouter automatiquement? (décommenter si voulu)
                    # for ph in missing:
                    #     line = line.replace('msgstr "', f'msgstr "{ph} ')
                    # modified = True
        
        new_lines.append(line)
        i += 1
    
    if modified:
        # Sauvegarde automatique
        backup = po_file + '.smart.bak'
        if not os.path.exists(backup):
            with open(backup, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  💾 Backup créé: {backup}")
        
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    
    return False

# Exécuter
translations_dir = 'translations'
for lang in os.listdir(translations_dir):
    po_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.po')
    if os.path.exists(po_file):
        print(f"\n📁 Traitement de {lang}...")
        if smart_fix_po_file(po_file):
            print(f"  ✅ Modifications effectuées")

print("\n🔄 Recompilez avec: pybabel compile -d translations")