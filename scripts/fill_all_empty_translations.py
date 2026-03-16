#!/usr/bin/env python3
# scripts/check_real_status.py

import polib
from pathlib import Path

def check_status():
    print("🔍 VÉRIFICATION DU STATUT RÉEL")
    print("=" * 70)
    
    for lang in ['fr', 'en']:
        po_file = Path(f"translations/{lang}/LC_MESSAGES/messages.po")
        po = polib.pofile(str(po_file))
        
        print(f"\n📄 {lang.upper()}:")
        
        # Entrées normales vides
        empty = [e for e in po if e.msgid and not e.msgstr and e.msgid != ""]
        print(f"  Entrées vides normales: {len(empty)}")
        
        # Entrées fuzzy
        fuzzy = [e for e in po if 'fuzzy' in e.flags]
        print(f"  Entrées fuzzy: {len(fuzzy)}")
        
        # Entrées obsolètes (commentées)
        obsolete = [e for e in po if e.obsolete]
        print(f"  Entrées obsolètes: {len(obsolete)}")
        
        if empty:
            print("\n  Premières entrées vides:")
            for e in empty[:3]:
                print(f"    • {e.msgid[:60]}...")

if __name__ == "__main__":
    check_status()