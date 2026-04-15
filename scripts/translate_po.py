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

def is_msgstr_empty(lines, msgstr_start_idx):
    """Vérifie si un msgstr est vraiment vide (même multiligne)"""
    i = msgstr_start_idx
    line = lines[i]
    
    # Cas simple: msgstr "" sur une ligne
    if line.strip() == 'msgstr ""':
        return True
    
    # Cas multiligne: msgstr "" puis lignes vides ""
    if line.strip() == 'msgstr ""':
        i += 1
        while i < len(lines):
            current = lines[i].strip()
            # Si on trouve du texte non vide, le msgstr n'est pas vide
            if current.startswith('"') and current != '""':
                # Vérifier si la ligne contient autre chose que des guillemets vides
                match = re.search(r'"([^"]*)"', lines[i])
                if match and match.group(1).strip():
                    return False
            # Si on arrive au prochain msgid, on a fini
            if current.startswith('msgid') or current.startswith('#:'):
                break
            i += 1
        return True
    
    return False

def get_msgstr_end_index(lines, msgstr_start_idx):
    """Trouve l'index de fin du bloc msgstr"""
    i = msgstr_start_idx
    if lines[i].strip() == 'msgstr ""':
        i += 1
        # Continuer tant qu'on est dans le bloc msgstr multiligne
        while i < len(lines):
            current = lines[i].strip()
            if current.startswith('"') and not current.startswith('msgstr'):
                i += 1
            else:
                break
    return i

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

def split_text_for_po(text, max_length=70):
    """Divise un texte long en plusieurs lignes pour le format .po"""
    if len(text) <= max_length:
        return [text]
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += (" " + word) if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

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
    skipped_count = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Détecter le début d'un msgid
        if line.startswith('msgid'):
            # Extraire le msgid complet
            msgid, msgid_end = extract_msgid_full(lines, i)
            
            # Chercher le msgstr correspondant
            j = msgid_end + 1
            msgstr_line_index = -1
            
            while j < len(lines):
                if lines[j].startswith('msgstr'):
                    msgstr_line_index = j
                    break
                j += 1
            
            if msgstr_line_index != -1:
                # Vérifier si le msgstr est VRAIMENT vide
                if is_msgstr_empty(lines, msgstr_line_index):
                    total_empty += 1
                    
                    # Ignorer les entêtes du fichier .po
                    if msgid and not msgid.startswith('Project-Id-Version') and not msgid.startswith('Plural-Forms'):
                        # Traduire
                        print(f"      🌐 Traduction: {msgid[:60]}...")
                        translated = translate_text(msgid, lang_code)
                        
                        # Formater la traduction pour .po
                        translated_lines = split_text_for_po(translated)
                        
                        # Remplacer le bloc msgstr
                        if len(translated_lines) == 1:
                            lines[msgstr_line_index] = f'msgstr "{translated_lines[0]}"\n'
                        else:
                            lines[msgstr_line_index] = 'msgstr ""\n'
                            for idx, tline in enumerate(translated_lines):
                                lines.insert(msgstr_line_index + 1 + idx, f'"{tline}"\n')
                        
                        translated_count += 1
                        
                        if translated_count % 10 == 0:
                            print(f"      ✅ {translated_count} traductions...")
                else:
                    skipped_count += 1
            
            # Ajouter toutes les lignes jusqu'à la fin de cette entrée
            msgstr_end = get_msgstr_end_index(lines, msgstr_line_index) if msgstr_line_index != -1 else j
            for k in range(i, msgstr_end):
                if k < len(lines):
                    new_lines.append(lines[k])
            
            i = msgstr_end
        else:
            new_lines.append(line)
            i += 1
    
    # Sauvegarder si des modifications ont été faites
    if translated_count > 0:
        with open(po_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"  ✅ {lang_code}: {translated_count} traductions ajoutées ({skipped_count} déjà traduites)")
    else:
        print(f"  ✓ {lang_code}: toutes les entrées sont déjà traduites ({skipped_count} existantes)")
    
    return translated_count

def main():
    print("🤖 Traduction des msgstr vides (gère les multilignes)")
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