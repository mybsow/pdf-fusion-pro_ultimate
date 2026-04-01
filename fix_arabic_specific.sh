#!/bin/bash

echo "========================================="
echo "CORRECTION SPÉCIFIQUE DE L'ARABE"
echo "========================================="
echo ""

ARABIC_PO="translations/ar/LC_MESSAGES/messages.po"

# Liste des traductions italiennes trouvées dans l'arabe
declare -A FIXES=(
    ["Home"]="الرئيسية"
    ["Contatti"]="اتصل بنا"
    ["Chiudi"]="إغلاق"
    ["Unisci"]="دمج"
    ["Dividi"]="تقسيم"
    ["Ruota"]="تدوير"
    ["Comprimi"]="ضغط"
    ["Converti"]="تحويل"
    ["Versione"]="الإصدار"
    ["Privacy"]="الخصوصية"
    ["Termini"]="الشروط"
    ["Note legali"]="إشعارات قانونية"
    ["Avvertenza"]="تحذير"
    ["Formato Word"]="تنسيق Word"
    ["Formato PDF"]="تنسيق PDF"
    ["Estrazione OCR"]="استخراج OCR"
    ["Unisci PDF"]="دمج PDF"
    ["Dividi PDF"]="تقسيم PDF"
    ["Ruota PDF"]="تدوير PDF"
    ["Comprimi PDF"]="ضغط PDF"
    ["Proteggi PDF"]="حماية PDF"
    ["Sblocca PDF"]="إلغاء قفل PDF"
    ["Gratuito"]="مجاني"
    ["Sicuro"]="آمن"
    ["Veloce"]="سريع"
    ["Pagina non trovata"]="الصفحة غير موجودة"
    ["Errore interno del server"]="خطأ داخلي في الخادم"
    ["File too large"]="الملف كبير جداً"
)

echo "Corrections à appliquer:"
echo ""

for ITALIAN in "${!FIXES[@]}"; do
    ARABIC="${FIXES[$ITALIAN]}"
    
    # Vérifier si cette chaîne existe comme traduction
    if grep -q "msgstr \"$ITALIAN\"" "$ARABIC_PO"; then
        echo "  🔄 $ITALIAN -> $ARABIC"
        sed -i "s/msgstr \"$ITALIAN\"/msgstr \"$ARABIC\"/g" "$ARABIC_PO"
    fi
done

# Vérifier aussi les textes longs
echo ""
echo "Vérification des textes longs..."

# Textes PDF/A en italien dans l'arabe
ITALIAN_PDFA_TEXTS=(
    "PDF/A è una versione standardizzata del PDF progettata per l'archiviazione a lungo termine. Garantisce che il tuo documento sarà esattamente lo stesso tra 10, 20 o 50 anni, indipendentemente dal software utilizzato."
    "La conversione in PDF/A può modificare leggermente l'aspetto del documento per garantirne la longevità. Le funzionalità interattive (moduli, JavaScript) verranno rimosse."
)

for ITALIAN_TEXT in "${ITALIAN_PDFA_TEXTS[@]}"; do
    if grep -q "msgstr \"$ITALIAN_TEXT\"" "$ARABIC_PO"; then
        echo "  🔄 Texte PDF/A italien trouvé !"
        # Remplacer par la version arabe (à définir)
    fi
done

# Compiler
echo ""
echo "Compilation..."
msgfmt -o "translations/ar/LC_MESSAGES/messages.mo" "$ARABIC_PO"

if [ $? -eq 0 ]; then
    size=$(stat -c%s "translations/ar/LC_MESSAGES/messages.mo")
    echo "✅ Compilé avec succès ($size octets)"
else
    echo "❌ Erreur de compilation"
fi

echo ""
echo "========================================="
echo "✅ CORRECTIONS TERMINÉES"
echo "========================================="
