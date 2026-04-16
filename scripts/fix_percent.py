#!/usr/bin/env python3
# scripts/add_missing_edit_pdf_translations.py

import re
import os
import subprocess

# Textes à ajouter
MISSING_TEXTS = [
    "Sélectionnez votre image",
    "Aucune image sélectionnée"
]

# Traductions pour toutes les langues
TRANSLATIONS = {
    'fr': {
        "Sélectionnez votre image": "Sélectionnez votre image",
        "Aucune image sélectionnée": "Aucune image sélectionnée"
    },
    'en': {
        "Sélectionnez votre image": "Select your image",
        "Aucune image sélectionnée": "No image selected"
    },
    'es': {
        "Sélectionnez votre image": "Seleccione su imagen",
        "Aucune image sélectionnée": "Ninguna imagen seleccionada"
    },
    'de': {
        "Sélectionnez votre image": "Wählen Sie Ihr Bild aus",
        "Aucune image sélectionnée": "Kein Bild ausgewählt"
    },
    'it': {
        "Sélectionnez votre image": "Seleziona la tua immagine",
        "Aucune image sélectionnée": "Nessuna immagine selezionata"
    },
    'pt': {
        "Sélectionnez votre image": "Selecione sua imagem",
        "Aucune image sélectionnée": "Nenhuma imagem selecionada"
    },
    'nl': {
        "Sélectionnez votre image": "Selecteer uw afbeelding",
        "Aucune image sélectionnée": "Geen afbeelding geselecteerd"
    },
    'ar': {
        "Sélectionnez votre image": "اختر صورتك",
        "Aucune image sélectionnée": "لم يتم اختيار أي صورة"
    },
    'zh': {
        "Sélectionnez votre image": "选择您的图片",
        "Aucune image sélectionnée": "未选择图片"
    },
    'ja': {
        "Sélectionnez votre image": "画像を選択してください",
        "Aucune image sélectionnée": "画像が選択されていません"
    },
    'ru': {
        "Sélectionnez votre image": "Выберите изображение",
        "Aucune image sélectionnée": "Изображение не выбрано"
    }
}

def parse_existing_msgids(po_file):
    """Retourne l'ensemble des msgid existants"""
    existing = set()
    
    if not os.path.exists(po_file):
        return existing
    
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'msgid "(.+?)"\nmsgstr'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for m in matches:
            clean = m.replace('"\n"', '')
            existing.add(clean)
    except:
        pass
    
    return existing

def add_translations(po_file, lang):
    """Ajoute les traductions manquantes sans doublons"""
    
    if not os.path.exists(po_file):
        print(f"  ❌ {lang}: fichier non trouvé")
        return 0
    
    existing = parse_existing_msgids(po_file)
    
    # Trouver les textes manquants
    missing = {}
    if lang in TRANSLATIONS:
        for text in MISSING_TEXTS:
            if text not in existing:
                missing[text] = TRANSLATIONS[lang].get(text, text)
    
    if not missing:
        return 0
    
    # Ajouter au fichier
    with open(po_file, 'a', encoding='utf-8') as f:
        f.write('\n# ===== EDIT PDF - IMAGE SECTION =====\n')
        f.write('#: templates/conversion/edit_pdf.html\n\n')
        
        for text, trans in missing.items():
            text_esc = text.replace('"', '\\"')
            trans_esc = trans.replace('"', '\\"')
            f.write(f'msgid "{text_esc}"\n')
            f.write(f'msgstr "{trans_esc}"\n\n')
    
    return len(missing)

def main():
    print("=" * 60)
    print("📝 AJOUT DES TRADUCTIONS POUR EDIT_PDF.HTML")
    print("=" * 60)
    
    languages = ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl', 'ar', 'zh', 'ja', 'ru']
    lang_names = {
        'fr': 'Français', 'en': 'Anglais', 'es': 'Espagnol', 'de': 'Allemand',
        'it': 'Italien', 'pt': 'Portugais', 'nl': 'Néerlandais', 'ar': 'Arabe',
        'zh': 'Chinois', 'ja': 'Japonais', 'ru': 'Russe'
    }
    
    total_added = 0
    
    for lang in languages:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if not os.path.exists(po_file):
            print(f"  ❌ {lang}: fichier non trouvé")
            continue
        
        added = add_translations(po_file, lang)
        
        if added > 0:
            print(f"  ✅ {lang_names[lang]} ({lang}): {added} textes ajoutés")
            total_added += added
        else:
            print(f"  ✓ {lang_names[lang]} ({lang}): déjà présents")
    
    print("=" * 60)
    print(f"✨ Total: {total_added} traductions ajoutées")
    
    if total_added > 0:
        print("\n🔨 Compilation...")
        result = subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Compilation réussie !")
        else:
            print(f"❌ Erreur de compilation")
    
    # Vérification
    print("\n📋 Vérification :")
    for text in MISSING_TEXTS:
        print(f"\n  📝 '{text}'")
        for lang in ['fr', 'en', 'es', 'de']:
            po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
            if os.path.exists(po_file):
                with open(po_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if f'msgid "{text}"' in content:
                        match = re.search(rf'msgid "{text}"\nmsgstr "([^"]*)"', content)
                        if match:
                            print(f"    ✅ {lang}: {match.group(1)[:40]}...")
                        else:
                            print(f"    ⚠️ {lang}: présent mais msgstr vide")
                    else:
                        print(f"    ❌ {lang}: non trouvé")
    
    print("\n✨ Terminé !")

if __name__ == "__main__":
    main()