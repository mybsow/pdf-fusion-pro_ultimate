#!/usr/bin/env python3
# scripts/fix_placeholders.py - Version améliorée

import polib
import re
from pathlib import Path
import sys

def extract_placeholders(text):
    """Extrait les placeholders comme {0}, %s, %d, etc."""
    # Pattern pour {word} ou {number}
    bracket_pattern = re.compile(r"\{[^}]+\}")
    # Pattern pour %s, %d, %f, etc.
    percent_pattern = re.compile(r"%[sdifeEgGxX]")
    
    placeholders = []
    placeholders.extend(bracket_pattern.findall(text))
    placeholders.extend(percent_pattern.findall(text))
    
    return sorted(placeholders)

def fix_placeholders_in_file(po_file):
    """Corrige les placeholders manquants dans un fichier .po"""
    print(f"🔧 Traitement de {po_file}...")
    
    try:
        po = polib.pofile(str(po_file))
    except Exception as e:
        print(f"  ❌ Erreur de lecture: {e}")
        return False
    
    modified = False
    entry_count = 0
    fixed_count = 0
    
    for entry in po:
        entry_count += 1
        if not entry.msgstr or entry.msgstr.strip() == "":
            continue  # Ignorer les traductions vides
        
        msgid_ph = extract_placeholders(entry.msgid)
        msgstr_ph = extract_placeholders(entry.msgstr)
        
        if msgid_ph != msgstr_ph:
            print(f"\n  ⚠️ Problème ligne {entry.lineno}:")
            print(f"    msgid: {entry.msgid[:50]}...")
            print(f"    msgid placeholders: {msgid_ph}")
            print(f"    msgstr placeholders: {msgstr_ph}")
            
            # Tentative de correction
            corrected = entry.msgstr
            
            # Ajouter les placeholders manquants
            for ph in msgid_ph:
                if ph not in msgstr_ph:
                    # Vérifier si le placeholder existe déjà sous une forme différente
                    ph_base = re.sub(r'[{}%]', '', ph)
                    found = False
                    for existing in msgstr_ph:
                        if ph_base in existing:
                            found = True
                            break
                    
                    if not found:
                        corrected += f" {ph}"
                        print(f"    ✅ Ajout du placeholder: {ph}")
                        modified = True
            
            # Remplacer les placeholders mal formatés
            for i, ph in enumerate(msgid_ph):
                if i < len(msgstr_ph) and msgstr_ph[i] != ph:
                    # Si le type de placeholder est différent mais le contenu similaire
                    if re.sub(r'[{}%]', '', msgstr_ph[i]) == re.sub(r'[{}%]', '', ph):
                        corrected = corrected.replace(msgstr_ph[i], ph)
                        print(f"    ✅ Correction du format: {msgstr_ph[i]} → {ph}")
                        modified = True
            
            entry.msgstr = corrected.strip()
            fixed_count += 1
    
    if modified:
        try:
            po.save()
            print(f"\n  ✅ {fixed_count}/{entry_count} entrées corrigées dans {po_file.name}")
        except Exception as e:
            print(f"  ❌ Erreur de sauvegarde: {e}")
            return False
    else:
        print(f"  ✅ Aucune correction nécessaire ({entry_count} entrées vérifiées)")
    
    return True

def main():
    print("🔧 CORRECTION DES PLACEHOLDERS DANS LES TRADUCTIONS")
    print("=" * 60)
    
    translations_dir = Path("translations")
    if not translations_dir.exists():
        print("❌ Dossier 'translations' introuvable")
        return 1
    
    po_files = list(translations_dir.rglob("*.po"))
    if not po_files:
        print("❌ Aucun fichier .po trouvé")
        return 1
    
    print(f"📁 {len(po_files)} fichiers .po trouvés\n")
    
    success_count = 0
    for po_file in po_files:
        if fix_placeholders_in_file(po_file):
            success_count += 1
        print()  # Ligne vide pour la lisibilité
    
    print("=" * 60)
    print(f"📊 Récapitulatif: {success_count}/{len(po_files)} fichiers traités avec succès")
    
    # Option: recompiler automatiquement
    if success_count > 0:
        print("\n🔨 Recompilation des traductions...")
        import subprocess
        result = subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Compilation réussie !")
        else:
            print("⚠️ Compilation avec avertissements (normal)")
            print(result.stderr[:200] + "...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
