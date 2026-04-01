#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import shutil
from collections import OrderedDict

# Textes à traduire (version complète)
TEXTS = {
    "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.": {
        "fr": "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.",
        "en": "PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used.",
        "es": "PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado.",
        "de": "PDF/A ist eine standardisierte Version von PDF für die Langzeitarchivierung. Es stellt sicher, dass Ihr Dokument in 10, 20 oder 50 Jahren unabhängig von der verwendeten Software genau gleich aussieht.",
        "it": "PDF/A è una versione standardizzata del PDF progettata per l'archiviazione a lungo termine. Garantisce che il tuo documento sarà esattamente lo stesso tra 10, 20 o 50 anni, indipendentemente dal software utilizzato.",
        "pt": "PDF/A é uma versão padronizada do PDF projetada para arquivamento de longo prazo. Garante que seu documento terá exatamente a mesma aparência em 10, 20 ou 50 anos, independentemente do software usado.",
        "nl": "PDF/A is een gestandaardiseerde versie van PDF ontworpen voor langdurige archivering. Het garandeert dat uw document over 10, 20 of 50 jaar exact hetzelfde zal zijn, ongeacht de gebruikte software.",
        "zh": "PDF/A 是为长期存档而设计的标准化 PDF 版本。它确保您的文档在 10 年、20 年或 50 年后看起来完全相同，无论使用什么软件。",
        "ja": "PDF/Aは長期保存用に設計された標準化されたPDFバージョンです。使用するソフトウェアに関係なく、10年後、20年後、50年後もドキュメントが完全に同じであることを保証します。",
        "ru": "PDF/A — это стандартизированная версия PDF, предназначенная для долгосрочного архивирования. Она гарантирует, что ваш документ будет выглядеть точно так же через 10, 20 или 50 лет, независимо от используемого программного обеспечения.",
        "ar": "PDF/A هو إصدار موحد من PDF مصمم للأرشفة طويلة المدى. يضمن أن يكون مستندك مطابقًا تمامًا بعد 10 أو 20 أو 50 عامًا، بغض النظر عن البرامج المستخدمة.",
    },
    "La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées.": {
        "fr": "La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées.",
        "en": "Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed.",
        "es": "La conversión a PDF/A puede modificar ligeramente la apariencia del documento para garantizar su longevidad. Las características interactivas (formularios, JavaScript) se eliminarán.",
        "de": "Die Konvertierung in PDF/A kann das Erscheinungsbild des Dokuments leicht verändern, um die Langlebigkeit zu gewährleisten. Interaktive Funktionen (Formulare, JavaScript) werden entfernt.",
        "it": "La conversione in PDF/A può modificare leggermente l'aspetto del documento per garantirne la longevità. Le funzionalità interattive (moduli, JavaScript) verranno rimosse.",
        "pt": "A conversão para PDF/A pode alterar ligeiramente a aparência do documento para garantir sua longevidade. Recursos interativos (formulários, JavaScript) serão removidos.",
        "nl": "Conversie naar PDF/A kan het uiterlijk van het document enigszins wijzigen om de levensduur te garanderen. Interactieve functies (formulieren, JavaScript) worden verwijderd.",
        "zh": "转换为 PDF/A 可能会略微更改文档外观以确保其持久性。交互功能（表单、JavaScript）将被删除。",
        "ja": "PDF/Aへの変換により、長期的な保存を保証するためにドキュメントの外観が若干変更される場合があります。インタラクティブ機能（フォーム、JavaScript）は削除されます。",
        "ru": "Преобразование в PDF/A может незначительно изменить внешний вид документа для обеспечения долговечности. Интерактивные функции (формы, JavaScript) будут удалены.",
        "ar": "قد يؤدي التحويل إلى PDF/A إلى تغيير مظهر المستند قليلاً لضمان طول العمر. ستتم إزالة الميزات التفاعلية (النماذج، JavaScript).",
    },
    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.": {
        "fr": "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.",
        "en": "Compatible with all PDF readers. Animations and transitions are not preserved in the PDF.",
        "es": "Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF.",
        "de": "Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert.",
        "it": "Compatibile con tutti i lettori PDF. Le animazioni e le transizioni non vengono conservate nel PDF.",
        "pt": "Compatível com todos os leitores de PDF. Animações e transições não são preservadas no PDF.",
        "nl": "Compatibel met alle PDF-lezers. Animaties en overgangen worden niet bewaard in de PDF.",
        "zh": "兼容所有 PDF 阅读器。动画和过渡效果不会保留在 PDF 中。",
        "ja": "すべてのPDFリーダーと互換性があります。アニメーションとトランジションはPDFに保持されません。",
        "ru": "Совместим со всеми программами для чтения PDF. Анимации и переходы не сохраняются в PDF.",
        "ar": "متوافق مع جميع قارئات PDF. لا يتم الاحتفاظ بالرسوم المتحركة والانتقالات في PDF.",
    },
    "Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.": {
        "fr": "Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.",
        "en": "Compatible with all PDF readers. Fonts are embedded for faithful reproduction.",
        "es": "Compatible con todos los lectores PDF. Las fuentes están incrustadas para una reproducción fiel.",
        "de": "Kompatibel mit allen PDF-Readern. Schriftarten sind für eine originalgetreue Wiedergabe eingebettet.",
        "it": "Compatibile con tutti i lettori PDF. I caratteri sono incorporati per una riproduzione fedele.",
        "pt": "Compatível com todos os leitores de PDF. As fontes estão incorporadas para reprodução fiel.",
        "nl": "Compatibel met alle PDF-lezers. Lettertypen zijn ingebed voor getrouwe reproductie.",
        "zh": "兼容所有 PDF 阅读器。字体已嵌入以实现忠实再现。",
        "ja": "すべてのPDFリーダーと互換性があります。フォントは忠実な再現のために埋め込まれています。",
        "ru": "Совместим со всеми программами для чтения PDF. Шрифты встроены для точного воспроизведения.",
        "ar": "متوافق مع جميع قارئات PDF. الخطوط مضمنة لإعادة إنتاج دقيقة.",
    },
    "Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs.": {
        "fr": "Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs.",
        "en": "The generated file is in DOCX format, compatible with Microsoft Word 2007 and later versions, as well as LibreOffice and Google Docs.",
        "es": "El archivo generado está en formato DOCX, compatible con Microsoft Word 2007 y versiones posteriores, así como con LibreOffice y Google Docs.",
        "de": "Die generierte Datei ist im DOCX-Format, kompatibel mit Microsoft Word 2007 und neueren Versionen sowie mit LibreOffice und Google Docs.",
        "it": "Il file generato è in formato DOCX, compatibile con Microsoft Word 2007 e versioni successive, nonché con LibreOffice e Google Docs.",
        "pt": "O arquivo gerado está no formato DOCX, compatível com Microsoft Word 2007 e versões posteriores, bem como com LibreOffice e Google Docs.",
        "nl": "Het gegenereerde bestand is in DOCX-formaat, compatibel met Microsoft Word 2007 en latere versies, evenals met LibreOffice en Google Docs.",
        "zh": "生成的文件为 DOCX 格式，兼容 Microsoft Word 2007 及更高版本，以及 LibreOffice 和 Google Docs。",
        "ja": "生成されるファイルはDOCX形式で、Microsoft Word 2007以降、およびLibreOffice、Google Docsと互換性があります。",
        "ru": "Сгенерированный файл имеет формат DOCX, совместимый с Microsoft Word 2007 и более поздними версиями, а также с LibreOffice и Google Docs.",
        "ar": "الملف الذي تم إنشاؤه بتنسيق DOCX، متوافق مع Microsoft Word 2007 والإصدارات الأحدث، وكذلك مع LibreOffice وGoogle Docs.",
    },
    "Extraction OCR": {
        "fr": "Extraction OCR",
        "en": "OCR Extraction",
        "es": "Extracción OCR",
        "de": "OCR-Extraktion",
        "it": "Estrazione OCR",
        "pt": "Extração OCR",
        "nl": "OCR-extractie",
        "zh": "OCR 提取",
        "ja": "OCR抽出",
        "ru": "Извлечение OCR",
        "ar": "استخراج OCR",
    },
    "Format PDF": {
        "fr": "Format PDF",
        "en": "PDF Format",
        "es": "Formato PDF",
        "de": "PDF-Format",
        "it": "Formato PDF",
        "pt": "Formato PDF",
        "nl": "PDF-formaat",
        "zh": "PDF 格式",
        "ja": "PDF形式",
        "ru": "Формат PDF",
        "ar": "تنسيق PDF",
    },
    "Format Word": {
        "fr": "Format Word",
        "en": "Word Format",
        "es": "Formato Word",
        "de": "Word-Format",
        "it": "Formato Word",
        "pt": "Formato Word",
        "nl": "Word-formaat",
        "zh": "Word 格式",
        "ja": "Word形式",
        "ru": "Формат Word",
        "ar": "تنسيق Word",
    },
    "Attention": {
        "fr": "Attention",
        "en": "Warning",
        "es": "Advertencia",
        "de": "Warnung",
        "it": "Attenzione",
        "pt": "Aviso",
        "nl": "Waarschuwing",
        "zh": "警告",
        "ja": "警告",
        "ru": "Внимание",
        "ar": "تحذير",
    },
}

