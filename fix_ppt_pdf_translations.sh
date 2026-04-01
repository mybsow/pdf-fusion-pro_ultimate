#!/bin/bash

echo "========================================="
echo "CORRECTION DES TRADUCTIONS PPT TO PDF"
echo "========================================="
echo ""

# Texte à corriger
TEXT="Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."

# Traductions correctes
EN_TRANS="Compatible with all PDF readers. Animations and transitions are not preserved in the PDF."
ES_TRANS="Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF."
DE_TRANS="Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert."
IT_TRANS="Compatibile con tutti i lettori PDF. Le animazioni e le transizioni non vengono conservate nel PDF."
PT_TRANS="Compatível com todos os leitores de PDF. Animações e transições não são preservadas no PDF."
NL_TRANS="Compatibel met alle PDF-lezers. Animaties en overgangen worden niet bewaard in de PDF."
ZH_TRANS="兼容所有PDF阅读器。动画和过渡效果不会保留在PDF中。"
JA_TRANS="すべてのPDFリーダーと互換性があります。アニメーションとトランジションはPDFに保持されません。"
RU_TRANS="Совместим со всеми программами для чтения PDF. Анимации и переходы не сохраняются в PDF."
AR_TRANS="متوافق مع جميع قارئات PDF. لا يتم الاحتفاظ بالرسوم المتحركة والانتقالات في PDF."

# Fonction pour mettre à jour la traduction
update_translation() {
    local po_file=$1
    local lang=$2
    local translation=$3
    
    if [ -f "$po_file" ]; then
        echo "  Mise à jour de $lang..."
        
        # Vérifier si le texte existe
        if grep -q "^msgid \"$TEXT\"$" "$po_file"; then
            # Mettre à jour la traduction
            sed -i "/^msgid \"$TEXT\"$/{n;s/^msgstr \".*\"/msgstr \"$translation\"/}" "$po_file"
            echo "    ✅ Traduction mise à jour"
        else
            # Ajouter le texte
            echo "" >> "$po_file"
            echo "msgid \"$TEXT\"" >> "$po_file"
            echo "msgstr \"$translation\"" >> "$po_file"
            echo "    ➕ Texte ajouté"
        fi
    fi
}

# Mettre à jour chaque langue
update_translation "translations/en/LC_MESSAGES/messages.po" "en" "$EN_TRANS"
update_translation "translations/es/LC_MESSAGES/messages.po" "es" "$ES_TRANS"
update_translation "translations/de/LC_MESSAGES/messages.po" "de" "$DE_TRANS"
update_translation "translations/it/LC_MESSAGES/messages.po" "it" "$IT_TRANS"
update_translation "translations/pt/LC_MESSAGES/messages.po" "pt" "$PT_TRANS"
update_translation "translations/nl/LC_MESSAGES/messages.po" "nl" "$NL_TRANS"
update_translation "translations/zh/LC_MESSAGES/messages.po" "zh" "$ZH_TRANS"
update_translation "translations/ja/LC_MESSAGES/messages.po" "ja" "$JA_TRANS"
update_translation "translations/ru/LC_MESSAGES/messages.po" "ru" "$RU_TRANS"
update_translation "translations/ar/LC_MESSAGES/messages.po" "ar" "$AR_TRANS"

echo ""
echo "Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null
    echo "  ✅ $lang"
done

echo ""
echo "========================================="
echo "✅ Traductions corrigées !"
echo "========================================="
echo ""
echo "Vérification :"
echo "  - Anglais: $EN_TRANS"
echo "  - Espagnol: $ES_TRANS"
echo "  - Allemand: $DE_TRANS"
