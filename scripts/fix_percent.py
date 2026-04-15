#!/usr/bin/env python3
# scripts/extract_conversion_map_safe.py

import re
import os
import ast
from pathlib import Path

# Liste des textes à extraire de CONVERSION_MAP
CONVERSION_TEXTS = {
    'fr': {
        # Titres
        'Word vers PDF': 'Word vers PDF',
        'Excel vers PDF': 'Excel vers PDF', 
        'PowerPoint vers PDF': 'PowerPoint vers PDF',
        'Image vers PDF': 'Image vers PDF',
        'JPG vers PDF': 'JPG vers PDF',
        'PNG vers PDF': 'PNG vers PDF',
        'HTML vers PDF': 'HTML vers PDF',
        'TXT vers PDF': 'TXT vers PDF',
        'PDF vers Word': 'PDF vers Word',
        'PDF vers DOC': 'PDF vers DOC',
        'PDF vers Excel': 'PDF vers Excel',
        'PDF vers PowerPoint': 'PDF vers PowerPoint',
        'PDF vers Image': 'PDF vers Image',
        'PDF vers PDF/A': 'PDF vers PDF/A',
        'PDF vers HTML': 'PDF vers HTML',
        'PDF vers TXT': 'PDF vers TXT',
        'Protéger PDF': 'Protéger PDF',
        'Déverrouiller PDF': 'Déverrouiller PDF',
        'Caviarder PDF': 'Caviarder PDF',
        'Éditer PDF': 'Éditer PDF',
        'Signer PDF': 'Signer PDF',
        'Préparer formulaire PDF': 'Préparer formulaire PDF',
        'Image vers Word': 'Image vers Word',
        'Image vers Excel': 'Image vers Excel',
        'CSV vers Excel': 'CSV vers Excel',
        'Excel vers CSV': 'Excel vers CSV',
        
        # Descriptions
        'Convertissez vos documents Word en PDF': 'Convertissez vos documents Word en PDF',
        'Convertissez vos feuilles Excel en PDF': 'Convertissez vos feuilles Excel en PDF',
        'Convertissez vos présentations PowerPoint en PDF': 'Convertissez vos présentations PowerPoint en PDF',
        'Convertissez vos images en document PDF': 'Convertissez vos images en document PDF',
        'Convertissez vos images JPG en PDF': 'Convertissez vos images JPG en PDF',
        'Convertissez vos images PNG en PDF': 'Convertissez vos images PNG en PDF',
        'Convertissez vos pages HTML en PDF': 'Convertissez vos pages HTML en PDF',
        'Convertissez vos fichiers texte en PDF': 'Convertissez vos fichiers texte en PDF',
        'Extrayez le texte de vos PDF en documents Word': 'Extrayez le texte de vos PDF en documents Word',
        'Convertissez vos PDF en documents Word (format DOC)': 'Convertissez vos PDF en documents Word (format DOC)',
        'Extrayez les tableaux de vos PDF en feuilles Excel': 'Extrayez les tableaux de vos PDF en feuilles Excel',
        'Convertissez vos PDF en présentations PowerPoint modifiables': 'Convertissez vos PDF en présentations PowerPoint modifiables',
        'Convertissez les pages de vos PDF en images': 'Convertissez les pages de vos PDF en images',
        'Convertissez vos PDF en format PDF/A pour l\'archivage': 'Convertissez vos PDF en format PDF/A pour l\'archivage',
        'Convertissez vos PDF en pages HTML': 'Convertissez vos PDF en pages HTML',
        'Extrayez le texte de vos PDF en fichiers texte': 'Extrayez le texte de vos PDF en fichiers texte',
        'Ajoutez un mot de passe pour protéger vos PDF': 'Ajoutez un mot de passe pour protéger vos PDF',
        'Retirez la protection des PDF': 'Retirez la protection des PDF',
        'Supprimez définitivement le contenu sensible de votre PDF': 'Supprimez définitivement le contenu sensible de votre PDF',
        'Modifiez ou ajoutez du texte, des images et des pages à votre PDF': 'Modifiez ou ajoutez du texte, des images et des pages à votre PDF',
        'Ajoutez votre signature électronique à votre PDF': 'Ajoutez votre signature électronique à votre PDF',
        'Transformez vos documents en formulaires PDF interactifs': 'Transformez vos documents en formulaires PDF interactifs',
        'Extrayez le texte des images en documents Word': 'Extrayez le texte des images en documents Word',
        'Extrayez les tableaux des images en Excel': 'Extrayez les tableaux des images en Excel',
        'Convertissez vos fichiers CSV en Excel': 'Convertissez vos fichiers CSV en Excel',
        'Exportez vos feuilles Excel en CSV': 'Exportez vos feuilles Excel en CSV',
        
        # Formats
        'Word': 'Word',
        'Excel': 'Excel',
        'PowerPoint': 'PowerPoint',
        'Image': 'Image',
        'JPG': 'JPG',
        'PNG': 'PNG',
        'HTML': 'HTML',
        'TXT': 'TXT',
        'PDF': 'PDF',
        'DOC': 'DOC',
        'PDF/A': 'PDF/A',
        'CSV': 'CSV',
        'Document': 'Document',
        'PDF Formulaire': 'PDF Formulaire',
    }
}

