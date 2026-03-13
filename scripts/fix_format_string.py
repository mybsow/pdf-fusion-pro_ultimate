#!/usr/bin/env python3
import os
import re

def fix_format_strings(po_file):
    """Corrige les différences de format strings"""
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('msgid "'):
            # Capturer la ligne msgid et les suivantes jusqu'au msgstr
            msgid_lines = [line]
            j = i + 1
            while j < len(lines) and not lines[j].startswith('msgstr "'):
                msgid_lines.append(lines[j])
                j += 1
            
            # Extraire le msgid complet
            msgid = ''.join(msgid_lines).replace('msgid "', '').replace('"', '').strip()
            
            # Chercher le msgstr
            if j < len(lines):
                msgstr_line = lines[j]
                # Analyser les types de format dans msgid et msgstr
                msgid_formats = set(re.findall(r'%[diouxXeEfFgGcs]', msgid))
                msgstr_formats = set(re.findall(r'%[diouxXeEfFgGcs]', msgstr_line))
                
                # Si les ensembles sont différents, corriger
                if msgid_formats and msgstr_formats and msgid_formats != msgstr_formats:
                    print(f"  ⚠️ Différence de format à la ligne {i+1} dans {po_file}")
                    print(f"     msgid: {msgid_formats}")
                    print(f"     msgstr: {msgstr_formats}")
                    
                    # Remplacer les formats du msgstr par ceux du msgid
                    for old_fmt in msgstr_formats:
                        for new_fmt in msgid_formats:
                            if old_fmt != new_fmt:
                                msgstr_line = msgstr_line.replace(old_fmt, new_fmt)
                                modified = True
                    
                    if modified:
                        print(f"  ✅ Corrigé avec {msgid_formats}")
                        lines[j] = msgstr_line
        
        i += 1
    
    if modified:
        backup = po_file + '.fmt.bak'
        if not os.path.exists(backup):
            with open(backup, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  💾 Backup: {backup}")
        
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    
    return False

def main():
    translations_dir = 'translations'
    fixed_count = 0
    
    for lang in os.listdir(translations_dir):
        po_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.po')
        if os.path.exists(po_file):
            print(f"\n📁 Analyse de {lang}...")
            if fix_format_strings(po_file):
                fixed_count += 1
    
    print(f"\n✅ {fixed_count} fichiers corrigés")
    print("\n🔄 Recompilez avec: pybabel compile -d translations")

if __name__ == "__main__":
    main()