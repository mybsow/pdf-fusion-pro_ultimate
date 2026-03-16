#!/usr/bin/env python3
import re
import sys
from collections import OrderedDict

def clean_po_duplicates(po_file):
    with open(po_file, 'r') as f:
        content = f.read()
    
    # Séparer les entrées
    entries = re.split(r'\n\n', content)
    
    # Garder une trace des msgid uniques
    seen = OrderedDict()
    header = entries[0]  # Garder l'en-tête
    
    cleaned_entries = [header]
    
    for entry in entries[1:]:
        if not entry.strip():
            continue
            
        # Extraire le msgid
        msgid_match = re.search(r'msgid "(.*)"', entry, re.DOTALL)
        if msgid_match:
            msgid = msgid_match.group(1)
            if msgid not in seen:
                seen[msgid] = True
                cleaned_entries.append(entry)
    
    # Écrire le fichier nettoyé
    with open(po_file, 'w') as f:
        f.write('\n\n'.join(cleaned_entries))
    
    print(f"✓ Nettoyé : {po_file}")

if __name__ == "__main__":
    for po_file in sys.argv[1:]:
        clean_po_duplicates(po_file)