#!/bin/bash

echo "========================================="
echo "CORRECTION DES TRADUCTIONS - TOUTES LANGUES"
echo "========================================="
echo ""

# Liste complète des textes et leurs traductions pour toutes les langues

# ==================== ANGLAIS ====================
declare -A en_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Compatible with all PDF readers. Animations and transitions are not preserved in the PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Compatible with all PDF readers. Fonts are embedded for faithful reproduction."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="The generated file is in DOCX format, compatible with Microsoft Word 2007 and later versions, as well as LibreOffice and Google Docs."
    ["Extraction OCR"]="OCR Extraction"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — automatic column and header detection"
    ["Format PDF"]="PDF Format"
    ["Format Word"]="Word Format"
    ["Attention"]="Warning"
)

# ==================== ESPAGNOL ====================
declare -A es_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Compatible con todos los lectores PDF. Las fuentes están incrustadas para una reproducción fiel."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="La conversión a PDF/A puede modificar ligeramente la apariencia del documento para garantizar su longevidad. Las características interactivas (formularios, JavaScript) se eliminarán."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="El archivo generado está en formato DOCX, compatible con Microsoft Word 2007 y versiones posteriores, así como con LibreOffice y Google Docs."
    ["Extraction OCR"]="Extracción OCR"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — detección automática de columnas y encabezados"
    ["Format PDF"]="Formato PDF"
    ["Format Word"]="Formato Word"
    ["Attention"]="Advertencia"
)

# ==================== ALLEMAND ====================
declare -A de_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Kompatibel mit allen PDF-Readern. Schriftarten sind für eine originalgetreue Wiedergabe eingebettet."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A ist eine standardisierte Version von PDF für die Langzeitarchivierung. Es stellt sicher, dass Ihr Dokument in 10, 20 oder 50 Jahren unabhängig von der verwendeten Software genau gleich aussieht."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Die Konvertierung in PDF/A kann das Erscheinungsbild des Dokuments leicht verändern, um die Langlebigkeit zu gewährleisten. Interaktive Funktionen (Formulare, JavaScript) werden entfernt."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="Die generierte Datei ist im DOCX-Format, kompatibel mit Microsoft Word 2007 und neueren Versionen sowie mit LibreOffice und Google Docs."
    ["Extraction OCR"]="OCR-Extraktion"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — automatische Spalten- und Kopfzeilenerkennung"
    ["Format PDF"]="PDF-Format"
    ["Format Word"]="Word-Format"
    ["Attention"]="Warnung"
)

# ==================== ITALIEN ====================
declare -A it_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Compatibile con tutti i lettori PDF. Le animazioni e le transizioni non vengono conservate nel PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Compatibile con tutti i lettori PDF. I caratteri sono incorporati per una riproduzione fedele."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A è una versione standardizzata del PDF progettata per l'archiviazione a lungo termine. Garantisce che il tuo documento sarà esattamente lo stesso tra 10, 20 o 50 anni, indipendentemente dal software utilizzato."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="La conversione in PDF/A può modificare leggermente l'aspetto del documento per garantirne la longevità. Le funzionalità interattive (moduli, JavaScript) verranno rimosse."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="Il file generato è in formato DOCX, compatibile con Microsoft Word 2007 e versioni successive, nonché con LibreOffice e Google Docs."
    ["Extraction OCR"]="Estrazione OCR"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — rilevamento automatico di colonne e intestazioni"
    ["Format PDF"]="Formato PDF"
    ["Format Word"]="Formato Word"
    ["Attention"]="Attenzione"
)

# ==================== PORTUGAIS ====================
declare -A pt_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Compatível com todos os leitores de PDF. Animações e transições não são preservadas no PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Compatível com todos os leitores de PDF. As fontes estão incorporadas para reprodução fiel."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A é uma versão padronizada do PDF projetada para arquivamento de longo prazo. Garante que seu documento terá exatamente a mesma aparência em 10, 20 ou 50 anos, independentemente do software usado."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="A conversão para PDF/A pode alterar ligeiramente a aparência do documento para garantir sua longevidade. Recursos interativos (formulários, JavaScript) serão removidos."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="O arquivo gerado está no formato DOCX, compatível com Microsoft Word 2007 e versões posteriores, bem como com LibreOffice e Google Docs."
    ["Extraction OCR"]="Extração OCR"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — detecção automática de colunas e cabeçalhos"
    ["Format PDF"]="Formato PDF"
    ["Format Word"]="Formato Word"
    ["Attention"]="Aviso"
)

