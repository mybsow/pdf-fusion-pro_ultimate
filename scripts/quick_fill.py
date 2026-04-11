#!/usr/bin/env python3
# scripts/regenerate_english_simple.py

"""
Version simplifiée - utilise des règles de base pour la traduction
(à compléter manuellement pour les cas spécifiques)
"""

import os
import re
import subprocess

# Dictionnaire de traductions manuelles
MANUAL_TRANSLATIONS = {
    # Textes courants
    "Convertir un autre fichier": "Convert another file",
    "Veuillez sélectionner un fichier ou coller du code HTML": "Please select a file or paste HTML code",
    "Téléchargez votre image ou PDF": "Download your image or PDF",
    "Convertissez vos feuilles Excel en PDF": "Convert your Excel sheets to PDF",
    "Notre système le convertit automatiquement en": "Our system automatically converts it to",
    
    # Navigation
    "Accueil": "Home",
    "Contact": "Contact",
    "À propos": "About",
    "Connexion": "Login",
    "Déconnexion": "Logout",
    
    # Actions
    "Envoyer": "Send",
    "Recevoir": "Receive",
    "Télécharger": "Download",
    "Téléverser": "Upload",
    "Rechercher": "Search",
    "Enregistrer": "Save",
    "Supprimer": "Delete",
    "Modifier": "Edit",
    "Annuler": "Cancel",
    "Valider": "Validate",
    "Fermer": "Close",
    "Ouvrir": "Open",
    "Aide": "Help",
    
    # Paramètres
    "Paramètres": "Settings",
    "Profil": "Profile",
    
    # PDF Tools
    "Fusionner PDF": "Merge PDF",
    "Diviser PDF": "Split PDF",
    "Compresser PDF": "Compress PDF",
    "Tourner PDF": "Rotate PDF",
    "Protéger PDF": "Protect PDF",
    "Déverrouiller PDF": "Unlock PDF",
    "Éditer PDF": "Edit PDF",
    "Signer PDF": "Sign PDF",
    
    # Conversions
    "Word vers PDF": "Word to PDF",
    "Excel vers PDF": "Excel to PDF",
    "PowerPoint vers PDF": "PowerPoint to PDF",
    "Image vers PDF": "Image to PDF",
    "PDF vers Word": "PDF to Word",
    "PDF vers Excel": "PDF to Excel",
    "PDF vers Image": "PDF to Image",
}

FR_FILE = "translations/fr/LC_MESSAGES/messages.po"
EN_FILE = "translations/en/LC_MESSAGES/messages.po"

def translate_text(text):
    """Traduit un texte en utilisant le dictionnaire manuel"""
    if not text:
        return text
    
    # Traduction directe
    if text in MANUAL_TRANSLATIONS:
        return MANUAL_TRANSLATIONS[text]
    
    # Règles simples
    # Mettre la première lettre en majuscule, le reste en minuscule
    # (à améliorer selon les besoins)
    return text

def main():
    print("🔄 Génération de l'anglais depuis le français (version simple)")
    print("=" * 60)
    
    if not os.path.exists(FR_FILE):
        print(f"❌ Fichier français non trouvé: {FR_FILE}")
        return
    
    # Sauvegarde
    if os.path.exists(EN_FILE):
        os.rename(EN_FILE, EN_FILE + ".backup")
        print("💾 Ancien fichier anglais sauvegardé")
    
    with open(FR_FILE, 'r', encoding='utf-8') as f:
        fr_lines = f.readlines()
    
    en_lines = []
    
    for line in fr_lines:
        if line.startswith('msgid "'):
            en_lines.append(line)
        elif line.startswith('msgstr "'):
            # Traduire le msgstr
            fr_text = line[8:-2]
            en_text = translate_text(fr_text)
            en_lines.append(f'msgstr "{en_text}"\n')
        else:
            en_lines.append(line)
    
    with open(EN_FILE, 'w', encoding='utf-8') as f:
        f.writelines(en_lines)
    
    print(f"✅ Fichier anglais généré: {EN_FILE}")
    
    # Recompiler
    subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'])
    print("✅ Compilation terminée")

if __name__ == "__main__":
    main()