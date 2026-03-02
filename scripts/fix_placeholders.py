#!/usr/bin/env python3
import re
from pathlib import Path

def fix_placeholders_in_file(po_file):
    """Corrige automatiquement les placeholders dans un fichier .po"""
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les msgstr avec des %s ou %d
    lines = content.split('\n')
    modified = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Si on trouve un msgid avec des placeholders nommés
        if line.startswith('msgid "') and '%(' in line:
            # Chercher le msgstr correspondant
            j = i + 1
            while j < len(lines) and not lines[j].startswith('msgstr "'):
                j += 1
            
            if j < len(lines):
                msgstr_line = lines[j]
                # Si le msgstr contient %s ou %d mais pas de placeholders nommés
                if re.search(r'%[sd]', msgstr_line) and not re.search(r'%\(', msgstr_line):
                    # Remplacer %s et %d par la version avec placeholders
                    # (solution simplifiée - à adapter selon vos besoins)
                    lines[j] = msgstr_line.replace('%s', '%(value)s').replace('%d', '%(value)d')
                    modified = True
        i += 1
    
    if modified:
        with open(po_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"✅ Corrigé: {po_file}")
        return True
    return False

# Parcourir tous les fichiers .po
fixed = 0
for po_file in Path('translations').rglob('*.po'):
    if fix_placeholders_in_file(po_file):
        fixed += 1

print(f"\n📊 {fixed} fichiers .po corrigés")