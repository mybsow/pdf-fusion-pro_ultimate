#!/bin/bash

echo "========================================="
echo "CORRECTION DES TRADUCTIONS PDF/A"
echo "========================================="
echo ""

# Textes à traduire
TEXT1="Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."
TEXT2="La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."

# ==================== TRADUCTIONS ANGLAISES ====================
EN_TEXT1="PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used."
EN_TEXT2="Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed."

# ==================== TRADUCTIONS ESPAGNOLES ====================
ES_TEXT1="PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado."
ES_TEXT2="La conversión a PDF/A puede modificar ligeramente la apariencia del documento para garantizar su longevidad. Las características interactivas (formularios, JavaScript) se eliminarán."

# ==================== TRADUCTIONS ALLEMANDES ====================
DE_TEXT1="PDF/A ist eine standardisierte Version von PDF für die Langzeitarchivierung. Es stellt sicher, dass Ihr Dokument in 10, 20 oder 50 Jahren unabhängig von der verwendeten Software genau gleich aussieht."
DE_TEXT2="Die Konvertierung in PDF/A kann das Erscheinungsbild des Dokuments leicht verändern, um die Langlebigkeit zu gewährleisten. Interaktive Funktionen (Formulare, JavaScript) werden entfernt."

# ==================== TRADUCTIONS ITALIENNES ====================
IT_TEXT1="PDF/A è una versione standardizzata del PDF progettata per l'archiviazione a lungo termine. Garantisce che il tuo documento sarà esattamente lo stesso tra 10, 20 o 50 anni, indipendentemente dal software utilizzato."
IT_TEXT2="La conversione in PDF/A può modificare leggermente l'aspetto del documento per garantirne la longevità. Le funzionalità interattive (moduli, JavaScript) verranno rimosse."

# ==================== TRADUCTIONS PORTUGAISES ====================
PT_TEXT1="PDF/A é uma versão padronizada do PDF projetada para arquivamento de longo prazo. Garante que seu documento terá exatamente a mesma aparência em 10, 20 ou 50 anos, independentemente do software usado."
PT_TEXT2="A conversão para PDF/A pode alterar ligeiramente a aparência do documento para garantir sua longevidade. Recursos interativos (formulários, JavaScript) serão removidos."

# ==================== TRADUCTIONS NÉERLANDAISES ====================
NL_TEXT1="PDF/A is een gestandaardiseerde versie van PDF ontworpen voor langdurige archivering. Het garandeert dat uw document over 10, 20 of 50 jaar exact hetzelfde zal zijn, ongeacht de gebruikte software."
NL_TEXT2="Conversie naar PDF/A kan het uiterlijk van het document enigszins wijzigen om de levensduur te garanderen. Interactieve functies (formulieren, JavaScript) worden verwijderd."

# ==================== TRADUCTIONS CHINOISES ====================
ZH_TEXT1="PDF/A 是为长期存档而设计的标准化 PDF 版本。它确保您的文档在 10 年、20 年或 50 年后看起来完全相同，无论使用什么软件。"
ZH_TEXT2="转换为 PDF/A 可能会略微更改文档外观以确保其持久性。交互功能（表单、JavaScript）将被删除。"

# ==================== TRADUCTIONS JAPONAISES ====================
JA_TEXT1="PDF/Aは長期保存用に設計された標準化されたPDFバージョンです。使用するソフトウェアに関係なく、10年後、20年後、50年後もドキュメントが完全に同じであることを保証します。"
JA_TEXT2="PDF/Aへの変換により、長期的な保存を保証するためにドキュメントの外観が若干変更される場合があります。インタラクティブ機能（フォーム、JavaScript）は削除されます。"

# ==================== TRADUCTIONS RUSSES ====================
RU_TEXT1="PDF/A — это стандартизированная версия PDF, предназначенная для долгосрочного архивирования. Она гарантирует, что ваш документ будет выглядеть точно так же через 10, 20 или 50 лет, независимо от используемого программного обеспечения."
RU_TEXT2="Преобразование в PDF/A может незначительно изменить внешний вид документа для обеспечения долговечности. Интерактивные функции (формы, JavaScript) будут удалены."

