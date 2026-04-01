#!/usr/bin/env python3
"""
Réparer les erreurs de syntaxe dans le fichier .po arabe
"""

import re

def fix_po_file(input_file, output_file):
    """Corrige les erreurs communes dans les fichiers .po"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corriger msgdir -> msgstr
    content = content.replace('msgdir', 'msgstr')
    
    # Corriger les msgid dupliqués (garde la première occurrence)
    lines = content.split('\n')
    seen_msgid = set()
    fixed_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        if line.startswith('msgid "'):
            msgid = line
            # Si on a déjà vu ce msgid, sauter cette entrée
            if msgid in seen_msgid:
                skip_next = True
                continue
            else:
                seen_msgid.add(msgid)
                skip_next = False
        
        if not skip_next:
            fixed_lines.append(line)
        elif line.startswith('msgstr'):
            skip_next = False
    
    content = '\n'.join(fixed_lines)
    
    # Écrire le fichier corrigé
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fichier corrigé: {output_file}")

if __name__ == "__main__":
    # Réparer le fichier principal
    fix_po_file('translations/ar/LC_MESSAGES/messages.po', 
                'translations/ar/LC_MESSAGES/messages.po.fixed')
    
    # Remplacer par le fichier corrigé
    import shutil
    shutil.move('translations/ar/LC_MESSAGES/messages.po.fixed', 
                'translations/ar/LC_MESSAGES/messages.po')
    
    print("\n📊 Vérification du fichier réparé:")
    os.system("msgfmt --statistics translations/ar/LC_MESSAGES/messages.po")