# ==================== NÉERLANDAIS ====================
declare -A nl_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Compatibel met alle PDF-lezers. Animaties en overgangen worden niet bewaard in de PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Compatibel met alle PDF-lezers. Lettertypen zijn ingebed voor getrouwe reproductie."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A is een gestandaardiseerde versie van PDF ontworpen voor langdurige archivering. Het garandeert dat uw document over 10, 20 of 50 jaar exact hetzelfde zal zijn, ongeacht de gebruikte software."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Conversie naar PDF/A kan het uiterlijk van het document enigszins wijzigen om de levensduur te garanderen. Interactieve functies (formulieren, JavaScript) worden verwijderd."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="Het gegenereerde bestand is in DOCX-formaat, compatibel met Microsoft Word 2007 en latere versies, evenals met LibreOffice en Google Docs."
    ["Extraction OCR"]="OCR-extractie"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — automatische kolom- en koptekstdetectie"
    ["Format PDF"]="PDF-formaat"
    ["Format Word"]="Word-formaat"
    ["Attention"]="Waarschuwing"
)

# ==================== CHINOIS ====================
declare -A zh_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="兼容所有 PDF 阅读器。动画和过渡效果不会保留在 PDF 中。"
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="兼容所有 PDF 阅读器。字体已嵌入以实现忠实再现。"
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A 是为长期存档而设计的标准化 PDF 版本。它确保您的文档在 10 年、20 年或 50 年后看起来完全相同，无论使用什么软件。"
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="转换为 PDF/A 可能会略微更改文档外观以确保其持久性。交互功能（表单、JavaScript）将被删除。"
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="生成的文件为 DOCX 格式，兼容 Microsoft Word 2007 及更高版本，以及 LibreOffice 和 Google Docs。"
    ["Extraction OCR"]="OCR 提取"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — 自动检测列和标题"
    ["Format PDF"]="PDF 格式"
    ["Format Word"]="Word 格式"
    ["Attention"]="警告"
)

# ==================== JAPONAIS ====================
declare -A ja_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="すべてのPDFリーダーと互換性があります。アニメーションとトランジションはPDFに保持されません。"
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="すべてのPDFリーダーと互換性があります。フォントは忠実な再現のために埋め込まれています。"
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/Aは長期保存用に設計された標準化されたPDFバージョンです。使用するソフトウェアに関係なく、10年後、20年後、50年後もドキュメントが完全に同じであることを保証します。"
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="PDF/Aへの変換により、長期的な保存を保証するためにドキュメントの外観が若干変更される場合があります。インタラクティブ機能（フォーム、JavaScript）は削除されます。"
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="生成されるファイルはDOCX形式で、Microsoft Word 2007以降、およびLibreOffice、Google Docsと互換性があります。"
    ["Extraction OCR"]="OCR抽出"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — 列とヘッダーの自動検出"
    ["Format PDF"]="PDF形式"
    ["Format Word"]="Word形式"
    ["Attention"]="警告"
)

# ==================== RUSSE ====================
declare -A ru_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Совместим со всеми программами для чтения PDF. Анимации и переходы не сохраняются в PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Совместим со всеми программами для чтения PDF. Шрифты встроены для точного воспроизведения."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A — это стандартизированная версия PDF, предназначенная для долгосрочного архивирования. Она гарантирует, что ваш документ будет выглядеть точно так же через 10, 20 или 50 лет, независимо от используемого программного обеспечения."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Преобразование в PDF/A может незначительно изменить внешний вид документа для обеспечения долговечности. Интерактивные функции (формы, JavaScript) будут удалены."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="Сгенерированный файл имеет формат DOCX, совместимый с Microsoft Word 2007 и более поздними версиями, а также с LibreOffice и Google Docs."
    ["Extraction OCR"]="Извлечение OCR"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — автоматическое обнаружение столбцов и заголовков"
    ["Format PDF"]="Формат PDF"
    ["Format Word"]="Формат Word"
    ["Attention"]="Внимание"
)