# ==================== TRADUCTIONS ARABES ====================
AR_TEXT1="PDF/A هو إصدار موحد من PDF مصمم للأرشفة طويلة المدى. يضمن أن يكون مستندك مطابقًا تمامًا بعد 10 أو 20 أو 50 عامًا، بغض النظر عن البرامج المستخدمة."
AR_TEXT2="قد يؤدي التحويل إلى PDF/A إلى تغيير مظهر المستند قليلاً لضمان طول العمر. ستتم إزالة الميزات التفاعلية (النماذج، JavaScript)."

# Fonction pour mettre à jour la traduction
update_translation() {
    local po_file=$1
    local msgid=$2
    local msgstr=$3
    
    if [ -f "$po_file" ]; then
        if grep -q "^msgid \"$msgid\"$" "$po_file"; then
            # Mettre à jour la traduction existante
            sed -i "/^msgid \"$msgid\"$/{n;s/^msgstr \".*\"/msgstr \"$msgstr\"/}" "$po_file"
            echo "      ✅ Mis à jour"
        else
            # Ajouter le texte s'il n'existe pas
            echo "" >> "$po_file"
            echo "msgid \"$msgid\"" >> "$po_file"
            echo "msgstr \"$msgstr\"" >> "$po_file"
            echo "      ➕ Ajouté"
        fi
    fi
}

# Traiter chaque langue
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "Traitement de $lang..."
    
    case $lang in
        fr)
            update_translation "$po_file" "$TEXT1" "$TEXT1"
            update_translation "$po_file" "$TEXT2" "$TEXT2"
            ;;
        en)
            update_translation "$po_file" "$TEXT1" "$EN_TEXT1"
            update_translation "$po_file" "$TEXT2" "$EN_TEXT2"
            ;;
        es)
            update_translation "$po_file" "$TEXT1" "$ES_TEXT1"
            update_translation "$po_file" "$TEXT2" "$ES_TEXT2"
            ;;
        de)
            update_translation "$po_file" "$TEXT1" "$DE_TEXT1"
            update_translation "$po_file" "$TEXT2" "$DE_TEXT2"
            ;;
        it)
            update_translation "$po_file" "$TEXT1" "$IT_TEXT1"
            update_translation "$po_file" "$TEXT2" "$IT_TEXT2"
            ;;
        pt)
            update_translation "$po_file" "$TEXT1" "$PT_TEXT1"
            update_translation "$po_file" "$TEXT2" "$PT_TEXT2"
            ;;
        nl)
            update_translation "$po_file" "$TEXT1" "$NL_TEXT1"
            update_translation "$po_file" "$TEXT2" "$NL_TEXT2"
            ;;
        zh)
            update_translation "$po_file" "$TEXT1" "$ZH_TEXT1"
            update_translation "$po_file" "$TEXT2" "$ZH_TEXT2"
            ;;
        ja)
            update_translation "$po_file" "$TEXT1" "$JA_TEXT1"
            update_translation "$po_file" "$TEXT2" "$JA_TEXT2"
            ;;
        ru)
            update_translation "$po_file" "$TEXT1" "$RU_TEXT1"
            update_translation "$po_file" "$TEXT2" "$RU_TEXT2"
            ;;
        ar)
            update_translation "$po_file" "$TEXT1" "$AR_TEXT1"
            update_translation "$po_file" "$TEXT2" "$AR_TEXT2"
            ;;
        *)
            echo "   Langue non reconnue: $lang"
            ;;
    esac
done

# Compiler les fichiers .mo
echo ""
echo "Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        echo "✅"
    else
        echo "❌"
    fi
done

# Vérification
echo ""
echo "Vérification des traductions PDF/A:"
python3 << 'PYEOF'
import gettext

test_texts = [
    "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.",
    "La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."
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
        for i, text in enumerate(test_texts, 1):
            result = _(text)
            if result != text or lang_code == 'fr':
                print(f"  ✅ Texte {i}: {result[:60]}...")
            else:
                print(f"  ⚠️  Texte {i}: NON TRADUIT")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

print("\n" + "="*50)
print("✅ Vérification terminée !")
PYEOF

echo ""
echo "========================================="
echo "✅ CORRECTIONS PDF/A TERMINÉES !"
echo "========================================="
