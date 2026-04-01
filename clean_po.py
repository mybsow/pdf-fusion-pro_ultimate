#!/usr/bin/env python3
"""
Nettoyer un fichier PO en supprimant les doublons
"""

import polib
import sys

def clean_po_file(input_file, output_file):
    """Supprime les entrées dupliquées d'un fichier PO"""
    
    po = polib.pofile(input_file)
    
    # Garder une trace des msgid déjà vus
    seen = {}
    unique_entries = []
    
    for entry in po:
        if entry.msgid not in seen:
            seen[entry.msgid] = True
            unique_entries.append(entry)
        else:
            print(f"Suppression du doublon: {entry.msgid[:50]}...")
    
    # Créer un nouveau fichier
    new_po = polib.POFile()
    for entry in unique_entries:
        new_po.append(entry)
    
    # Copier les métadonnées
    if po.metadata:
        new_po.metadata = po.metadata
    
    new_po.save(output_file)
    print(f"\n✅ Fichier nettoyé: {len(unique_entries)} entrées uniques (était {len(po)})")

if __name__ == "__main__":
    clean_po_file('translations/ar/LC_MESSAGES/messages.po', 
                  'translations/ar/LC_MESSAGES/messages.po')