def clean_po_file(po_file):
    """Nettoie un fichier .po en supprimant les doublons"""
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Supprimer les doublons
    seen_msgids = set()
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        if line.startswith('msgid "'):
            msgid = line.strip()
            if msgid in seen_msgids:
                # Sauter cette entrée (msgid + msgstr + ligne vide)
                i += 1
                while i < len(lines) and not lines[i].startswith('msgid "'):
                    i += 1
                continue
            else:
                seen_msgids.add(msgid)
        cleaned_lines.append(line)
        i += 1
    
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    return True

def update_po_file(po_file, lang):
    """Met à jour un fichier .po avec les traductions"""
    if not os.path.exists(po_file):
        return False
    
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for text, translations in TEXTS.items():
        translation = translations.get(lang, text)
        
        # Chercher le msgid
        msgid_pattern = f'msgid "{text}"'
        if msgid_pattern in content:
            # Remplacer la traduction existante
            import re
            pattern = f'({re.escape(msgid_pattern)}\\n)msgstr ".*?"'
            new_content = re.sub(pattern, f'\\1msgstr "{translation}"', content, flags=re.DOTALL)
            if new_content != content:
                content = new_content
                modified = True
        else:
            # Ajouter le texte
            content += f'\n\nmsgid "{text}"\nmsgstr "{translation}"'
            modified = True
    
    if modified:
        with open(po_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return modified

def main():
    print("=" * 50)
    print("NETTOYAGE ET CORRECTION DES TRADUCTIONS")
    print("=" * 50)
    print()
    
    # 1. Sauvegarder
    if os.path.exists('translations_backup_clean'):
        shutil.rmtree('translations_backup_clean')
    shutil.copytree('translations', 'translations_backup_clean')
    print("✅ Sauvegarde créée dans translations_backup_clean")
    print()
    
    # 2. Nettoyer tous les fichiers .po
    print("1. Nettoyage des doublons...")
    for po_file in [f for f in os.listdir('translations') if os.path.isdir(f'translations/{f}')]:
        po_path = f'translations/{po_file}/LC_MESSAGES/messages.po'
        if os.path.exists(po_path):
            clean_po_file(po_path)
            print(f"   ✅ {po_file}")
    
    # 3. Mettre à jour les traductions
    print()
    print("2. Mise à jour des traductions...")
    for po_file in [f for f in os.listdir('translations') if os.path.isdir(f'translations/{f}')]:
        lang = po_file
        po_path = f'translations/{lang}/LC_MESSAGES/messages.po'
        if update_po_file(po_path, lang):
            print(f"   ✅ {lang}")
    
    # 4. Compiler
    print()
    print("3. Compilation des fichiers .mo...")
    for lang in os.listdir('translations'):
        po_path = f'translations/{lang}/LC_MESSAGES/messages.po'
        mo_path = f'translations/{lang}/LC_MESSAGES/messages.mo'
        if os.path.exists(po_path):
            result = subprocess.run(['msgfmt', '-o', mo_path, po_path], capture_output=True)
            if result.returncode == 0:
                print(f"   ✅ {lang}")
            else:
                print(f"   ❌ {lang}: {result.stderr.decode()[:80]}")
    
    # 5. Vérifier
    print()
    print("4. Vérification des traductions:")
    import gettext
    
    test_texts = list(TEXTS.keys())[:3]
    languages = ['fr', 'en', 'es', 'de']
    
    for lang in languages:
        print(f"\n{lang.upper()}:")
        try:
            trans = gettext.translation('messages', './translations', languages=[lang], fallback=True)
            _ = trans.gettext
            for text in test_texts:
                result = _(text)
                expected = TEXTS[text].get(lang, text)
                if result == expected:
                    print(f"  ✅ {text[:40]}...")
                else:
                    print(f"  ⚠️  {text[:40]}... -> {result[:40]}...")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print()
    print("=" * 50)
    print("✅ TERMINÉ !")
    print("=" * 50)

if __name__ == "__main__":
    main()