def parse_po_file(po_file):
    """Parse un fichier .po et retourne un dict {msgid: msgstr}"""
    translations = {}
    
    if not os.path.exists(po_file):
        return translations
    
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour trouver les paires msgid/msgstr
    pattern = r'msgid "(.+?)"\nmsgstr "(.+?)"'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for msgid, msgstr in matches:
        # Nettoyer les sauts de ligne dans msgid
        msgid_clean = msgid.replace('"\n"', '')
        msgstr_clean = msgstr.replace('"\n"', '')
        translations[msgid_clean] = msgstr_clean
    
    return translations

def add_missing_to_po_file(po_file, texts_to_add, lang):
    """
    Ajoute uniquement les textes MANQUANTS au fichier .po
    Ne modifie PAS les traductions existantes
    """
    
    if not os.path.exists(po_file):
        print(f"  ❌ {lang}: fichier non trouvé - création d'un nouveau fichier")
        # Créer un nouveau fichier avec toutes les entrées
        with open(po_file, 'w', encoding='utf-8') as f:
            f.write(f'# Translations for {lang}\n')
            f.write('msgid ""\nmsgstr ""\n')
            f.write('"Content-Type: text/plain; charset=UTF-8\\n"\n\n')
            
            for original, translation in texts_to_add.items():
                f.write(f'#: blueprints/conversion.py\n')
                f.write(f'msgid "{original}"\n')
                f.write(f'msgstr "{translation}"\n\n')
        print(f"  ✅ {lang}: {len(texts_to_add)} entrées créées")
        return
    
    # Lire les traductions existantes
    existing = parse_po_file(po_file)
    
    # Trouver les entrées manquantes
    missing = {k: v for k, v in texts_to_add.items() if k not in existing}
    
    if not missing:
        print(f"  ✓ {lang}: toutes les entrées existent déjà")
        return
    
    # Ajouter uniquement les entrées manquantes à la fin du fichier
    with open(po_file, 'a', encoding='utf-8') as f:
        f.write('\n# ===== NOUVELLES ENTRÉES (ajoutées automatiquement) =====\n\n')
        
        for original, translation in missing.items():
            f.write(f'#: blueprints/conversion.py\n')
            f.write(f'msgid "{original}"\n')
            f.write(f'msgstr "{translation}"\n\n')
    
    print(f"  ✅ {lang}: {len(missing)} nouvelles entrées ajoutées (préservation de {len(existing)} existantes)")

def add_french_and_leave_others_empty():
    """Ajoute le français et laisse les msgstr vides pour les autres langues"""
    
    target_langs = ['en', 'es', 'de', 'it', 'pt', 'nl', 'ar', 'ja', 'ru', 'zh']
    
    print("\n📝 Traitement des fichiers de traduction...")
    print("=" * 50)
    
    # 1. Ajouter le français avec traductions
    print("\n🇫🇷 Français (avec traductions) :")
    fr_po = "translations/fr/LC_MESSAGES/messages.po"
    add_missing_to_po_file(fr_po, CONVERSION_TEXTS['fr'], 'fr')
    
    # 2. Pour les autres langues, ajouter avec msgstr VIDE
    print("\n🌍 Autres langues (msgstr vides pour traduction manuelle) :")
    empty_texts = {k: "" for k in CONVERSION_TEXTS['fr'].keys()}
    
    for lang in target_langs:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_file):
            add_missing_to_po_file(po_file, empty_texts, lang)
        else:
            print(f"  ⚠️ {lang}: fichier non trouvé, ignoré")

def show_summary():
    """Affiche un résumé des chaînes vides à traduire"""
    
    print("\n📊 RÉSUMÉ DES TRADUCTIONS MANQUANTES")
    print("=" * 50)
    
    target_langs = ['en', 'es', 'de', 'it', 'pt', 'nl', 'ar', 'ja', 'ru', 'zh']
    lang_names = {
        'en': 'Anglais', 'es': 'Espagnol', 'de': 'Allemand',
        'it': 'Italien', 'pt': 'Portugais', 'nl': 'Néerlandais',
        'ar': 'Arabe', 'ja': 'Japonais', 'ru': 'Russe', 'zh': 'Chinois'
    }
    
    for lang in target_langs:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        if os.path.exists(po_file):
            translations = parse_po_file(po_file)
            empty_count = sum(1 for v in translations.values() if v == "")
            total = len(translations)
            
            if empty_count > 0:
                print(f"  {lang_names.get(lang, lang)} ({lang}): {empty_count} chaînes vides / {total} total")
    
    print("\n💡 Utilisez 'grep -B1 \"^msgstr \\\"\\\"$\" translations/XX/LC_MESSAGES/messages.po | grep \"^msgid\"'")
    print("   pour voir les chaînes à traduire pour une langue spécifique.")

def main():
    print("=" * 60)
    print("📝 EXTRACTION SÉCURISÉE - PRÉSERVATION DES TRADUCTIONS")
    print("=" * 60)
    
    # Ajouter les textes sans écraser l'existant
    add_french_and_leave_others_empty()
    
    # Afficher le résumé
    show_summary()
    
    # Recompiler
    print("\n🔨 Recompilation des catalogues...")
    import subprocess
    result = subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Compilation réussie!")
    else:
        print(f"❌ Erreur de compilation:\n{result.stderr}")
    
    print("\n✨ Terminé! Les traductions existantes ont été préservées.")
    print("📝 Les nouvelles chaînes ont été ajoutées avec msgstr vide pour traduction manuelle.")

if __name__ == "__main__":
    main()