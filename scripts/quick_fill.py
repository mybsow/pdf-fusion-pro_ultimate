#!/usr/bin/env python3
# scripts/translate_all.py

from deep_translator import GoogleTranslator
import os
import re
import time

# Mapping des langues pour Google Translate
LANGS = {
    "fr": "fr",
    "en": "en",
    "es": "es",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "nl": "nl",
    "ar": "ar",
    "ja": "ja",
    "ru": "ru",
    "zh": "zh-CN"  # Important: zh-CN et pas zh
}

def extract_multiline_msgid(lines, start_index):
    """Extrait un msgid qui peut être sur plusieurs lignes"""
    msgid_parts = []
    i = start_index
    line = lines[i]
    
    # Première partie: msgid "texte"
    match = re.search(r'msgid "(.+)"', line)
    if match:
        msgid_parts.append(match.group(1))
    else:
        # Format multiligne: msgid "" puis ligne suivante avec le texte
        if line.strip() == 'msgid ""':
            i += 1
            while i < len(lines):
                line = lines[i]
                if line.strip().startswith('"') and not line.strip().startswith('msgstr'):
                    # Extraire le texte entre guillemets
                    text_match = re.search(r'"(.+)"', line)
                    if text_match:
                        msgid_parts.append(text_match.group(1))
                    i += 1
                else:
                    break
            return ''.join(msgid_parts), i - 1
    
    return msgid_parts[0] if msgid_parts else None, i

def extract_msgid_full(lines, start_index):
    """Extrait un msgid complet (peut être multiligne)"""
    msgid_parts = []
    i = start_index
    
    # Vérifier si c'est un msgid multiligne (msgid "" sur sa propre ligne)
    if lines[i].strip() == 'msgid ""':
        i += 1
        # Lire toutes les lignes suivantes qui commencent par "
        while i < len(lines) and lines[i].strip().startswith('"') and not lines[i].strip().startswith('msgstr'):
            match = re.search(r'"([^"]*)"', lines[i])
            if match:
                msgid_parts.append(match.group(1))
            i += 1
        return ''.join(msgid_parts), i - 1
    
    # Msgid sur une seule ligne
    match = re.search(r'msgid "(.+)"', lines[i])
    if match:
        return match.group(1), i
    
    return None, i

def translate_text(text, target_lang):
    """Traduit un texte avec gestion des erreurs"""
    if not text or len(text) < 2:
        return text
    
    # Ne pas traduire les placeholders seuls
    if re.match(r'^%\([a-z_]+\)[sd]$', text):
        return text
    
    try:
        translator = GoogleTranslator(source='fr', target=target_lang)
        translated = translator.translate(text)
        time.sleep(0.1)  # Pause pour éviter la limitation d'API
        return translated
    except Exception as e:
        print(f"      ⚠️ Erreur: {text[:50]}... -> {e}")
        return text

def process_po_file(po_file, lang_code):
    """Traduit les msgstr vides dans un fichier .po (gère les multilignes)"""
    
    if not os.path.exists(po_file):
        print(f"  ❌ {lang_code}: fichier non trouvé")
        return 0
    
    print(f"  🌍 Traduction de {lang_code}...")
    
    with open(po_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    translated_count = 0
    total_empty = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Détecter le début d'un msgid
        if line.startswith('msgid'):
            # Extraire le msgid complet (peut être multiligne)
            msgid, end_idx = extract_msgid_full(lines, i)
            
            # Chercher le msgstr correspondant
            j = end_idx + 1
            msgstr_line_index = -1
            
            while j < len(lines):
                if lines[j].startswith('msgstr'):
                    msgstr_line_index = j
                    break
                j += 1
            
            if msgstr_line_index != -1:
                msgstr_line = lines[msgstr_line_index]
                
                # Vérifier si le msgstr est vide
                if msgstr_line.strip() == 'msgstr ""':
                    total_empty += 1
                    
                    if msgid and not msgid.startswith('Project-Id-Version'):
                        # Traduire
                        translated = translate_text(msgid, lang_code)
                        # Remplacer la ligne msgstr
                        lines[msgstr_line_index] = f'msgstr "{translated}"\n'
                        translated_count += 1
                        
                        if translated_count % 20 == 0:
                            print(f"      ✅ {translated_count} traductions...")
            
            # Ajouter toutes les lignes jusqu'à la fin de cette entrée
            for k in range(i, j + 1 if msgstr_line_index != -1 else i + 1):
                if k < len(lines):
                    new_lines.append(lines[k])
            
            i = j + 1 if msgstr_line_index != -1 else i + 1
        else:
            new_lines.append(line)
            i += 1
    
    # Sauvegarder si des modifications ont été faites
    if translated_count > 0:
        with open(po_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"  ✅ {lang_code}: {translated_count}/{total_empty} traductions ajoutées")
    else:
        print(f"  ✓ {lang_code}: aucune traduction nécessaire")
    
    return translated_count

def main():
    print("🤖 TRAduction des msgstr vides (gère les multilignes)")
    print("=" * 60)
    print()
    
    total = 0
    for lang_code, target_lang in LANGS.items():
        po_file = f"translations/{lang_code}/LC_MESSAGES/messages.po"
        total += process_po_file(po_file, target_lang)
        print()
    
    print(f"📊 Total: {total} nouvelles traductions ajoutées")
    print()
    print("✨ Terminé!")

if __name__ == "__main__":
    main()