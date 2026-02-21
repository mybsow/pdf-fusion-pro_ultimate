#!/usr/bin/env python3
# Correction avancée Babel placeholders + flags python-format

import polib
import re
from pathlib import Path
import sys

PERCENT_PATTERN = re.compile(r"%\([^)]+\)[sdifeEgGxX]|%[sdifeEgGxX]")
BRACE_PATTERN = re.compile(r"\{[^}]+\}")

def extract_percent(text):
    return PERCENT_PATTERN.findall(text or "")

def extract_brace(text):
    return BRACE_PATTERN.findall(text or "")

def fix_file(po_path):
    print(f"🔧 {po_path}")
    po = polib.pofile(str(po_path))
    modified = False

    for entry in po:
        if not entry.msgid:
            continue

        id_percent = extract_percent(entry.msgid)
        str_percent = extract_percent(entry.msgstr)

        id_brace = extract_brace(entry.msgid)
        str_brace = extract_brace(entry.msgstr)

        # 1️⃣ Corriger incompatibilités
        if id_percent != str_percent or id_brace != str_brace:
            print(f"  ⚠️ Correction placeholders ligne {entry.linenum}")
            entry.msgstr = entry.msgid
            modified = True

        # 2️⃣ Corriger flag python-format incohérent
        if "python-format" in entry.flags:
            if not id_percent:
                entry.flags.remove("python-format")
                modified = True

    if modified:
        po.save()
        print("  ✅ Corrigé")
    else:
        print("  ✅ OK")

def main():
    translations = Path("translations")
    for po in translations.rglob("*.po"):
        fix_file(po)

    print("✅ Nettoyage terminé")
    return 0

if __name__ == "__main__":
    sys.exit(main())
