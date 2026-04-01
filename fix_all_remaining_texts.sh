#!/bin/bash

echo "========================================="
echo "FIX DES TEXTES RESTANTS"
echo "========================================="
echo ""

# 1. Corriger les deux-points dans les templates
echo "1. Correction des deux-points dans les templates..."
find templates/conversion -name "*.html" -exec sed -i \
    -e 's/{{ _('\''Format Word :'\'') }}/{{ _('\''Format Word'\'') }}:/g' \
    -e 's/{{ _('\''Format PDF :'\'') }}/{{ _('\''Format PDF'\'') }}:/g' \
    -e 's/{{ _('\''Attention :'\'') }}/{{ _('\''Attention'\'') }}:/g' \
    -e 's/<strong>{{ _('\''Format Word :'\'') }}<\/strong>/<strong>{{ _('\''Format Word'\'') }}:<\/strong>/g' \
    -e 's/<strong>{{ _('\''Format PDF :'\'') }}<\/strong>/<strong>{{ _('\''Format PDF'\'') }}:<\/strong>/g' \
    {} \;

echo "   ✅ Templates corrigés"

# 2. Ajouter les textes manquants aux fichiers .po
echo ""
echo "2. Ajout des textes aux fichiers .po..."

# Définir les textes à ajouter
declare -A texts_to_add=(
    ["Extraction OCR"]="OCR Extraction"
    ["Extraction OCR en cours"]="OCR Extraction in progress"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — automatic column and header detection"
    ["Format Word"]="Word Format"
    ["Format PDF"]="PDF Format"
    ["Attention"]="Warning"
    ["Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Compatible with all PDF readers. Animations and transitions are not preserved in the PDF."
    ["Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Compatible with all PDF readers. Fonts are embedded for faithful reproduction."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used."
    ["La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed."
    ["Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="The generated file is in DOCX format, compatible with Microsoft Word 2007 and later versions, as well as LibreOffice and Google Docs."
)

# Pour chaque langue
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "   $lang..."
    
    for text in "${!texts_to_add[@]}"; do
        # Vérifier si le texte existe déjà
        if ! grep -q "^msgid \"$text\"$" "$po_file"; then
            echo "" >> "$po_file"
            echo "msgid \"$text\"" >> "$po_file"
            
            case $lang in
                fr)
                    echo "msgstr \"$text\"" >> "$po_file"
                    ;;
                en)
                    echo "msgstr \"${texts_to_add[$text]}\"" >> "$po_file"
                    ;;
                es)
                    # Traductions espagnoles
                    case "$text" in
                        "Extraction OCR") echo "msgstr \"Extracción OCR\"" >> "$po_file" ;;
                        "Format Word") echo "msgstr \"Formato Word\"" >> "$po_file" ;;
                        "Format PDF") echo "msgstr \"Formato PDF\"" >> "$po_file" ;;
                        "Attention") echo "msgstr \"Advertencia\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") 
                            echo "msgstr \"Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF.\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.") 
                            echo "msgstr \"Compatible con todos los lectores PDF. Las fuentes están incrustadas para una reproducción fiel.\"" >> "$po_file" ;;
                        "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.") 
                            echo "msgstr \"PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado.\"" >> "$po_file" ;;
                        *) echo "msgstr \"$text\"" >> "$po_file" ;;
                    esac
                    ;;
                de)
                    # Traductions allemandes
                    case "$text" in
                        "Extraction OCR") echo "msgstr \"OCR-Extraktion\"" >> "$po_file" ;;
                        "Format Word") echo "msgstr \"Word-Format\"" >> "$po_file" ;;
                        "Format PDF") echo "msgstr \"PDF-Format\"" >> "$po_file" ;;
                        "Attention") echo "msgstr \"Warnung\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") 
                            echo "msgstr \"Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert.\"" >> "$po_file" ;;
                        *) echo "msgstr \"$text\"" >> "$po_file" ;;
                    esac
                    ;;
                *)
                    echo "msgstr \"$text\"" >> "$po_file"
                    ;;
            esac
        fi
    done
done

# 3. Compiler les fichiers .mo
echo ""
echo "3. Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        echo "✅"
    else
        echo "❌"
    fi
done

# 4. Vérification
echo ""
echo "4. Vérification des traductions..."
python3 << 'PYEOF'
import gettext

test_texts = [
    "Extraction OCR",
    "Format PDF",
    "Format Word",
    "Attention",
    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.",
]

print("\nTest des traductions:")
for lang in ['fr', 'en', 'es']:
    print(f"\n{lang.upper()}:")
    try:
        trans = gettext.translation('messages', './translations', languages=[lang], fallback=True)
        _ = trans.gettext
        for text in test_texts:
            result = _(text)
            if result != text or lang == 'fr':
                print(f"  ✅ '{text[:40]}...' -> '{result[:40]}...'")
            else:
                print(f"  ⚠️  '{text[:40]}...' -> PAS TRADUIT")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

PYEOF

echo ""
echo "========================================="
echo "✅ TERMINÉ !"
echo "========================================="
echo ""
echo "🔄 Redémarrez l'application:"
echo "   pkill -f python"
echo "   export LANG=fr_FR.UTF-8"
echo "   python3 app.py"
