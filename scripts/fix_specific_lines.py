#!/usr/bin/env python3
"""
Script final pour corriger toutes les erreurs de placeholders
"""

import os
import re

def fix_all_errors():
    # Liste de tous les fichiers avec leurs lignes problématiques
    error_lines = {
        'translations/pt/LC_MESSAGES/messages.po': [5362],
        'translations/it/LC_MESSAGES/messages.po': [5367],
        'translations/de/LC_MESSAGES/messages.po': [5378, 5487],
        'translations/ja/LC_MESSAGES/messages.po': [5247, 5350],
        'translations/ru/LC_MESSAGES/messages.po': [5369, 5476],
        'translations/ar/LC_MESSAGES/messages.po': [5311, 5416],
        'translations/nl/LC_MESSAGES/messages.po': [5374],
        'translations/zh/LC_MESSAGES/messages.po': [5245, 5348],
        'translations/en/LC_MESSAGES/messages.po': [5329]
    }
    
    for po_file, lines in error_lines.items():
        if not os.path.exists(po_file):
            print(f"⚠️ Fichier non trouvé: {po_file}")
            continue
            
        print(f"\n📁 Correction de {po_file}")
        
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        modified = False
        
        for line_num in lines:
            idx = line_num - 1
            if idx >= len(content):
                continue
                
            original = content[idx]
            print(f"  Ligne {line_num}: {original.strip()}")
            
            # Correction 1: Remplacer 100%%% par 100%%
            if '100%%%' in original:
                content[idx] = original.replace('100%%%', '100%%')
                print(f"    ✅ 100%%% → 100%%")
                modified = True
            
            # Correction 2: Remplacer 100% par 100%% si nécessaire
            elif '100%' in original and '100%%' not in original:
                # Vérifier si c'est dans un msgstr qui doit avoir des doubles %
                if 'msgstr "' in original:
                    content[idx] = original.replace('100%', '100%%')
                    print(f"    ✅ 100% → 100%%")
                    modified = True
            
            # Correction 3: Vérifier les placeholders manquants dans les msgstr
            if original.startswith('msgstr "'):
                # Chercher le msgid correspondant (ligne précédente ou suivante?)
                msgid_line = ""
                if idx > 0 and content[idx-1].startswith('msgid "'):
                    msgid_line = content[idx-1]
                elif idx > 1 and content[idx-2].startswith('msgid "'):
                    msgid_line = content[idx-2]
                
                if msgid_line:
                    # Extraire les placeholders du msgid
                    msgid_placeholders = re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', msgid_line)
                    if msgid_placeholders:
                        # Vérifier s'ils sont dans msgstr
                        for ph in msgid_placeholders:
                            if ph not in original:
                                print(f"    ⚠️ Placeholder {ph} manquant dans msgstr")
                                # Option: ajouter automatiquement?
                                # content[idx] = content[idx].replace('msgstr "', f'msgstr "{ph} ')
                                # modified = True
        
        if modified:
            backup = po_file + '.final2.bak'
            with open(backup, 'w', encoding='utf-8') as f:
                f.writelines(content)
            
            with open(po_file, 'w', encoding='utf-8') as f:
                f.writelines(content)
            print(f"  ✅ Modifications enregistrées (backup: {backup})")
        else:
            print(f"  ✓ Aucune modification nécessaire")

def fix_triple_percent_specific():
    """Corrige spécifiquement les lignes avec 100%%%"""
    
    files_with_triple = [
        ('translations/de/LC_MESSAGES/messages.po', 5487),
        ('translations/ja/LC_MESSAGES/messages.po', 5350),
        ('translations/ru/LC_MESSAGES/messages.po', 5476),
        ('translations/ar/LC_MESSAGES/messages.po', 5416),
        ('translations/zh/LC_MESSAGES/messages.po', 5348)
    ]
    
    for po_file, line_num in files_with_triple:
        if not os.path.exists(po_file):
            continue
            
        print(f"\n🔧 Correction triple % dans {po_file} ligne {line_num}")
        
        with open(po_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        idx = line_num - 1
        if idx < len(lines) and '100%%%' in lines[idx]:
            old_line = lines[idx]
            lines[idx] = old_line.replace('100%%%', '100%%')
            print(f"  Avant: {old_line.strip()}")
            print(f"  Après: {lines[idx].strip()}")
            
            backup = po_file + '.triple.bak'
            with open(backup, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            with open(po_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  ✅ Corrigé (backup: {backup})")

def main():
    print("🔍 CORRECTION FINALE DES ERREURS")
    print("=" * 60)
    
    # D'abord corriger les triples pourcents
    fix_triple_percent_specific()
    
    # Ensuite correction générale
    fix_all_errors()
    
    print("\n" + "=" * 60)
    print("🔄 Recompilez maintenant avec:")
    print("   pybabel compile -d translations")
    
    # Test automatique
    print("\n🔎 Test de compilation...")
    result = os.system("pybabel compile -d translations 2>&1 | tee /tmp/compile_result.log")
    
    # Compter les erreurs
    with open('/tmp/compile_result.log', 'r') as f:
        errors = sum(1 for line in f if 'error:' in line)
    
    if errors == 0:
        print("✅ SUCCÈS: Plus aucune erreur!")
    else:
        print(f"⚠️ Il reste {errors} erreurs. Vérifiez /tmp/compile_result.log")

if __name__ == "__main__":
    response = input("⚠️  Ce script va modifier les fichiers .po. Continuer? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        main()
    else:
        print("Annulé.")