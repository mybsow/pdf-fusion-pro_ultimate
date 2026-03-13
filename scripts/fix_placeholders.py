#!/usr/bin/env python3
"""
Script complet pour corriger tous les problèmes de placeholders dans les fichiers .po
Version automatique pour Docker (détection automatique)
"""

import os
import re
import shutil
import sys
from pathlib import Path

def fix_placeholders_in_file(po_file, force=False):
    """
    Corrige les placeholders manquants dans un fichier .po
    """
    print(f"\n📁 Traitement de {po_file}...")
    
    try:
        with open(po_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ❌ Erreur lecture: {e}")
        return False
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Chercher les lignes msgid avec des placeholders
        if line.startswith('msgid "') and '%' in line:
            # Extraire tous les placeholders du msgid
            msgid_placeholders = set(re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', line))
            
            if msgid_placeholders:
                # Trouver le msgstr correspondant (la prochaine ligne msgstr)
                j = i + 1
                while j < len(lines) and not lines[j].startswith('msgstr "'):
                    j += 1
                
                if j < len(lines):
                    msgstr_line = j
                    # Extraire les placeholders du msgstr
                    msgstr_placeholders = set(re.findall(r'(%\([^)]+\)[diouxXeEfFgGcs])', lines[msgstr_line]))
                    
                    # Trouver les placeholders manquants
                    missing = msgid_placeholders - msgstr_placeholders
                    
                    if missing:
                        print(f"  ✅ Correction à la ligne {msgstr_line+1}: ajout de {missing}")
                        
                        # Ajouter les placeholders manquants au début du msgstr
                        current_msgstr = lines[msgstr_line]
                        prefix = ' '.join(missing) + ' '
                        
                        # Insérer après 'msgstr "'
                        if 'msgstr "' in current_msgstr:
                            new_msgstr = current_msgstr.replace('msgstr "', f'msgstr "{prefix}', 1)
                            lines[msgstr_line] = new_msgstr
                            modified = True
        i += 1
    
    if modified:
        # Créer une sauvegarde
        backup_file = po_file + '.fixed.bak'
        try:
            shutil.copy2(po_file, backup_file)
            print(f"  💾 Backup créé: {backup_file}")
        except Exception as e:
            print(f"  ⚠️ Impossible de créer la sauvegarde: {e}")
        
        # Écrire les modifications
        try:
            with open(po_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        except Exception as e:
            print(f"  ❌ Erreur écriture: {e}")
            return False
    
    print("  ✓ Aucune correction nécessaire")
    return False

def verify_specific_lines():
    """
    Vérifie et corrige les lignes spécifiques mentionnées dans les erreurs
    """
    corrections = {
        'translations/en/LC_MESSAGES/messages.po': {
            892: 'from_format'  # Ligne 892: ajouter %(from_format)s
        },
        'translations/es/LC_MESSAGES/messages.po': {
            894: 'from_format'  # Ligne 894: ajouter %(from_format)s
        },
        'translations/it/LC_MESSAGES/messages.po': {
            5625: 'developer_name'  # Ligne 5625: ajouter %(developer_name)s
        },
        'translations/nl/LC_MESSAGES/messages.po': {
            5633: 'developer_name'  # Ligne 5633: ajouter %(developer_name)s
        },
        'translations/ru/LC_MESSAGES/messages.po': {
            5627: 'developer_name'  # Ligne 5627: ajouter %(developer_name)s
        }
    }
    
    for po_file, lines in corrections.items():
        if os.path.exists(po_file):
            print(f"\n🔧 Correction spécifique pour {po_file}")
            
            try:
                with open(po_file, 'r', encoding='utf-8') as f:
                    lines_content = f.readlines()
            except Exception as e:
                print(f"  ❌ Erreur lecture: {e}")
                continue
            
            modified = False
            for line_num, placeholder in lines.items():
                # La ligne est 1-indexée dans l'erreur, mais Python est 0-indexé
                idx = line_num - 1
                
                if idx < len(lines_content) and lines_content[idx].startswith('msgstr "'):
                    placeholder_str = f'%({placeholder})s'
                    
                    if placeholder_str not in lines_content[idx]:
                        print(f"  ✅ Ajout de {placeholder_str} à la ligne {line_num}")
                        lines_content[idx] = lines_content[idx].replace('msgstr "', f'msgstr "{placeholder_str} ', 1)
                        modified = True
            
            if modified:
                backup = po_file + '.specific.bak'
                try:
                    shutil.copy2(po_file, backup)
                    print(f"  💾 Backup: {backup}")
                except:
                    pass
                
                try:
                    with open(po_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines_content)
                except Exception as e:
                    print(f"  ❌ Erreur écriture: {e}")

def main(force=False):
    translations_dir = 'translations'
    
    print("🔍 RECHERCHE ET CORRECTION DES PLACEHOLDERS")
    print("=" * 50)
    
    if not os.path.exists(translations_dir):
        print(f"❌ Dossier {translations_dir} non trouvé")
        return 1
    
    # Correction générale
    fixed_count = 0
    for lang in os.listdir(translations_dir):
        lang_path = os.path.join(translations_dir, lang)
        if not os.path.isdir(lang_path):
            continue
            
        po_file = os.path.join(lang_path, 'LC_MESSAGES', 'messages.po')
        if os.path.exists(po_file):
            if fix_placeholders_in_file(po_file, force):
                fixed_count += 1
    
    # Corrections spécifiques pour les lignes signalées
    verify_specific_lines()
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSUMÉ: {fixed_count} fichiers corrigés")
    print("\n🔄 Maintenant, recompilez avec:")
    print("   pybabel compile -d translations")
    
    return 0

if __name__ == "__main__":
    try:
        # Essaie en mode interactif (quand exécuté manuellement)
        response = input("⚠️  Ce script va modifier vos fichiers .po. Une sauvegarde sera créée. Continuer? (oui/non): ")
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            sys.exit(main())
        else:
            print("Annulé.")
            sys.exit(0)
    except EOFError:
        # En cas d'exécution dans Docker (pas de terminal), passe en mode forcé
        print("🚀 Mode automatique activé (exécution dans Docker)")
        sys.exit(main(force=True))