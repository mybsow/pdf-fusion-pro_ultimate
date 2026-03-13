#!/usr/bin/env python3
import os
import re
import sys

def smart_fix_po_file(po_file):
    """Corrige intelligemment les problèmes de formatage"""
    
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Détecter les lignes msgstr
        if line.startswith('msgstr "') and i > 0:
            # Vérifier la ligne msgid précédente
            msgid_line = lines[i-1] if i-1 >= 0 else ""
            
            # Corriger les doubles pourcentages
            if '100%' in line and not '100%%' in line:
                line = line.replace('100%', '100%%')
                modified = True
                print(f"  ✅ 100% corrigé dans {po_file}:{i+1}")
            
            # Vérifier la cohérence des placeholders avec msgid
            if msgid_line.startswith('msgid "'):
                # Extraire les placeholders du msgid
                id_placeholders = set(re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', msgid_line))
                # Extraire les placeholders du msgstr
                str_placeholders = set(re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', line))
                
                # Vérifier si des placeholders manquent
                missing = id_placeholders - str_placeholders
                if missing:
                    print(f"  ⚠️ Placeholders manquants dans {po_file}:{i+1} - {missing}")
                    # Option: ajouter automatiquement
                    for ph in missing:
                        line = line.replace('msgstr "', f'msgstr "{ph} ')
                        modified = True
                        print(f"  ✅ {ph} ajouté automatiquement")
        
        new_lines.append(line)
        i += 1
    
    if modified:
        # Sauvegarde automatique
        backup = po_file + '.smart.bak'
        if not os.path.exists(backup):
            with open(backup, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"  💾 Backup créé: {backup}")
        
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    
    return False

def main():
    translations_dir = 'translations'
    print("🔍 CORRECTION INTELLIGENTE DES FICHIERS .po")
    print("=" * 50)
    
    if not os.path.exists(translations_dir):
        print(f"❌ Dossier {translations_dir} non trouvé")
        return 1
    
    fixed_count = 0
    for lang in os.listdir(translations_dir):
        po_file = os.path.join(translations_dir, lang, 'LC_MESSAGES', 'messages.po')
        if os.path.exists(po_file):
            print(f"\n📁 Traitement de {lang}...")
            if smart_fix_po_file(po_file):
                fixed_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSUMÉ: {fixed_count} fichiers modifiés")
    print("\n🔄 Recompilez avec: pybabel compile -d translations")
    return 0

if __name__ == "__main__":
    # Détection automatique de l'environnement
    try:
        # En mode interactif (terminal)
        sys.exit(main())
    except EOFError:
        # Dans Docker (pas de terminal)
        print("🚀 Mode automatique Docker détecté")
        sys.exit(main())