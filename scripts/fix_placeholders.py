import polib
import re
from pathlib import Path

translations_dir = Path("translations")
placeholder_pattern = re.compile(r"{\w+}|%[sd]")

def extract_placeholders(text):
    return sorted(placeholder_pattern.findall(text))

errors = []

for po_file in translations_dir.rglob("*.po"):
    po = polib.pofile(str(po_file))
    modified = False
    for entry in po:
        if entry.msgstr.strip() == "":
            continue  # ignore empty translations
        msgid_ph = extract_placeholders(entry.msgid)
        msgstr_ph = extract_placeholders(entry.msgstr)
        if msgid_ph != msgstr_ph:
            print(f"[ERREUR] {po_file} | Ligne {entry.lineno}")
            print(f"  msgid placeholders: {msgid_ph}")
            print(f"  msgstr placeholders: {msgstr_ph}")
            
            # Tentative de correction automatique simple
            corrected = entry.msgstr
            for ph in msgid_ph:
                if ph not in msgstr_ph:
                    # ajoute le placeholder manquant
                    corrected += f" {ph}"
                    modified = True
            entry.msgstr = corrected.strip()
    if modified:
        po.save()
        print(f"  -> Corrections appliquées à {po_file}")
