#!/bin/bash

echo "========================================="
echo "AJOUT DES TEXTES FOOTER ET EXTRACTION"
echo "========================================="
echo ""

# Textes à ajouter
FOOTER1="Outils PDF gratuits en ligne. Convertissez, fusionnez, divisez et compressez vos fichiers PDF."
FOOTER2="Vos fichiers sont traités de manière sécurisée et supprimés automatiquement."
EXTRACT_TITLE="Extraction intelligente :"
EXTRACT_DESC="Les tableaux seront automatiquement détectés et convertis en feuilles Excel. L'OCR permet de reconnaître le texte dans les documents scannés."

# ==================== TRADUCTIONS ====================
# Anglais
EN_FOOTER1="Free online PDF tools. Convert, merge, split and compress your PDF files."
EN_FOOTER2="Your files are processed securely and automatically deleted."
EN_EXTRACT_TITLE="Intelligent Extraction:"
EN_EXTRACT_DESC="Tables will be automatically detected and converted to Excel sheets. OCR recognizes text in scanned documents."

# Espagnol
ES_FOOTER1="Herramientas PDF gratuitas en línea. Convierta, fusione, divida y comprima sus archivos PDF."
ES_FOOTER2="Sus archivos se procesan de forma segura y se eliminan automáticamente."
ES_EXTRACT_TITLE="Extracción inteligente:"
ES_EXTRACT_DESC="Las tablas se detectarán automáticamente y se convertirán en hojas de Excel. El OCR reconoce el texto en documentos escaneados."

# Allemand
DE_FOOTER1="Kostenlose PDF-Tools online. Konvertieren, zusammenführen, teilen und komprimieren Sie Ihre PDF-Dateien."
DE_FOOTER2="Ihre Dateien werden sicher verarbeitet und automatisch gelöscht."
DE_EXTRACT_TITLE="Intelligente Extraktion:"
DE_EXTRACT_DESC="Tabellen werden automatisch erkannt und in Excel-Blätter konvertiert. Die OCR erkennt Text in gescannten Dokumenten."

# Portugais
PT_FOOTER1="Ferramentas PDF gratuitas online. Converta, mescle, divida e comprima seus arquivos PDF."
PT_FOOTER2="Seus arquivos são processados de forma segura e excluídos automaticamente."
PT_EXTRACT_TITLE="Extração inteligente:"
PT_EXTRACT_DESC="As tabelas serão detectadas automaticamente e convertidas em planilhas Excel. O OCR reconhece texto em documentos digitalizados."

# Italien
IT_FOOTER1="Strumenti PDF gratuiti online. Converti, unisci, dividi e comprimi i tuoi file PDF."
IT_FOOTER2="I tuoi file vengono elaborati in modo sicuro ed eliminati automaticamente."
IT_EXTRACT_TITLE="Estrazione intelligente:"
IT_EXTRACT_DESC="Le tabelle verranno rilevate automaticamente e convertite in fogli Excel. L'OCR riconosce il testo nei documenti scansionati."

# Néerlandais
NL_FOOTER1="Gratis online PDF-tools. Converteer, voeg samen, splits en comprimeer uw PDF-bestanden."
NL_FOOTER2="Uw bestanden worden veilig verwerkt en automatisch verwijderd."
NL_EXTRACT_TITLE="Intelligente extractie:"
NL_EXTRACT_DESC="Tabellen worden automatisch gedetecteerd en geconverteerd naar Excel-bladen. OCR herkent tekst in gescande documenten."

# Chinois
ZH_FOOTER1="免费在线 PDF 工具。转换、合并、拆分和压缩您的 PDF 文件。"
ZH_FOOTER2="您的文件经过安全处理并自动删除。"
ZH_EXTRACT_TITLE="智能提取："
ZH_EXTRACT_DESC="表格将被自动检测并转换为 Excel 工作表。OCR 可识别扫描文档中的文本。"

# Japonais
JA_FOOTER1="無料のオンラインPDFツール。PDFファイルの変換、結合、分割、圧縮ができます。"
JA_FOOTER2="お客様のファイルは安全に処理され、自動的に削除されます。"
JA_EXTRACT_TITLE="インテリジェント抽出："
JA_EXTRACT_DESC="表は自動的に検出され、Excelシートに変換されます。OCRはスキャンされたドキュメント内のテキストを認識します。"

# Russe
RU_FOOTER1="Бесплатные онлайн-инструменты PDF. Конвертируйте, объединяйте, разделяйте и сжимайте ваши PDF-файлы."
RU_FOOTER2="Ваши файлы обрабатываются безопасно и автоматически удаляются."
RU_EXTRACT_TITLE="Интеллектуальное извлечение:"
RU_EXTRACT_DESC="Таблицы будут автоматически обнаружены и преобразованы в листы Excel. OCR распознает текст в отсканированных документах."

