#!/usr/bin/env python3
# scripts/check_final.py

import polib
from pathlib import Path

def check_final():
    print("🔍 VÉRIFICATION FINALE")
    print("=" * 60)
    
    total_remaining = 0
    all_good = True
    
    for po_file in sorted(Path("translations").glob("*/LC_MESSAGES/messages.po")):
        lang = po_file.parent.parent.name
        
        # Ignorer le français (langue source)
        if lang == 'fr':
            continue
            
        po = polib.pofile(str(po_file))
        
        empty = [e for e in po if e.msgid and not e.msgstr and e.msgid != ""]
        
        if empty:
            all_good = False
            print(f"\n❌ {lang.upper()}: {len(empty)} restantes")
            for entry in empty[:3]:
                print(f"  • {entry.msgid[:60]}...")
        else:
            print(f"✅ {lang.upper()}: OK")
        
        total_remaining += len(empty)
    
    print("\n" + "=" * 60)
    if total_remaining == 0:
        print("🎉 TOUTES LES TRADUCTIONS SONT COMPLÈTES !")
    else:
        print(f"⚠ {total_remaining} traductions restantes (hors français)")

if __name__ == "__main__":
    check_final()