#!/bin/bash

# Liste des textes manquants à ajouter
declare -a missing_texts=(
    "Je ne sais où ce trouve les texte mais je veux qu'ils soient traduits"
    "Extraction OCR"
    "Tesseract OCR — détection automatique des colonnes et en-têtes"
    "Word format: Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."
    "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."
    "Warning: La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."
    "PDF format: Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."
    "PDF format: Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."
)

# Traductions anglaises
declare -A en_trans=(
    ["Je ne sais où ce trouve les texte mais je veux qu'ils soient traduits"]="I don't know where these texts are but I want them translated"
    ["Extraction OCR"]="OCR Extraction"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — automatic column and header detection"
    ["Word format: Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="Word format: The generated file is in DOCX format, compatible with Microsoft Word 2007 and later versions, as well as LibreOffice and Google Docs."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used."
    ["Warning: La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Warning: Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed."
    ["PDF format: Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="PDF format: Compatible with all PDF readers. Animations and transitions are not preserved in the PDF."
    ["PDF format: Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="PDF format: Compatible with all PDF readers. Fonts are embedded for faithful reproduction."
)

# Traductions espagnoles
declare -A es_trans=(
    ["Extraction OCR"]="Extracción OCR"
    ["Tesseract OCR — détection automatique des colonnes et en-têtes"]="Tesseract OCR — detección automática de columnas y encabezados"
    ["Word format: Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs."]="Formato Word: El archivo generado está en formato DOCX, compatible con Microsoft Word 2007 y versiones posteriores, así como con LibreOffice y Google Docs."
    ["Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés."]="PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado."
    ["Warning: La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées."]="Advertencia: La conversión a PDF/A puede modificar ligeramente la apariencia del documento para garantizar su longevidad. Las características interactivas (formularios, JavaScript) se eliminarán."
    ["PDF format: Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF."]="Formato PDF: Compatible con todos los lectores de PDF. Las animaciones y transiciones no se conservan en el PDF."
    ["PDF format: Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle."]="Formato PDF: Compatible con todos los lectores de PDF. Las fuentes están incrustadas para una reproducción fiel."
)

# Ajouter les traductions pour chaque langue
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "Traitement de $lang..."
    
    for text in "${missing_texts[@]}"; do
        case $lang in
            fr)
                # Français : garder identique
                if ! grep -q "^msgid \"$text\"$" "$po_file"; then
                    echo "" >> "$po_file"
                    echo "msgid \"$text\"" >> "$po_file"
                    echo "msgstr \"$text\"" >> "$po_file"
                fi
                ;;
            en)
                # Anglais : utiliser traduction
                if [[ -n "${en_trans[$text]}" ]]; then
                    translation="${en_trans[$text]}"
                else
                    translation="$text"
                fi
                if ! grep -q "^msgid \"$text\"$" "$po_file"; then
                    echo "" >> "$po_file"
                    echo "msgid \"$text\"" >> "$po_file"
                    echo "msgstr \"$translation\"" >> "$po_file"
                fi
                ;;
            es)
                # Espagnol : utiliser traduction si disponible
                if [[ -n "${es_trans[$text]}" ]]; then
                    translation="${es_trans[$text]}"
                else
                    translation="$text"
                fi
                if ! grep -q "^msgid \"$text\"$" "$po_file"; then
                    echo "" >> "$po_file"
                    echo "msgid \"$text\"" >> "$po_file"
                    echo "msgstr \"$translation\"" >> "$po_file"
                fi
                ;;
        esac
    done
done

echo ""
echo "✅ Traductions ajoutées ! Compilation..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null
    echo "  ✅ ${po_file}"
done
