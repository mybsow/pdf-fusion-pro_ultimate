#!/usr/bin/env python3
"""
Utiliser les traductions italiennes comme base (car elles sont complètes)
et les marquer comme à traduire vers l'arabe
"""

import polib
import re

def detect_arabic(text):
    """Détecter si un texte contient déjà de l'arabe"""
    return bool(re.search('[\u0600-\u06FF]', text))

def prepare_for_arabic(ar_file, it_file):
    """Préparer le fichier arabe avec les messages italiens comme commentaires"""
    
    ar = polib.pofile(ar_file)
    it = polib.pofile(it_file)
    
    it_dict = {entry.msgid: entry.msgstr for entry in it}
    
    for entry in ar:
        if entry.msgid in it_dict and it_dict[entry.msgid]:
            # Marquer la traduction italienne comme commentaire
            if not entry.msgstr or not detect_arabic(entry.msgstr):
                entry.comment = f"Italian translation: {it_dict[entry.msgid]}"
    
    ar.save()
    print("✅ Fichier préparé avec commentaires italiens")

if __name__ == "__main__":
    prepare_for_arabic('translations/ar/LC_MESSAGES/messages.po',
                       'translations/it/LC_MESSAGES/messages.po')
