#!/usr/bin/env python3
import os

langs = ['es', 'en', 'de', 'it', 'pt', 'ru', 'ar', 'zh', 'ja', 'nl']

base_translations = {
    'es': {
        'PDF Fusion Pro - Outils PDF Gratuits': 'PDF Fusion Pro - Herramientas PDF Gratuitas',
        'Accueil': 'Inicio',
        'Contact': 'Contacto',
        'À propos': 'Acerca de',
    },
    'en': {
        'PDF Fusion Pro - Outils PDF Gratuits': 'PDF Fusion Pro - Free PDF Tools',
        'Accueil': 'Home',
        'Contact': 'Contact',
        'À propos': 'About',
    },
    # Ajoutez d'autres langues...
}

for lang in langs:
    po_file = f'translations/{lang}/LC_MESSAGES/messages.po'
    if os.path.exists(po_file):
        print(f"Traitement de {lang}...")
        with open(po_file, 'r') as f:
            content = f.read()
        
        for fr, translated in base_translations.get(lang, {}).items():
            if fr in content:
                content = content.replace(
                    f'msgid "{fr}"\nmsgstr ""',
                    f'msgid "{fr}"\nmsgstr "{translated}"'
                )
        
        with open(po_file, 'w') as f:
            f.write(content)