#!/usr/bin/env python3
import re
import os

def fix_file(po_file):
    with open(po_file, 'r') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        if lines[i].startswith('msgid "'):
            # Trouver le msgid complet
            msgid = lines[i]
            j = i + 1
            while j < len(lines) and lines[j].startswith('"'):
                msgid += lines[j]
                j += 1
            
            # Chercher le msgstr
            k = j
            while k < len(lines) and not lines[k].startswith('msgstr "'):
                k += 1
            
            if k < len(lines):
                msgstr = lines[k]
                l = k + 1
                while l < len(lines) and lines[l].startswith('"'):
                    msgstr += lines[l]
                    l += 1
                
                # Vérifier les %
                if '100%' in msgid and '100%' not in msgstr:
                    print(f"Correction: {po_file}:{k+1}")
                    lines[k] = lines[k].replace('100%%', '100%')
                    modified = True
                elif '100%%' in msgid and '100%%' not in msgstr:
                    print(f"Correction: {po_file}:{k+1}")
                    lines[k] = lines[k].replace('100%', '100%%')
                    modified = True
        
        i += 1
    
    if modified:
        backup = po_file + '.intelligent.bak'
        os.rename(po_file, backup)
        with open(po_file, 'w') as f:
            f.writelines(lines)
        print(f"✅ Corrigé: {po_file}")
        return True
    return False

# Traiter les fichiers
for po_file in ['translations/ja/LC_MESSAGES/messages.po', 
                'translations/zh/LC_MESSAGES/messages.po']:
    if os.path.exists(po_file):
        fix_file(po_file)

print("\n🔄 Recompilez avec: pybabel compile -d translations")
