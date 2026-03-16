#!/usr/bin/env python3
# scripts/list_exact_remaining.py

import polib
from pathlib import Path

def list_remaining():
    print("📋 LISTE DÉTAILLÉE DES TRADUCTIONS RESTANTES")
    print("=" * 80)
    
    total = 0
    for po_file in Path("translations").glob("*/LC_MESSAGES/messages.po"):
        lang = po_file.parent.parent.name
        po = polib.pofile(str(po_file))
        
        empty = [e for e in po if e.msgid and not e.msgstr and e.msgid != ""]
        
        if empty:
            print(f"\n🌍 {lang.upper()} ({len(empty)} restantes):")
            for entry in empty[:10]:  # Max 10 par langue
                print(f"  • {entry.msgid[:80]}")
                if entry.occurrences:
                    occ = entry.occurrences[0]
                    print(f"    → {occ[0]}:{occ[1]}")
            if len(empty) > 10:
                print(f"    ... et {len(empty)-10} autres")
            total += len(empty)
    
    print("\n" + "=" * 80)
    print(f"📊 TOTAL GÉNÉRAL: {total} traductions restantes")

if __name__ == "__main__":
    list_remaining()