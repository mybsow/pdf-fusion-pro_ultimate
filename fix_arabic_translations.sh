#!/bin/bash

echo "========================================="
echo "CORRECTION DES TRADUCTIONS ARABES"
echo "========================================="
echo ""

ARABIC_PO="translations/ar/LC_MESSAGES/messages.po"

# Sauvegarder
cp "$ARABIC_PO" "$ARABIC_PO.backup"
echo "✅ Sauvegarde créée: $ARABIC_PO.backup"

echo ""
echo "Recherche des traductions italiennes dans le fichier arabe..."

# Liste des mots/phrases italiennes à remplacer
declare -A ITALIAN_TO_ARABIC=(
    # Mots courants
    ["Home"]="الرئيسية"
    ["Contatti"]="اتصل بنا"
    ["Chiudi"]="إغلاق"
    ["Chiudi"]="حول"
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
    
    # Textes plus longs
    ["Unisci PDF"]="دمج PDF"
    ["Dividi PDF"]="تقسيم PDF"
    ["Ruota PDF"]="تدوير PDF"
    ["Comprimi PDF"]="ضغط PDF"
    ["Proteggi PDF"]="حماية PDF"
    ["Sblocca PDF"]="إلغاء قفل PDF"
    ["Convertitore universale"]="محول شامل"
    
    # Phrases
    ["PDF Fusion Pro"]="PDF Fusion Pro"
    ["Gratuito"]="مجاني"
    ["Sicuro"]="آمن"
    ["Veloce"]="سريع"
    ["Pagina non trovata"]="الصفحة غير موجودة"
    ["Errore interno del server"]="خطأ داخلي في الخادم"
    ["File too large"]="الملف كبير جداً"
)

# Compter les corrections
count=0

# Appliquer les corrections
for ITALIAN in "${!ITALIAN_TO_ARABIC[@]}"; do
    ARABIC="${ITALIAN_TO_ARABIC[$ITALIAN]}"
    
    # Vérifier si cette traduction italienne existe dans le fichier arabe
    if grep -q "msgstr \"$ITALIAN\"" "$ARABIC_PO"; then
        echo "  🔄 Remplacer: '$ITALIAN' -> '$ARABIC'"
        sed -i "s/msgstr \"$ITALIAN\"/msgstr \"$ARABIC\"/g" "$ARABIC_PO"
        ((count++))
    fi
done

echo ""
echo "✅ $count corrections effectuées"

# Vérifier s'il reste des caractères italiens (lettres accentuées)
echo ""
echo "Recherche des caractères italiens restants..."
grep "^msgstr" "$ARABIC_PO" | grep -E "[àáâãäåæçèéêëìíîïðòóôõöøùúûüýÿ]" | while read line; do
    echo "  ⚠️  Possible italien: $line"
done

# Compiler
echo ""
echo "Compilation du fichier arabe..."
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