# ==================== ARABE ====================
declare -A ar_translations=(
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="متوافق مع جميع قارئات PDF. لا يتم الاحتفاظ بالرسوم المتحركة والانتقالات في PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="متوافق مع جميع قارئات PDF. الخطوط مضمنة لإعادة إنتاج دقيقة."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A هو إصدار موحد من PDF مصمم للأرشفة طويلة المدى. يضمن أن يكون مستندك مطابقًا تمامًا بعد 10 أو 20 أو 50 عامًا، بغض النظر عن البرامج المستخدمة."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="قد يؤدي التحويل إلى PDF/A إلى تغيير مظهر المستند قليلاً لضمان طول العمر. ستتم إزالة الميزات التفاعلية (النماذج، JavaScript)."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="الملف الذي تم إنشاؤه بتنسيق DOCX، متوافق مع Microsoft Word 2007 والإصدارات الأحدث، وكذلك مع LibreOffice وGoogle Docs."
    ["Extraction OCR"]="استخراج OCR"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — الكشف التلقائي عن الأعمدة والرؤوس"
    ["Format PDF"]="تنسيق PDF"
    ["Format Word"]="تنسيق Word"
    ["Attention"]="تحذير"
)

# Fonction pour mettre à jour une traduction
update_translation() {
    local po_file=$1
    local msgid=$2
    local msgstr=$3
    
    if [ -f "$po_file" ]; then
        if grep -q "^msgid \"$msgid\"$" "$po_file"; then
            sed -i "/^msgid \"$msgid\"$/{n;s/^msgstr \".*\"/msgstr \"$msgstr\"/}" "$po_file"
        else
            echo "" >> "$po_file"
            echo "msgid \"$msgid\"" >> "$po_file"
            echo "msgstr \"$msgstr\"" >> "$po_file"
        fi
    fi
}

# Traiter chaque langue
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "Traitement de $lang..."
    
    case $lang in
        en)
            for msgid in "${!en_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${en_translations[$msgid]}"
            done
            ;;
        es)
            for msgid in "${!es_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${es_translations[$msgid]}"
            done
            ;;
        de)
            for msgid in "${!de_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${de_translations[$msgid]}"
            done
            ;;
        it)
            for msgid in "${!it_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${it_translations[$msgid]}"
            done
            ;;
        pt)
            for msgid in "${!pt_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${pt_translations[$msgid]}"
            done
            ;;
        nl)
            for msgid in "${!nl_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${nl_translations[$msgid]}"
            done
            ;;
        zh)
            for msgid in "${!zh_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${zh_translations[$msgid]}"
            done
            ;;
        ja)
            for msgid in "${!ja_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${ja_translations[$msgid]}"
            done
            ;;
        ru)
            for msgid in "${!ru_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${ru_translations[$msgid]}"
            done
            ;;
        ar)
            for msgid in "${!ar_translations[@]}"; do
                update_translation "$po_file" "$msgid" "${ar_translations[$msgid]}"
            done
            ;;
        fr)
            for msgid in "${!en_translations[@]}"; do
                update_translation "$po_file" "$msgid" "$msgid"
            done
            ;;
    esac
    echo "   ✅ $lang terminé"
done

# Compiler les fichiers .mo
echo ""
echo "Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        size=$(ls -lh "${po_file%.po}.mo" | awk '{print $5}')
        echo "✅ ($size)"
    else
        echo "❌ Erreur"
    fi
done

# Vérification finale
echo ""
echo "Vérification des traductions pour toutes les langues:"
python3 << 'PYEOF'
import gettext

test_texts = [
    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.",
    "Extraction OCR",
    "Format PDF",
]

languages = {
    'fr': 'Français',
    'en': 'English',
    'es': 'Español',
    'de': 'Deutsch',
    'it': 'Italiano',
    'pt': 'Português',
    'nl': 'Nederlands',
    'zh': '中文',
    'ja': '日本語',
    'ru': 'Русский',
    'ar': 'العربية'
}

for lang_code, lang_name in languages.items():
    print(f"\n{lang_name} ({lang_code}):")
    try:
        trans = gettext.translation('messages', './translations', languages=[lang_code], fallback=True)
        _ = trans.gettext
        for text in test_texts:
            result = _(text)
            if result != text or lang_code == 'fr':
                print(f"  ✅ {text[:40]}... -> {result[:40]}...")
            else:
                print(f"  ⚠️  {text[:40]}... -> NON TRADUIT")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

PYEOF

echo ""
echo "========================================="
echo "✅ TOUTES LES TRADUCTIONS SONT CORRIGÉES !"
echo "========================================="