# Arabe
AR_FOOTER1="أدوات PDF مجانية عبر الإنترنت. قم بتحويل ودمج وتقسيم وضغط ملفات PDF الخاصة بك."
AR_FOOTER2="تتم معالجة ملفاتك بشكل آمن وحذفها تلقائيًا."
AR_EXTRACT_TITLE="استخراج ذكي:"
AR_EXTRACT_DESC="سيتم اكتشاف الجداول تلقائيًا وتحويلها إلى أوراق Excel. يتعرف OCR على النص في المستندات الممسوحة ضوئيًا."

# Fonction pour ajouter une traduction
add_translation() {
    local po_file=$1
    local msgid=$2
    local msgstr=$3
    
    if [ -f "$po_file" ]; then
        if grep -q "^msgid \"$msgid\"$" "$po_file"; then
            # Mettre à jour la traduction existante
            sed -i "/^msgid \"$msgid\"$/{n;s/^msgstr \".*\"/msgstr \"$msgstr\"/}" "$po_file"
            echo "      🔄 Mis à jour: $(echo "$msgid" | cut -c1-50)..."
        else
            # Ajouter le texte
            echo "" >> "$po_file"
            echo "msgid \"$msgid\"" >> "$po_file"
            echo "msgstr \"$msgstr\"" >> "$po_file"
            echo "      ➕ Ajouté: $(echo "$msgid" | cut -c1-50)..."
        fi
    fi
}

# Traiter chaque langue
echo "1. Ajout des traductions..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "   $lang..."
    
    case $lang in
        fr)
            add_translation "$po_file" "$FOOTER1" "$FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$EXTRACT_DESC"
            ;;
        en)
            add_translation "$po_file" "$FOOTER1" "$EN_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$EN_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$EN_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$EN_EXTRACT_DESC"
            ;;
        es)
            add_translation "$po_file" "$FOOTER1" "$ES_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$ES_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$ES_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$ES_EXTRACT_DESC"
            ;;
        de)
            add_translation "$po_file" "$FOOTER1" "$DE_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$DE_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$DE_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$DE_EXTRACT_DESC"
            ;;
        pt)
            add_translation "$po_file" "$FOOTER1" "$PT_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$PT_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$PT_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$PT_EXTRACT_DESC"
            ;;
        it)
            add_translation "$po_file" "$FOOTER1" "$IT_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$IT_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$IT_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$IT_EXTRACT_DESC"
            ;;
        nl)
            add_translation "$po_file" "$FOOTER1" "$NL_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$NL_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$NL_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$NL_EXTRACT_DESC"
            ;;
        zh)
            add_translation "$po_file" "$FOOTER1" "$ZH_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$ZH_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$ZH_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$ZH_EXTRACT_DESC"
            ;;
        ja)
            add_translation "$po_file" "$FOOTER1" "$JA_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$JA_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$JA_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$JA_EXTRACT_DESC"
            ;;
        ru)
            add_translation "$po_file" "$FOOTER1" "$RU_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$RU_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$RU_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$RU_EXTRACT_DESC"
            ;;
        ar)
            add_translation "$po_file" "$FOOTER1" "$AR_FOOTER1"
            add_translation "$po_file" "$FOOTER2" "$AR_FOOTER2"
            add_translation "$po_file" "$EXTRACT_TITLE" "$AR_EXTRACT_TITLE"
            add_translation "$po_file" "$EXTRACT_DESC" "$AR_EXTRACT_DESC"
            ;;
        *)
            echo "      ⚠️ Langue non reconnue: $lang"
            ;;
    esac
done

echo ""
echo "2. Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        size=$(stat -c%s "${po_file%.po}.mo" 2>/dev/null || echo "0")
        echo "✅ ($size octets)"
    else
        echo "❌ Erreur"
    fi
done

echo ""
echo "3. Vérification des traductions ajoutées..."
python3 << 'PYEOF'
import gettext

test_texts = [
    "Outils PDF gratuits en ligne. Convertissez, fusionnez, divisez et compressez vos fichiers PDF.",
    "Vos fichiers sont traités de manière sécurisée et supprimés automatiquement.",
    "Extraction intelligente :",
    "Les tableaux seront automatiquement détectés et convertis en feuilles Excel. L'OCR permet de reconnaître le texte dans les documents scannés."
]

languages = ['fr', 'en', 'es', 'de', 'pt', 'it', 'nl', 'zh', 'ja', 'ru', 'ar']

print("\nTest des traductions ajoutées:")
for lang in languages:
    print(f"\n{lang.upper()}:")
    try:
        trans = gettext.translation('messages', './translations', languages=[lang], fallback=True)
        _ = trans.gettext
        for text in test_texts:
            result = _(text)
            if result != text or lang == 'fr':
                print(f"  ✅ {text[:40]}... -> {result[:40]}...")
            else:
                print(f"  ⚠️  {text[:40]}... -> PAS TRADUIT")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

PYEOF

echo ""
echo "========================================="
echo "✅ TEXTES AJOUTÉS AVEC SUCCÈS !"
echo "========================================="
