#!/usr/bin/env python3
"""
Complète les traductions manquantes en utilisant final_working comme référence
"""

import polib
import os

def complete_from_final(ar_file, final_file):
    """Complète les traductions manquantes depuis final_working"""
    
    print(f"📖 Lecture du fichier arabe: {ar_file}")
    print(f"📖 Lecture du fichier final_working: {final_file}")
    
    ar = polib.pofile(ar_file)
    final = polib.pofile(final_file)
    
    # Créer un dictionnaire des traductions final_working
    final_dict = {entry.msgid: entry.msgstr for entry in final}
    
    fixed = 0
    total = len(ar)
    
    for entry in ar:
        if not entry.msgstr or entry.msgstr == "":
            if entry.msgid in final_dict and final_dict[entry.msgid]:
                entry.msgstr = final_dict[entry.msgid]
                fixed += 1
    
    ar.save()
    
    print(f"\n✅ {fixed} traductions complétées depuis final_working")
    print(f"📊 Total: {total}, Reste: {total - fixed}")
    
    return fixed

if __name__ == "__main__":
    complete_from_final(
        'translations/ar/LC_MESSAGES/messages.po',
        'translations_final_working/ar/LC_MESSAGES/messages.po'
    )
    
    # Vérifier le résultat
    print("\n📈 Statistiques finales:")
    os.system("msgfmt --statistics translations/ar/LC_MESSAGES/messages.po 2>&1 | tail -1")
