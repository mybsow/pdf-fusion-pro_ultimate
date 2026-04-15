#!/usr/bin/env python3
# scripts/translate_all_languages.py

import re
import time
import os
from deep_translator import GoogleTranslator

LANG_MAP = {
    'en': 'en', 'es': 'es', 'de': 'de', 'it': 'it', 'pt': 'pt',
    'nl': 'nl', 'ar': 'ar', 'zh': 'zh-CN', 'ja': 'ja', 'ru': 'ru'
}

def translate_po_file(po_file, target_lang):
    """Traduit tous les msgstr vides d'un fichier .po"""
    
    if not os.path.exists(po_file):
        print(f"      ❌ Fichier non trouvé")
        return 0
    
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    translator = GoogleTranslator(source='fr', target=LANG_MAP[target_lang])
    
    # Pattern pour trouver les msgstr vides
    pattern = r'(msgid "(.+?)"\n)msgstr ""'
    
    translated_count = 0
    errors = 0
    
    def translate_match(match):
        nonlocal translated_count, errors
        full_match = match.group(1)
        msgid = match.group(2)
        
        # Ignorer les chaînes techniques ou vides
        if not msgid or len(msgid) < 2:
            return match.group(0)
        
        # Ignorer les chaînes qui ne contiennent que des symboles
        if re.match(r'^[\s\d\W]+$', msgid):
            return match.group(0)
        
        try:
            translated = translator.translate(msgid)
            time.sleep(0.1)  # Petit délai pour éviter d'être bloqué
            translated_count += 1
            return f'{full_match}msgstr "{translated}"'
        except Exception as e:
            errors += 1
            if errors <= 3:  # Afficher seulement les 3 premières erreurs
                print(f"\n      ⚠️ Erreur sur '{msgid[:40]}...' : {e}")
            return match.group(0)
    
    content = re.sub(pattern, translate_match, content, flags=re.DOTALL)
    
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return translated_count

def main():
    print("🌍 Traduction automatique des langues")
    print("=" * 60)
    
    total_translated = 0
    
    for lang, code in LANG_MAP.items():
        po_file = f'translations/{lang}/LC_MESSAGES/messages.po'
        print(f"  🔄 {lang} ({code})...", end=" ", flush=True)
        
        count = translate_po_file(po_file, lang)
        
        if count > 0:
            print(f"✅ {count} chaînes traduites")
            total_translated += count
        else:
            print(f"✓ déjà à jour")
    
    print("=" * 60)
    print(f"✨ Total: {total_translated} chaînes traduites")

if __name__ == "__main__":
    main()
