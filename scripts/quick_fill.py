#!/usr/bin/env python3
# scripts/fix_all_missing_texts.py

import os
import re
import subprocess

# Traductions pour "Convertissez vos feuilles Excel en PDF"
EXCEL_TRANSLATIONS = {
    'fr': 'Convertissez vos feuilles Excel en PDF',
    'en': 'Convert your Excel sheets to PDF',
    'es': 'Convierta sus hojas de Excel a PDF',
    'de': 'Konvertieren Sie Ihre Excel-Tabellen in PDF',
    'it': 'Converti i tuoi fogli Excel in PDF',
    'pt': 'Converta suas planilhas Excel para PDF',
    'nl': 'Converteer uw Excel-bladen naar PDF',
    'ar': 'تحويل أوراق Excel الخاصة بك إلى PDF',
    'zh': '将您的Excel工作表转换为PDF',
    'ja': 'ExcelシートをPDFに変換',
    'ru': 'Конвертируйте листы Excel в PDF',
}

# Traductions pour "Notre système le convertit automatiquement en"
SYSTEM_TRANSLATIONS = {
    'fr': 'Notre système le convertit automatiquement en',
    'en': 'Our system automatically converts it to',
    'es': 'Nuestro sistema lo convierte automáticamente a',
    'de': 'Unser System konvertiert es automatisch in',
    'it': 'Il nostro sistema lo converte automaticamente in',
    'pt': 'Nosso sistema converte automaticamente para',
    'nl': 'Ons systeem converteert het automatisch naar',
    'ar': 'يقوم نظامنا بتحويله تلقائيا إلى',
    'zh': '我们的系统会自动将其转换为',
    'ja': '当社のシステムは自動的に変換します',
    'ru': 'Наша система автоматически конвертирует это в',
}

# Textes arabes spécifiques
ARABIC_FIXES = {
    r'\[À TRADUIRE: voir version française\]أدوات PDF المجانية عبر الإنترنت. تحويل، fusionnez، تقسيم وآخرون ضغط ملفات PDF الخاصة بك.': 'أدوات PDF مجانية عبر الإنترنت. قم بتحويل ودمج وتقسيم وضغط ملفات PDF الخاصة بك.',
    r'\[À TRADUIRE: voir version française\]ملفاتك تتميز بطريقة آمنة ومحذوفةالأتمتة.': 'تتم معالجة ملفاتك بشكل آمن ويتم حذفها تلقائيا.',
}

def fix_translations():
    """Corrige toutes les traductions manquantes"""
    
    for lang in EXCEL_TRANSLATIONS:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if not os.path.exists(po_file):
            continue
        
        print(f"📝 Correction de {lang}...")
        
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        
        # 1. Corriger la traduction Excel
        msgid = 'Convertissez vos feuilles Excel en PDF'
        if msgid in content:
            pattern = rf'(msgid "{msgid}"\n)msgstr "[^"]*"'
            replacement = rf'\1msgstr "{EXCEL_TRANSLATIONS[lang]}"'
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"  ✅ Excel: {EXCEL_TRANSLATIONS[lang]}")
        
        # 2. Corriger la traduction système
        msgid2 = 'Notre système le convertit automatiquement en'
        if msgid2 in content:
            pattern = rf'(msgid "{msgid2}"\n)msgstr "[^"]*"'
            replacement = rf'\1msgstr "{SYSTEM_TRANSLATIONS[lang]}"'
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"  ✅ Système: {SYSTEM_TRANSLATIONS[lang]}")
        
        # 3. Pour l'arabe, corrections spécifiques
        if lang == 'ar':
            for old, new in ARABIC_FIXES.items():
                if old in content:
                    content = content.replace(old, new)
                    modified = True
                    print(f"  ✅ Texte arabe corrigé")
        
        # 4. Supprimer tous les marqueurs "[À TRADUIRE" restants
        content = re.sub(r'\[À TRADUIRE[^\]]*\]', '', content)
        
        if modified:
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print()
    
    print("📦 Recompilation...")
    subprocess.run(['pybabel', 'compile', '-d', 'translations', '-f'])
    
    print()
    print("✨ Terminé!")

if __name__ == "__main__":
    fix_translations()