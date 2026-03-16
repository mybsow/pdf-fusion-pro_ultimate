#!/usr/bin/env python3
"""
fix_multiline_po.py
Corrige les entrées multi-lignes mal formatées dans les fichiers .po
qui causent : "WARNING: Got line starting with ' but not in msgid, msgstr or msgctxt"

Usage:
    python scripts/fix_multiline_po.py
"""

import re
from pathlib import Path

TRANSLATIONS_DIR = Path("translations")

def fix_po_file(po_path: Path) -> int:
    """
    Fusionne les lignes de continuation orphelines.
    Retourne le nombre de corrections effectuées.
    """
    original = po_path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)

    fixed_lines = []
    fixes = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Ligne normale msgid / msgstr / msgctxt qui ouvre une chaîne
        if re.match(r'^(msgid|msgstr|msgctxt|msgid_plural)\s+"', line):
            # Collecter toutes les lignes de continuation suivantes
            block = [line.rstrip('\n')]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                # Ligne de continuation valide : commence par "
                if re.match(r'^\s*"', next_line):
                    block.append(next_line.rstrip('\n'))
                    j += 1
                else:
                    break

            if len(block) == 1:
                # Pas de continuation, on garde tel quel
                fixed_lines.append(line)
            else:
                # Fusionner toutes les parties en une seule ligne
                # Extraire le préfixe (msgid / msgstr etc.)
                prefix_match = re.match(r'^(msgid|msgstr|msgctxt|msgid_plural)\s+"(.*)"$', block[0])
                if prefix_match:
                    keyword = prefix_match.group(1)
                    parts = [prefix_match.group(2)]
                    for continuation in block[1:]:
                        # Extraire le contenu entre guillemets
                        cont_match = re.match(r'^\s*"(.*)"$', continuation)
                        if cont_match:
                            parts.append(cont_match.group(1))
                        else:
                            # Ligne malformée sans guillemet fermant — on la garde brute
                            parts.append(continuation.strip().strip('"'))
                    merged = keyword + ' "' + "".join(parts) + '"\n'
                    fixed_lines.append(merged)
                    fixes += len(block) - 1
                else:
                    # Impossible de parser — on garde tel quel
                    fixed_lines.extend(l + '\n' for l in block)

            i = j

        else:
            fixed_lines.append(line)
            i += 1

    result = "".join(fixed_lines)

    if result != original:
        # Sauvegarder l'original en .bak avant modification
        bak_path = po_path.with_suffix(".po.multiline.bak")
        bak_path.write_text(original, encoding="utf-8")
        po_path.write_text(result, encoding="utf-8")
        print(f"  ✅ {po_path} — {fixes} lignes fusionnées (backup: {bak_path.name})")
    else:
        print(f"  ✔  {po_path} — aucune correction nécessaire")

    return fixes


def main():
    print("🔧 Correction des entrées multi-lignes dans les fichiers .po\n")

    po_files = sorted(TRANSLATIONS_DIR.glob("*/LC_MESSAGES/messages.po"))

    if not po_files:
        print("❌ Aucun fichier .po trouvé dans translations/")
        return

    total_fixes = 0
    for po_file in po_files:
        total_fixes += fix_po_file(po_file)

    print(f"\n✅ Terminé — {total_fixes} corrections au total sur {len(po_files)} fichiers")
    print("\n👉 Recompilez maintenant avec :")
    print("   pybabel compile -d translations")
    print("   git add translations/*/LC_MESSAGES/messages.po translations/*/LC_MESSAGES/messages.mo")
    print("   git commit -m 'fix: correction multi-lignes .po et recompilation .mo'")
    print("   git push")


if __name__ == "__main__":
    main()