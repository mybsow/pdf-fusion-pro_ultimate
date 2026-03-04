#!/usr/bin/env python3
import re
import os

def fix_placeholders(po_file, line_num):
    with open(po_file, 'r') as f:
        lines = f.readlines()
    
    # Trouver le msgid et msgstr autour de cette ligne
    msgid_line = None
    msgstr_line = None
    
    for i in range(max(0, line_num-10), min(len(lines), line_num+10)):
        if lines[i].startswith('msgid "'):
            msgid_line = i
        if lines[i].startswith('msgstr "'):
            msgstr_line = i
            break
    
    if msgid_line and msgstr_line:
        msgid = lines[msgid_line]
        msgstr = lines[msgstr_line]
        
        # Extraire les placeholders
        placeholders = re.findall(r'(%\([^)]+\)[sd])', msgid)
        
        if placeholders:
            for ph in placeholders:
                if ph not in msgstr:
                    print(f"Correction {po_file}: ajout de {ph}")
                    lines[msgstr_line] = msgstr.replace('msgstr "', f'msgstr "{ph} ')
                    break
        
        # Sauvegarder
        backup = po_file + '.last.bak'
        with open(backup, 'w') as f:
            f.writelines(lines)
        with open(po_file, 'w') as f:
            f.writelines(lines)
        return True
    return False

errors = [
    ('translations/de/LC_MESSAGES/messages.po', 5363),
    ('translations/ja/LC_MESSAGES/messages.po', 5235),
    ('translations/ru/LC_MESSAGES/messages.po', 5354),
    ('translations/ar/LC_MESSAGES/messages.po', 5297),
    ('translations/zh/LC_MESSAGES/messages.po', 5233)
]

for po_file, line in errors:
    if os.path.exists(po_file):
        if fix_placeholders(po_file, line):
            print(f"✅ Corrigé: {po_file}")

print("\n🔄 Recompilez avec: pybabel compile -d translations")
