#!/usr/bin/env python3
# scripts/remove_duplicates.py

import re
import sys
from collections import OrderedDict

def remove_duplicates(po_file):
    with open(po_file, 'r') as f:
        content = f.read()
    
    # Séparer les entrées (séparées par des lignes vides)
    entries = re.split(r'\n\n', content)
    
    # Garder l'en-tête (première entrée)
    header = entries[0]
    unique_entries = [header]
    
    # Dictionnaire pour suivre les msgid uniques
    seen_msgids = {}
    
    for entry in entries[1:]:
        if not entry.strip():
            continue
            
        # Extraire le msgid
        msgid_match = re.search(r'msgid "(.*)"', entry, re.DOTALL)
        if msgid_match:
            msgid = msgid_match.group(1)
            
            # Si c'est un doublon, ignorer
            if msgid in seen_msgids:
                print(f"  Doublon trouvé: {msgid[:50]}...")
                continue
                
            seen_msgids[msgid] = True
            unique_entries.append(entry)
    
    # Réécrire le fichier
    with open(po_file, 'w') as f:
        f.write('\n\n'.join(unique_entries))
    
    print(f"✓ Nettoyé: {po_file}")

if __name__ == "__main__":
    for po_file in sys.argv[1:]:
        print(f"Traitement de {po_file}...")
        remove_duplicates(po_file)