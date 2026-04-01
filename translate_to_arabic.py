#!/usr/bin/env python3
"""
Traduire automatiquement les messages anglais vers l'arabe
Utilise LibreTranslate (service gratuit)
"""

import polib
import requests
import time

def translate_text(text, source_lang='en', target_lang='ar'):
    """Traduire un texte avec LibreTranslate"""
    if not text or len(text.strip()) == 0:
        return text
    
    try:
        response = requests.post(
            'https://translate.argosopentech.com/translate',
            json={
                'q': text,
                'source': source_lang,
                'target': target_lang
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['translatedText']
    except Exception as e:
        print(f"Erreur de traduction: {e}")
    return text

def translate_po_file(po_file, output_file=None, max_translations=100):
    """Traduire un fichier .po"""
    if output_file is None:
        output_file = po_file
    
    po = polib.pofile(po_file)
    total = len(po)
    
    print(f"📖 Traduction de {total} messages...")
    print(f"⚠️  Note: Seulement les {max_translations} premières seront traduites")
    print("         pour éviter les limites d'API. Le reste restera en anglais.")
    
    translated = 0
    for i, entry in enumerate(po):
        if not entry.msgstr and i < max_translations:
            print(f"Traduction {i+1}/{min(total, max_translations)}: {entry.msgid[:50]}...")
            translated_text = translate_text(entry.msgid)
            if translated_text and translated_text != entry.msgid:
                entry.msgstr = translated_text
                translated += 1
            time.sleep(0.5)  # Éviter de surcharger l'API
    
    po.save(output_file)
    print(f"\n✅ {translated} messages traduits en arabe")
    print(f"📁 Fichier sauvegardé: {output_file}")

if __name__ == "__main__":
    # Traduire les 100 premiers messages pour commencer
    translate_po_file('translations/ar/LC_MESSAGES/messages.po', 
                      'translations/ar/LC_MESSAGES/messages.po',
                      max_translations=100)
