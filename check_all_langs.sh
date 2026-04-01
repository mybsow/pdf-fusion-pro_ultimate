#!/bin/bash

echo "========================================="
echo "VÉRIFICATION DES LANGUES"
echo "========================================="
echo ""

# Langues et leurs caractères spécifiques
declare -A LANG_CHARS=(
    ["fr"]="[àâäéèêëïîôöùûüÿç]"
    ["en"]="[a-zA-Z]"
    ["es"]="[áéíóúñü]"
    ["de"]="[äöüß]"
    ["it"]="[àèéìíîòóùú]"
    ["pt"]="[áâãàçéêíóôõú]"
    ["nl"]="[a-zA-Z]"
    ["zh"]="[\u4e00-\u9fff]"
    ["ja"]="[\u3040-\u309f\u30a0-\u30ff]"
    ["ru"]="[а-яА-Я]"
    ["ar"]="[اآببتثجحخدذرزسشصضطظعغفقكلمنهوي]"
)

# Textes de test
TEST_MSGIDS=(
    "Accueil"
    "Contact"
    "Fermer"
    "Format PDF"
    "Extraction OCR"
)

for lang in fr en es de it pt nl zh ja ru ar; do
    po_file="translations/$lang/LC_MESSAGES/messages.po"
    if [ -f "$po_file" ]; then
        echo "📁 $lang:"
        
        for msgid in "${TEST_MSGIDS[@]}"; do
            # Récupérer la traduction
            translation=$(grep -A1 "^msgid \"$msgid\"$" "$po_file" 2>/dev/null | grep "^msgstr" | sed 's/msgstr "\(.*\)"/\1/')
            
            if [ -n "$translation" ]; then
                # Vérifier si c'est de l'arabe (pour les langues non-arabes)
                if [[ "$lang" != "ar" && "$translation" =~ [اآببتثجحخدذرزسشصضطظعغفقكلمنهوي] ]]; then
                    echo "  ⚠️  $msgid -> \"$translation\" (contient des caractères arabes !)"
                # Vérifier si c'est du français (pour les langues non-françaises)
                elif [[ "$lang" != "fr" && "$translation" =~ [àâäéèêëïîôöùûüÿç] ]]; then
                    echo "  ⚠️  $msgid -> \"$translation\" (contient des caractères français !)"
                # Vérifier si c'est de l'italien (pour les langues non-italiennes)
                elif [[ "$lang" != "it" && "$translation" =~ [àèéìíîòóùú] ]]; then
                    echo "  ⚠️  $msgid -> \"$translation\" (contient des caractères italiens !)"
                else
                    echo "  ✅ $msgid -> \"$translation\""
                fi
            else
                echo "  ❌ $msgid -> NON TROUVÉ"
            fi
        done
        echo ""
    fi
done
