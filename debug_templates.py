#!/usr/bin/env python3
import os

def check_templates():
    print("🔍 Vérification des templates...")
    
    # Chemins à vérifier
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, 'templates')
    conversion_templates_dir = os.path.join(templates_dir, 'conversion')
    
    print(f"📁 Dossier racine : {base_dir}")
    print(f"📁 Dossier templates : {templates_dir}")
    print(f"📁 Dossier conversion : {conversion_templates_dir}")
    
    # Vérifier l'existence des dossiers
    print(f"\n✅ Dossier templates existe : {os.path.exists(templates_dir)}")
    print(f"✅ Dossier conversion existe : {os.path.exists(conversion_templates_dir)}")
    
    # Templates à vérifier
    templates_to_check = [
        'image_to_word.html',
        'image_to_excel.html',
        'pdf_to_word.html',
        'pdf_to_excel.html'
    ]
    
    print("\n📄 Vérification des fichiers :")
    for template in templates_to_check:
        file_path = os.path.join(conversion_templates_dir, template)
        exists = os.path.exists(file_path)
        print(f"  {template}: {'✅' if exists else '❌'} - {file_path}")
    
    # Lister tous les fichiers HTML dans conversion
    if os.path.exists(conversion_templates_dir):
        print("\n📋 Tous les templates disponibles :")
        for file in sorted(os.listdir(conversion_templates_dir)):
            if file.endswith('.html'):
                print(f"  - {file}")

if __name__ == "__main__":
    check_templates()