#!/usr/bin/env python3
# scripts/fix_placeholders.py
# Version robuste compatible Babel production

import polib
import re
from pathlib import Path
import sys

# Support :
# %(name)s
# %s %d %f
# {0} {name}
PLACEHOLDER_PATTERN = re.compile(
    r"%\([^)]+\)[sdifeEgGxX]|%[sdifeEgGxX]|\{[^}]+\}"
)

def extract_placeholders(text):
    return sorted(PLACEHOLDER_PATTERN.findall(text or ""))

def fix_placeholders_in_file(po_file):
    print(f"🔧 Traitement de {po_file}...")

    try:
        po = polib.pofile(str(po_file))
    except Exception as e:
        print(f"  ❌ Erreur lecture: {e}")
        return False

    modified = False
    checked = 0
    fixed = 0

    for entry in po:
        if not entry.msgid:
            continue

        checked += 1

        msgid_ph = extract_placeholders(entry.msgid)
        msgstr_ph = extract_placeholders(entry.msgstr)

        if msgid_ph != msgstr_ph:
            print(f"  ⚠️ Incompatibilité ligne {entry.linenum}")
            print(f"     msgid placeholders : {msgid_ph}")
            print(f"     msgstr placeholders: {msgstr_ph}")

            # Correction radicale et sûre
            entry.msgstr = entry.msgid
            modified = True
            fixed += 1

    if modified:
        po.save()
        print(f"  ✅ {fixed}/{checked} entrées corrigées")
    else:
        print(f"  ✅ OK ({checked} entrées vérifiées)")

    return True

def main():
    print("🔍 Vérification des placeholders Babel")
    print("=" * 60)

    translations_dir = Path("translations")
    if not translations_dir.exists():
        print("❌ Dossier translations introuvable")
        return 1

    po_files = list(translations_dir.rglob("*.po"))
    if not po_files:
        print("❌ Aucun fichier .po trouvé")
        return 1

    success = 0
    for po_file in po_files:
        if fix_placeholders_in_file(po_file):
            success += 1
        print()

    print("=" * 60)
    print(f"📊 {success}/{len(po_files)} fichiers traités")

    return 0

if __name__ == "__main__":
    sys.exit(main())
