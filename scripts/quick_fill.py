#!/usr/bin/env python3
# scripts/fix_all_duplicates.py

import os
import re
import subprocess

LANGUAGES = ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl', 'ar', 'zh', 'ja', 'ru']

def clean_duplicate_msgstr(content):
    """Nettoie les doublons dans les msgstr multilignes"""
    
    # Pattern pour trouver les msgstr avec répétitions
    # Capture le contenu d'un msgstr et cherche s'il se répète
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('msgstr "'):
            # Extraire le contenu du msgstr
            current_msgstr = line[8:]
            
            # Vérifier les lignes suivantes (pour les msgstr multilignes)
            full_msgstr = current_msgstr
            j = i + 1
            while j < len(lines) and lines[j].startswith('"'):
                full_msgstr += lines[j][1:]
                j += 1
            
            # Nettoyer les doublons
            cleaned = clean_duplicates_in_text(full_msgstr)
            
            # Réécrire le msgstr
            if cleaned != full_msgstr:
                # Reconstruire le msgstr nettoyé
                new_lines.append(f'msgstr "{cleaned.split(chr(34))[0] if chr(34) in cleaned else cleaned}"')
                i = j
                continue
        
        new_lines.append(line)
        i += 1
    
    return '\n'.join(new_lines)

def clean_duplicates_in_text(text):
    """Nettoie les doublons dans un texte"""
    
    # Supprimer les répétitions de phrases entières
    sentences = re.split(r'(?<=[.!?])\s+', text)
    unique_sentences = []
    last = None
    
    for sentence in sentences:
        if sentence != last:
            unique_sentences.append(sentence)
            last = sentence
    
    return ' '.join(unique_sentences)

def fix_known_duplicates(content):
    """Corrige les doublons connus spécifiques"""
    
    # Correction pour le texte DOCX
    docx_text = "The generated file is in DOCX format, compatible with Microsoft Word 2007 and later, as well as LibreOffice and Google Docs."
    pattern = re.escape(docx_text)
    content = re.sub(f'({pattern})\\1+', docx_text, content)
    
    return content

def process_file(po_file, lang):
    """Traite un fichier .po"""
    
    if not os.path.exists(po_file):
        print(f"  ⚠️ {lang}: fichier non trouvé")
        return False
    
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Corriger les doublons connus
    content = fix_known_duplicates(content)
    
    # Nettoyage général
    content = clean_duplicate_msgstr(content)
    
    if content != original_content:
        with open(po_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    print("=" * 60)
    print("🔧 CORRECTION DES DOUBLONS DANS LES TRADUCTIONS")
    print("=" * 60)
    print()
    
    fixed = []
    for lang in LANGUAGES:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        print(f"📝 Traitement de {lang}...")
        
        if process_file(po_file, lang):
            print(f"  ✅ Doublons corrigés")
            fixed.append(lang)
        else:
            print(f"  ✓ Aucun problème détecté")
        print()
    
    if fixed:
        print(f"📊 Langues corrigées: {', '.join(fixed)}")
        print()
        
        print("📦 Recompilation...")
        subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'])
    else:
        print("📊 Aucune correction nécessaire")
    
    print()
    print("✨ Terminé!")

if __name__ == "__main__":
    main()