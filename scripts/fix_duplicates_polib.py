#!/usr/bin/env python3
# scripts/fix_duplicates_polib.py

import polib
import sys
import os
from pathlib import Path

def fix_po_duplicates(po_file):
    print(f"Traitement de {po_file}...")
    
    # Sauvegarde
    backup = f"{po_file}.bak"
    os.system(f"cp {po_file} {backup}")
    
    # Charger le fichier PO
    po = polib.pofile(po_file)
    
    # Compter avant
    avant = len(po)
    print(f"  Entrées avant: {avant}")
    
    # Supprimer les doublons (garder la première occurrence)
    seen_msgids = {}
    entries_to_remove = []
    
    for entry in po:
        msgid = entry.msgid
        if msgid in seen_msgids:
            entries_to_remove.append(entry)
            print(f"  Doublon trouvé: {msgid[:50]}...")
        else:
            seen_msgids[msgid] = True
    
    # Supprimer les doublons
    for entry in entries_to_remove:
        po.remove(entry)
    
    # Compter après
    apres = len(po)
    print(f"  Entrées après: {apres}")
    print(f"  Supprimé: {avant - apres} doublons")
    
    # Sauvegarder
    po.save(po_file)
    
    # Recompiler
    mo_file = po_file.replace('.po', '.mo')
    po.save_as_mofile(mo_file)
    print(f"  ✓ Fichier MO généré: {mo_file}")

if __name__ == "__main__":
    for po_file in sys.argv[1:]:
        if os.path.exists(po_file):
            fix_po_duplicates(po_file)
        else:
            print(f"Fichier non trouvé: {po_file}")
            