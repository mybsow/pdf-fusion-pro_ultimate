#!/bin/bash

echo "========================================="
echo "NETTOYAGE ET RECONSTRUCTION COMPLÈTE"
echo "========================================="
echo ""

# 1. Sauvegarder les fichiers existants
echo "1. Sauvegarde des fichiers existants..."
mkdir -p translations_backup
cp -r translations/* translations_backup/
echo "   ✅ Sauvegarde créée dans translations_backup/"

# 2. Nettoyer tous les fichiers .po des doublons et erreurs
echo ""
echo "2. Nettoyage des fichiers .po..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    if [ -f "$po_file" ]; then
        lang=$(echo $po_file | cut -d'/' -f2)
        echo "   Nettoyage $lang..."
        
        # Supprimer les lignes vides en trop et les doublons
        sed -i '/^$/N;/^\n$/D' "$po_file"
        
        # Vérifier et réparer avec msguniq
        if command -v msguniq &> /dev/null; then
            msguniq "$po_file" > "${po_file}.tmp"
            mv "${po_file}.tmp" "$po_file"
        fi
    fi
done

# 3. Ajouter les textes manquants avec la bonne syntaxe
echo ""
echo "3. Ajout des textes manquants..."

# Créer un fichier temporaire avec tous les textes nécessaires
cat > /tmp/required_texts.txt << 'TEXTS'
Extraction OCR
Extraction OCR en cours
Tesseract OCR — détection automatique des colonnes et en-têtes
Format Word
Format PDF
Attention
Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.
Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.
Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.
La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées.
Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs.
TEXTS

# Pour chaque langue
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo "   $lang..."
    
    while IFS= read -r text; do
        [ -z "$text" ] && continue
        
        # Vérifier si le texte existe déjà
        if ! grep -q "^msgid \"$text\"$" "$po_file"; then
            # Ajouter le texte
            echo "" >> "$po_file"
            echo "msgid \"$text\"" >> "$po_file"
            
            # Ajouter la traduction selon la langue
            case $lang in
                fr)
                    echo "msgstr \"$text\"" >> "$po_file"
                    ;;
                en)
                    case "$text" in
                        "Extraction OCR") echo "msgstr \"OCR Extraction\"" >> "$po_file" ;;
                        "Extraction OCR en cours") echo "msgstr \"OCR Extraction in progress\"" >> "$po_file" ;;
                        "Tesseract OCR — détection automatique des colonnes et en-têtes") echo "msgstr \"Tesseract OCR — automatic column and header detection\"" >> "$po_file" ;;
                        "Format Word") echo "msgstr \"Word Format\"" >> "$po_file" ;;
                        "Format PDF") echo "msgstr \"PDF Format\"" >> "$po_file" ;;
                        "Attention") echo "msgstr \"Warning\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") echo "msgstr \"Compatible with all PDF readers. Animations and transitions are not preserved in the PDF.\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.") echo "msgstr \"Compatible with all PDF readers. Fonts are embedded for faithful reproduction.\"" >> "$po_file" ;;
                        "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.") echo "msgstr \"PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used.\"" >> "$po_file" ;;
                        "La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées.") echo "msgstr \"Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed.\"" >> "$po_file" ;;
                        "Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs.") echo "msgstr \"The generated file is in DOCX format, compatible with Microsoft Word 2007 and later versions, as well as LibreOffice and Google Docs.\"" >> "$po_file" ;;
                        *) echo "msgstr \"$text\"" >> "$po_file" ;;
                    esac
                    ;;
                es)
                    case "$text" in
                        "Extraction OCR") echo "msgstr \"Extracción OCR\"" >> "$po_file" ;;
                        "Format Word") echo "msgstr \"Formato Word\"" >> "$po_file" ;;
                        "Format PDF") echo "msgstr \"Formato PDF\"" >> "$po_file" ;;
                        "Attention") echo "msgstr \"Advertencia\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") echo "msgstr \"Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF.\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.") echo "msgstr \"Compatible con todos los lectores PDF. Las fuentes están incrustadas para una reproducción fiel.\"" >> "$po_file" ;;
                        "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.") echo "msgstr \"PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado.\"" >> "$po_file" ;;
                        *) echo "msgstr \"$text\"" >> "$po_file" ;;
                    esac
                    ;;
                de)
                    case "$text" in
                        "Extraction OCR") echo "msgstr \"OCR-Extraktion\"" >> "$po_file" ;;
                        "Format Word") echo "msgstr \"Word-Format\"" >> "$po_file" ;;
                        "Format PDF") echo "msgstr \"PDF-Format\"" >> "$po_file" ;;
                        "Attention") echo "msgstr \"Warnung\"" >> "$po_file" ;;
                        "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") echo "msgstr \"Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert.\"" >> "$po_file" ;;
                        *) echo "msgstr \"$text\"" >> "$po_file" ;;
                    esac
                    ;;
                *)
                    echo "msgstr \"$text\"" >> "$po_file"
                    ;;
            esac
        fi
    done < /tmp/required_texts.txt
done

# 4. Supprimer les msgid avec deux-points
echo ""
echo "4. Suppression des msgid contenant des deux-points..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    # Supprimer les entrées avec deux-points dans msgid
    sed -i '/^msgid ".*:.*"$/,/^msgstr/d' "$po_file"
    # Nettoyer les lignes vides en trop
    sed -i '/^$/N;/^\n$/D' "$po_file"
done

# 5. Compiler les fichiers .mo
echo ""
echo "5. Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>/dev/null; then
        size=$(ls -lh "${po_file%.po}.mo" | awk '{print $5}')
        entries=$(grep -c "^msgid" "$po_file")
        echo "✅ ($entries entrées, $size)"
    else
        echo "❌ Erreur - affichage des erreurs:"
        msgfmt -o /dev/null "$po_file" 2>&1 | head -5
    fi
done

# 6. Vérification finale
echo ""
echo "6. Vérification des traductions..."
python3 << 'PYEOF'
import gettext
import os

test_texts = [
    ("Extraction OCR", "OCR Extraction", "Extracción OCR"),
    ("Format PDF", "PDF Format", "Formato PDF"),
    ("Format Word", "Word Format", "Formato Word"),
    ("Attention", "Warning", "Advertencia"),
]

print("\nTest des traductions:")
for fr_text, en_expected, es_expected in test_texts:
    print(f"\nTexte: '{fr_text}'")
    
    # Français
    trans_fr = gettext.translation('messages', './translations', languages=['fr'], fallback=True)
    _fr = trans_fr.gettext
    result_fr = _fr(fr_text)
    print(f"  🇫🇷 FR: '{result_fr}'")
    
    # Anglais
    trans_en = gettext.translation('messages', './translations', languages=['en'], fallback=True)
    _en = trans_en.gettext
    result_en = _en(fr_text)
    print(f"  🇬🇧 EN: '{result_en}'")
    if result_en == en_expected:
        print(f"      ✅ Correct")
    else:
        print(f"      ⚠️  Attendu: '{en_expected}'")
    
    # Espagnol
    trans_es = gettext.translation('messages', './translations', languages=['es'], fallback=True)
    _es = trans_es.gettext
    result_es = _es(fr_text)
    print(f"  🇪🇸 ES: '{result_es}'")
    if result_es == es_expected:
        print(f"      ✅ Correct")

print("\n" + "="*50)
print("✅ Vérification terminée !")
PYEOF

echo ""
echo "========================================="
echo "✅ TERMINÉ !"
echo "========================================="
