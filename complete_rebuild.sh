#!/bin/bash

echo "========================================="
echo "RECONSTRUCTION COMPLÈTE DES FICHIERS .PO"
echo "========================================="
echo ""

# Sauvegarder les fichiers existants
echo "1. Sauvegarde..."
mkdir -p translations_backup_final
cp -r translations translations_backup_final/
echo "   ✅ Sauvegarde créée dans translations_backup_final/"
echo ""

# Langues à reconstruire
LANGUAGES=("pt" "de" "ja" "ru" "ar" "es")

# Textes à traduire
TEXT1="Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."
TEXT2="La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."
TEXT3="Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."
TEXT4="Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."
TEXT5="Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."
TEXT6="Extraction OCR"
TEXT7="Format PDF"
TEXT8="Format Word"
TEXT9="Attention"

# Traductions pour chaque langue
cat > /tmp/translations.txt << 'TRANS'
pt|PDF/A é uma versão padronizada do PDF projetada para arquivamento de longo prazo. Garante que seu documento terá exatamente a mesma aparência em 10, 20 ou 50 anos, independentemente do software usado.
pt|A conversão para PDF/A pode alterar ligeiramente a aparência do documento para garantir sua longevidade. Recursos interativos (formulários, JavaScript) serão removidos.
pt|Compatível com todos os leitores de PDF. Animações e transições não são preservadas no PDF.
pt|Compatível com todos os leitores de PDF. As fontes estão incorporadas para reprodução fiel.
pt|O arquivo gerado está no formato DOCX, compatível com Microsoft Word 2007 e versões posteriores, bem como com LibreOffice e Google Docs.
pt|Extração OCR
pt|Formato PDF
pt|Formato Word
pt|Aviso
de|PDF/A ist eine standardisierte Version von PDF für die Langzeitarchivierung. Es stellt sicher, dass Ihr Dokument in 10, 20 oder 50 Jahren unabhängig von der verwendeten Software genau gleich aussieht.
de|Die Konvertierung in PDF/A kann das Erscheinungsbild des Dokuments leicht verändern, um die Langlebigkeit zu gewährleisten. Interaktive Funktionen (Formulare, JavaScript) werden entfernt.
de|Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert.
de|Kompatibel mit allen PDF-Readern. Schriftarten sind für eine originalgetreue Wiedergabe eingebettet.
de|Die generierte Datei ist im DOCX-Format, kompatibel mit Microsoft Word 2007 und neueren Versionen sowie mit LibreOffice und Google Docs.
de|OCR-Extraktion
de|PDF-Format
de|Word-Format
de|Warnung
es|PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado.
es|La conversión a PDF/A puede modificar ligeramente la apariencia del documento para garantizar su longevidad. Las características interactivas (formularios, JavaScript) se eliminarán.
es|Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF.
es|Compatible con todos los lectores PDF. Las fuentes están incrustadas para una reproducción fiel.
es|El archivo generado está en formato DOCX, compatible con Microsoft Word 2007 y versiones posteriores, así como con LibreOffice y Google Docs.
es|Extracción OCR
es|Formato PDF
es|Formato Word
es|Advertencia
ja|PDF/Aは長期保存用に設計された標準化されたPDFバージョンです。使用するソフトウェアに関係なく、10年後、20年後、50年後もドキュメントが完全に同じであることを保証します。
ja|PDF/Aへの変換により、長期的な保存を保証するためにドキュメントの外観が若干変更される場合があります。インタラクティブ機能（フォーム、JavaScript）は削除されます。
ja|すべてのPDFリーダーと互換性があります。アニメーションとトランジションはPDFに保持されません。
ja|すべてのPDFリーダーと互換性があります。フォントは忠実な再現のために埋め込まれています。
ja|生成されるファイルはDOCX形式で、Microsoft Word 2007以降、およびLibreOffice、Google Docsと互換性があります。
ja|OCR抽出
ja|PDF形式
ja|Word形式
ja|警告
ru|PDF/A — это стандартизированная версия PDF, предназначенная для долгосрочного архивирования. Она гарантирует, что ваш документ будет выглядеть точно так же через 10, 20 или 50 лет, независимо от используемого программного обеспечения.
ru|Преобразование в PDF/A может незначительно изменить внешний вид документа для обеспечения долговечности. Интерактивные функции (формы, JavaScript) будут удалены.
ru|Совместим со всеми программами для чтения PDF. Анимации и переходы не сохраняются в PDF.
ru|Совместим со всеми программами для чтения PDF. Шрифты встроены для точного воспроизведения.
ru|Сгенерированный файл имеет формат DOCX, совместимый с Microsoft Word 2007 и более поздними версиями, а также с LibreOffice и Google Docs.
ru|Извлечение OCR
ru|Формат PDF
ru|Формат Word
ru|Внимание
ar|PDF/A هو إصدار موحد من PDF مصمم للأرشفة طويلة المدى. يضمن أن يكون مستندك مطابقًا تمامًا بعد 10 أو 20 أو 50 عامًا، بغض النظر عن البرامج المستخدمة.
ar|قد يؤدي التحويل إلى PDF/A إلى تغيير مظهر المستند قليلاً لضمان طول العمر. ستتم إزالة الميزات التفاعلية (النماذج، JavaScript).
ar|متوافق مع جميع قارئات PDF. لا يتم الاحتفاظ بالرسوم المتحركة والانتقالات في PDF.
ar|متوافق مع جميع قارئات PDF. الخطوط مضمنة لإعادة إنتاج دقيقة.
ar|الملف الذي تم إنشاؤه بتنسيق DOCX، متوافق مع Microsoft Word 2007 والإصدارات الأحدث، وكذلك مع LibreOffice وGoogle Docs.
ar|استخراج OCR
ar|تنسيق PDF
ar|تنسيق Word
ar|تحذير
TRANS

