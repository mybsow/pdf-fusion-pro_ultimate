#!/usr/bin/env python3
"""
fix_po_orphans.py

Corrige deux problèmes dans les fichiers .po :
1. Lignes '#' seules (commentaires vides) entre des entrées
2. msgstr sur plusieurs lignes avec continuation orpheline

Usage:
    python scripts/fix_po_orphans.py
"""

import re
from pathlib import Path

TRANSLATIONS_DIR = Path("translations")


def fix_po_file(po_path: Path) -> int:
    original = po_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    fixed = []
    fixes = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # --- Supprimer les lignes '#' seules (commentaire vide inutile) ---
        if line.strip() == '#':
            fixes += 1
            i += 1
            continue

        # --- Fusionner msgid / msgstr multi-lignes mal formés ---
        # Pattern : ligne msgid/msgstr se termine sans " fermant
        # ou ligne suivante commence par " sans être une continuation valide

        match = re.match(r'^(msgid|msgstr|msgctxt)\s+"(.*)', line)
        if match:
            keyword = match.group(1)
            content = match.group(2)

            # Si la ligne se termine par " → chaîne complète, pas de continuation
            if content.endswith('"'):
                fixed.append(line)
                i += 1
                continue

            # Sinon, collecter les lignes de continuation
            parts = [content]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                cont = re.match(r'^\s*"(.*)"?\s*$', next_line)
                if cont and next_line.strip().startswith('"'):
                    parts.append(cont.group(1))
                    j += 1
                    fixes += 1
                else:
                    break

            merged = keyword + ' "' + "".join(parts)
            if not merged.endswith('"'):
                merged += '"'
            fixed.append(merged)
            i = j
            continue

        fixed.append(line)
        i += 1

    result = "\n".join(fixed) + "\n"

    if result != original:
        bak = po_path.with_suffix(".po.orphan.bak")
        bak.write_text(original, encoding="utf-8")
        po_path.write_text(result, encoding="utf-8")
        print(f"  ✅ {po_path.parent.parent.name} — {fixes} corrections (backup: {bak.name})")
    else:
        print(f"  ✔  {po_path.parent.parent.name} — aucune correction nécessaire")

    return fixes


def main():
    print("🔧 Correction des orphelins et commentaires vides dans les .po\n")

    po_files = sorted(TRANSLATIONS_DIR.glob("*/LC_MESSAGES/messages.po"))

    if not po_files:
        print("❌ Aucun fichier .po trouvé")
        return

    total = sum(fix_po_file(f) for f in po_files)

    print(f"\n✅ Terminé — {total} corrections sur {len(po_files)} fichiers")
    if total > 0:
        print("\n👉 Recompilez :")
        print("   pybabel compile -d translations")
        print("   ls -la translations/*/LC_MESSAGES/messages.mo")
        print("   git add translations/*/LC_MESSAGES/messages.po translations/*/LC_MESSAGES/messages.mo")
        print("   git commit -m 'fix: correction orphelins .po et recompilation .mo'")
        print("   git push")


if __name__ == "__main__":
    main()