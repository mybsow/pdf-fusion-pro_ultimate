#!/usr/bin/env python3
# scripts/add_pdf_to_word_translations.py

import re
import os
import subprocess

# Nouveaux textes à traduire
NEW_TEXTS = [
    "Mode de conversion",
    "Hybride (mise en forme + texte éditable) - Recommandé",
    "Texte uniquement (éditable, mise en forme perdue)",
    "Image seule (mise en forme exacte, non éditable)",
    "Le mode hybride préserve l'apparence tout en permettant l'édition"
]

# Traductions pour toutes les langues
TRANSLATIONS = {
    'fr': {
        "Mode de conversion": "Mode de conversion",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Hybride (mise en forme + texte éditable) - Recommandé",
        "Texte uniquement (éditable, mise en forme perdue)": "Texte uniquement (éditable, mise en forme perdue)",
        "Image seule (mise en forme exacte, non éditable)": "Image seule (mise en forme exacte, non éditable)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "Le mode hybride préserve l'apparence tout en permettant l'édition"
    },
    'en': {
        "Mode de conversion": "Conversion mode",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Hybrid (formatting + editable text) - Recommended",
        "Texte uniquement (éditable, mise en forme perdue)": "Text only (editable, formatting lost)",
        "Image seule (mise en forme exacte, non éditable)": "Image only (exact formatting, non-editable)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "Hybrid mode preserves appearance while allowing editing"
    },
    'es': {
        "Mode de conversion": "Modo de conversión",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Híbrido (formato + texto editable) - Recomendado",
        "Texte uniquement (éditable, mise en forme perdue)": "Solo texto (editable, formato perdido)",
        "Image seule (mise en forme exacte, non éditable)": "Solo imagen (formato exacto, no editable)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "El modo híbrido conserva la apariencia permitiendo la edición"
    },
    'de': {
        "Mode de conversion": "Konvertierungsmodus",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Hybrid (Formatierung + bearbeitbarer Text) - Empfohlen",
        "Texte uniquement (éditable, mise en forme perdue)": "Nur Text (bearbeitbar, Formatierung verloren)",
        "Image seule (mise en forme exacte, non éditable)": "Nur Bild (exakte Formatierung, nicht bearbeitbar)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "Der Hybridmodus bewahrt das Erscheinungsbild und ermöglicht die Bearbeitung"
    },
    'it': {
        "Mode de conversion": "Modalità di conversione",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Ibrido (formattazione + testo modificabile) - Consigliato",
        "Texte uniquement (éditable, mise en forme perdue)": "Solo testo (modificabile, formattazione persa)",
        "Image seule (mise en forme exacte, non éditable)": "Solo immagine (formattazione esatta, non modificabile)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "La modalità ibrida preserva l'aspetto consentendo la modifica"
    },
    'pt': {
        "Mode de conversion": "Modo de conversão",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Híbrido (formatação + texto editável) - Recomendado",
        "Texte uniquement (éditable, mise en forme perdue)": "Apenas texto (editável, formatação perdida)",
        "Image seule (mise en forme exacte, non éditable)": "Apenas imagem (formatação exata, não editável)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "O modo híbrido preserva a aparência permitindo a edição"
    },
    'nl': {
        "Mode de conversion": "Conversiemodus",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Hybride (opmaak + bewerkbare tekst) - Aanbevolen",
        "Texte uniquement (éditable, mise en forme perdue)": "Alleen tekst (bewerkbaar, opmaak verloren)",
        "Image seule (mise en forme exacte, non éditable)": "Alleen afbeelding (exacte opmaak, niet bewerkbaar)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "Hybride modus behoudt het uiterlijk en maakt bewerking mogelijk"
    },
    'ar': {
        "Mode de conversion": "وضع التحويل",
        "Hybride (mise en forme + texte éditable) - Recommandé": "هجين (تنسيق + نص قابل للتعديل) - موصى به",
        "Texte uniquement (éditable, mise en forme perdue)": "نص فقط (قابل للتعديل، التنسيق مفقود)",
        "Image seule (mise en forme exacte, non éditable)": "صورة فقط (تنسيق دقيق، غير قابل للتعديل)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "الوضع الهجين يحافظ على المظهر مع السماح بالتعديل"
    },
    'zh': {
        "Mode de conversion": "转换模式",
        "Hybride (mise en forme + texte éditable) - Recommandé": "混合模式（格式 + 可编辑文本）- 推荐",
        "Texte uniquement (éditable, mise en forme perdue)": "仅文本（可编辑，格式丢失）",
        "Image seule (mise en forme exacte, non éditable)": "仅图像（精确格式，不可编辑）",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "混合模式保留外观同时允许编辑"
    },
    'ja': {
        "Mode de conversion": "変換モード",
        "Hybride (mise en forme + texte éditable) - Recommandé": "ハイブリッド（書式 + 編集可能テキスト）- 推奨",
        "Texte uniquement (éditable, mise en forme perdue)": "テキストのみ（編集可能、書式は失われます）",
        "Image seule (mise en forme exacte, non éditable)": "画像のみ（正確な書式、編集不可）",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "ハイブリッドモードは外観を保持しながら編集を可能にします"
    },
    'ru': {
        "Mode de conversion": "Режим конвертации",
        "Hybride (mise en forme + texte éditable) - Recommandé": "Гибридный (форматирование + редактируемый текст) - Рекомендуется",
        "Texte uniquement (éditable, mise en forme perdue)": "Только текст (редактируемый, форматирование потеряно)",
        "Image seule (mise en forme exacte, non éditable)": "Только изображение (точное форматирование, не редактируется)",
        "Le mode hybride préserve l'apparence tout en permettant l'édition": "Гибридный режим сохраняет внешний вид, позволяя редактирование"
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
        for text in NEW_TEXTS:
            if text not in existing:
                missing[text] = TRANSLATIONS[lang].get(text, text)
    
    if not missing:
        return 0
    
    # Ajouter au fichier
    with open(po_file, 'a', encoding='utf-8') as f:
        f.write('\n# ===== PDF TO WORD - MODES DE CONVERSION =====\n')
        f.write('#: templates/conversion/pdf_to_word.html\n\n')
        
        for text, trans in missing.items():
            text_esc = text.replace('"', '\\"')
            trans_esc = trans.replace('"', '\\"')
            f.write(f'msgid "{text_esc}"\n')
            f.write(f'msgstr "{trans_esc}"\n\n')
    
    return len(missing)

def main():
    print("=" * 60)
    print("📝 AJOUT DES TRADUCTIONS POUR PDF_TO_WORD.HTML")
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
    for text in NEW_TEXTS:
        short_text = text[:40] + "..." if len(text) > 40 else text
        print(f"\n  📝 '{short_text}'")
        for lang in ['fr', 'en', 'es', 'de']:
            po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
            if os.path.exists(po_file):
                with open(po_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if f'msgid "{text}"' in content:
                        match = re.search(rf'msgid "{re.escape(text)}"\nmsgstr "([^"]*)"', content)
                        if match:
                            trans = match.group(1)
                            short_trans = trans[:40] + "..." if len(trans) > 40 else trans
                            print(f"    ✅ {lang}: {short_trans}")
                        else:
                            print(f"    ⚠️ {lang}: présent mais msgstr vide")
                    else:
                        print(f"    ❌ {lang}: non trouvé")
    
    print("\n✨ Terminé !")

if __name__ == "__main__":
    main()