# Fonction pour extraire la traduction
get_translation() {
    local lang=$1
    local num=$2
    grep "^$lang|" /tmp/translations.txt | sed -n "${num}p" | cut -d'|' -f2-
}

# Reconstruire chaque langue
echo "2. Reconstruction des fichiers .po..."
for lang in "${LANGUAGES[@]}"; do
    echo "   $lang..."
    
    po_file="translations/$lang/LC_MESSAGES/messages.po"
    mkdir -p "translations/$lang/LC_MESSAGES"
    
    # Créer le fichier .po
    cat > "$po_file" << HEADER
msgid ""
msgstr ""
"Project-Id-Version: PDF Fusion Pro\n"
"POT-Creation-Date: $(date +'%Y-%m-%d %H:%M%z')\n"
"PO-Revision-Date: $(date +'%Y-%m-%d %H:%M%z')\n"
"Language: $lang\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n > 1);\n"
"\n"

HEADER
    
    # Ajouter les textes
    for i in {1..9}; do
        text_var="TEXT$i"
        text="${!text_var}"
        translation=$(get_translation "$lang" "$i")
        
        echo "msgid \"$text\"" >> "$po_file"
        echo "msgstr \"$translation\"" >> "$po_file"
        echo "" >> "$po_file"
    done
    
    # Compiler
    msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "      ✅ Compilé"
    else
        echo "      ❌ Erreur"
    fi
done

# Vérifier
echo ""
echo "3. Vérification des traductions..."
python3 << 'PYEOF'
import gettext

test_texts = [
    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.",
    "Extraction OCR",
    "Format PDF",
]

langs = {
    'pt': 'Português',
    'de': 'Deutsch', 
    'es': 'Español',
    'ja': '日本語',
    'ru': 'Русский',
    'ar': 'العربية'
}

for lang_code, lang_name in langs.items():
    print(f"\n{lang_name} ({lang_code}):")
    try:
        trans = gettext.translation('messages', './translations', languages=[lang_code], fallback=True)
        _ = trans.gettext
        for text in test_texts:
            result = _(text)
            if result != text:
                print(f"  ✅ {text[:40]}... -> {result[:40]}...")
            else:
                print(f"  ⚠️  {text[:40]}... -> NON TRADUIT")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

PYEOF

echo ""
echo "========================================="
echo "✅ RECONSTRUCTION TERMINÉE"
echo "========================================="
echo ""
echo "Pour restaurer les fichiers originaux si nécessaire:"
echo "  rm -rf translations"
echo "  mv translations_backup_final translations"
