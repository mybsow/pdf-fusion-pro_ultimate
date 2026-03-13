#!/usr/bin/env python3
import os
import re

def fix_duplicates_and_percent(po_file):
    """Supprime les doublons et corrige les pourcentages"""
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Première passe : corriger les pourcentages
    modified = False
    new_lines = []
    
    for line in lines:
        # Corriger 100% en 100%%
        if '100%' in line and not '100%%' in line and not '100%%%' in line:
            line = line.replace('100%', '100%%')
            modified = True
        
        new_lines.append(line)
    
    # Deuxième passe : supprimer les doublons
    seen_msgid = set()
    unique_lines = []
    i = 0
    
    while i < len(new_lines):
        line = new_lines[i]
        
        if line.startswith('msgid "'):
            # Capturer le msgid complet (peut être sur plusieurs lignes)
            msgid = line
            j = i + 1
            while j < len(new_lines) and not new_lines[j].startswith('msgstr "') and not new_lines[j].startswith('msgid "'):
                msgid += new_lines[j]
                j += 1
            
            # Vérifier si ce msgid a déjà été vu
            if msgid in seen_msgid:
                # C'est un doublon, on saute jusqu'au prochain msgid
                print(f"  ⚠️ Doublon trouvé dans {po_file} à la ligne {i+1}")
                while i < len(new_lines) and not new_lines[i].startswith('msgid "'):
                    i += 1
                modified = True
                continue
            else:
                seen_msgid.add(msgid)
        
        unique_lines.append(line)
        i += 1
    
    if modified:
        # Sauvegarde
        backup = po_file + '.clean.bak'
        if not os.path.exists(backup):
            with open(backup, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"  💾 Backup: {backup}")
        
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(unique_lines if unique_lines else new_lines)
        return True
    
    return False

# Traiter toutes les langues
for lang in os.listdir('translations'):
    po_file = f'translations/{lang}/LC_MESSAGES/messages.po'
    if os.path.exists(po_file):
        print(f"\n📁 Traitement de {lang}...")
        if fix_duplicates_and_percent(po_file):
            print(f"  ✅ Modifications effectuées")

print("\n🔄 Recompilez avec: pybabel compile -d translations")