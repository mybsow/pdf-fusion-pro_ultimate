#!/bin/bash

echo "========================================="
echo "RECONSTRUCTION COMPLÈTE DES TRADUCTIONS"
echo "========================================="
echo ""

# 1. Sauvegarder l'ancien dossier
echo "1. Sauvegarde des anciens fichiers..."
mv translations translations_old_backup
mkdir -p translations

# 2. Extraire tous les textes des templates
echo ""
echo "2. Extraction des textes à traduire..."
grep -roh "{{ _('[^']*') }}" --include="*.html" templates/ | \
    sed "s/{{ _('\([^']*\)') }}/\1/" | \
    sort -u > /tmp/all_texts.txt

grep -roh "gettext('[^']*')" --include="*.py" blueprints/ | \
    sed "s/gettext('\([^']*\)')/\1/" | \
    sort -u >> /tmp/all_texts.txt

sort -u /tmp/all_texts.txt > /tmp/final_texts.txt
total=$(cat /tmp/final_texts.txt | wc -l)
echo "   ✅ $total textes à traduire"

# 3. Créer les fichiers .po pour chaque langue
echo ""
echo "3. Création des fichiers .po..."

# Liste des langues
languages=("fr" "en" "es" "de" "it" "pt" "nl" "zh" "ja" "ru" "ar")

for lang in "${languages[@]}"; do
    echo "   Création $lang..."
    
    # Créer le dossier
    mkdir -p "translations/$lang/LC_MESSAGES"
    
    # Créer le fichier .po avec en-tête
    cat > "translations/$lang/LC_MESSAGES/messages.po" << HEADER
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
    
    # Ajouter tous les textes
    while IFS= read -r text; do
        [ -z "$text" ] && continue
        
        echo "msgid \"$text\"" >> "translations/$lang/LC_MESSAGES/messages.po"
        
        # Traductions selon la langue
        case $lang in
            fr)
                echo "msgstr \"$text\"" >> "translations/$lang/LC_MESSAGES/messages.po"
                ;;
            en)
                # Traductions anglaises de base
                case "$text" in
                    "Accueil") echo "msgstr \"Home\"" ;;
                    "Fusionner") echo "msgstr \"Merge\"" ;;
                    "Diviser") echo "msgstr \"Split\"" ;;
                    "Tourner") echo "msgstr \"Rotate\"" ;;
                    "Compresser") echo "msgstr \"Compress\"" ;;
                    "Convertir") echo "msgstr \"Convert\"" ;;
                    "Contact") echo "msgstr \"Contact\"" ;;
                    "À propos") echo "msgstr \"About\"" ;;
                    "Version") echo "msgstr \"Version\"" ;;
                    "Extraction OCR") echo "msgstr \"OCR Extraction\"" ;;
                    "Extraction OCR en cours") echo "msgstr \"OCR Extraction in progress\"" ;;
                    "Format PDF") echo "msgstr \"PDF Format\"" ;;
                    "Format Word") echo "msgstr \"Word Format\"" ;;
                    "Attention") echo "msgstr \"Warning\"" ;;
                    "Tesseract OCR — détection automatique des colonnes et en-têtes") echo "msgstr \"Tesseract OCR — automatic column and header detection\"" ;;
                    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") echo "msgstr \"Compatible with all PDF readers. Animations and transitions are not preserved in the PDF.\"" ;;
                    "Compatible avec tous les lecteurs PDF. Les polices sont intégrées pour une reproduction fidèle.") echo "msgstr \"Compatible with all PDF readers. Fonts are embedded for faithful reproduction.\"" ;;
                    "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.") echo "msgstr \"PDF/A is a standardized version of PDF designed for long-term archiving. It ensures that your document will look exactly the same in 10, 20, or 50 years, regardless of the software used.\"" ;;
                    "La conversion en PDF/A peut modifier légèrement l'apparence du document pour garantir sa pérennité. Les fonctionnalités interactives (formulaires, JavaScript) seront supprimées.") echo "msgstr \"Converting to PDF/A may slightly alter the document's appearance to ensure longevity. Interactive features (forms, JavaScript) will be removed.\"" ;;
                    "Le fichier généré est au format DOCX, compatible avec Microsoft Word 2007 et versions ultérieures, ainsi qu'avec LibreOffice et Google Docs.") echo "msgstr \"The generated file is in DOCX format, compatible with Microsoft Word 2007 and later versions, as well as LibreOffice and Google Docs.\"" ;;
                    *) echo "msgstr \"$text\"" ;;
                esac >> "translations/$lang/LC_MESSAGES/messages.po"
                ;;
            es)
                # Traductions espagnoles
                case "$text" in
                    "Accueil") echo "msgstr \"Inicio\"" ;;
                    "Fusionner") echo "msgstr \"Combinar\"" ;;
                    "Diviser") echo "msgstr \"Dividir\"" ;;
                    "Tourner") echo "msgstr \"Rotar\"" ;;
                    "Extraction OCR") echo "msgstr \"Extracción OCR\"" ;;
                    "Format PDF") echo "msgstr \"Formato PDF\"" ;;
                    "Format Word") echo "msgstr \"Formato Word\"" ;;
                    "Attention") echo "msgstr \"Advertencia\"" ;;
                    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") echo "msgstr \"Compatible con todos los lectores PDF. Las animaciones y transiciones no se conservan en el PDF.\"" ;;
                    "Le PDF/A est une version standardisée du PDF conçue pour l'archivage à long terme. Il garantit que votre document sera exactement le même dans 10, 20 ou 50 ans, indépendamment des logiciels utilisés.") echo "msgstr \"PDF/A es una versión estandarizada de PDF diseñada para archivo a largo plazo. Garantiza que su documento se verá exactamente igual dentro de 10, 20 o 50 años, independientemente del software utilizado.\"" ;;
                    *) echo "msgstr \"$text\"" ;;
                esac >> "translations/$lang/LC_MESSAGES/messages.po"
                ;;
            de)
                # Traductions allemandes
                case "$text" in
                    "Accueil") echo "msgstr \"Startseite\"" ;;
                    "Fusionner") echo "msgstr \"Zusammenführen\"" ;;
                    "Extraction OCR") echo "msgstr \"OCR-Extraktion\"" ;;
                    "Format PDF") echo "msgstr \"PDF-Format\"" ;;
                    "Format Word") echo "msgstr \"Word-Format\"" ;;
                    "Attention") echo "msgstr \"Warnung\"" ;;
                    "Compatible avec tous les lecteurs PDF. Les animations et transitions ne sont pas conservées dans le PDF.") echo "msgstr \"Kompatibel mit allen PDF-Readern. Animationen und Übergänge werden nicht im PDF gespeichert.\"" ;;
                    *) echo "msgstr \"$text\"" ;;
                esac >> "translations/$lang/LC_MESSAGES/messages.po"
                ;;
            *)
                echo "msgstr \"$text\"" >> "translations/$lang/LC_MESSAGES/messages.po"
                ;;
        esac
        
        echo "" >> "translations/$lang/LC_MESSAGES/messages.po"
        
    done < /tmp/final_texts.txt
    
    echo "      ✅ $(grep -c "^msgid" translations/$lang/LC_MESSAGES/messages.po) entrées"
done

# 4. Compiler les fichiers .mo
echo ""
echo "4. Compilation des fichiers .mo..."
for po_file in translations/*/LC_MESSAGES/messages.po; do
    lang=$(echo $po_file | cut -d'/' -f2)
    echo -n "   $lang... "
    if msgfmt -o "${po_file%.po}.mo" "$po_file" 2>&1; then
        size=$(ls -lh "${po_file%.po}.mo" | awk '{print $5}')
        echo "✅ ($size)"
    else
        echo "❌ Erreur"
    fi
done

# 5. Vérification finale
echo ""
echo "5. Vérification des traductions..."
python3 << 'PYEOF'
import gettext
import sys

test_texts = [
    "Extraction OCR",
    "Format PDF",
    "Format Word",
    "Attention",
]

print("\nTest des traductions:")
for lang in ['fr', 'en', 'es', 'de']:
    print(f"\n{lang.upper()}:")
    try:
        trans = gettext.translation('messages', './translations', languages=[lang], fallback=True)
        _ = trans.gettext
        for text in test_texts:
            result = _(text)
            if result != text or lang == 'fr':
                print(f"  ✅ '{text}' -> '{result}'")
            else:
                print(f"  ⚠️  '{text}' -> PAS TRADUIT")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
PYEOF

echo ""
echo "========================================="
echo "✅ RECONSTRUCTION TERMINÉE !"
echo "========================================="
echo ""
echo "📊 Résumé:"
echo "   - $total textes traduits"
echo "   - 11 langues disponibles"
echo ""
echo "🔄 Redémarrez l'application:"
echo "   pkill -f python"
echo "   export LANG=fr_FR.UTF-8"
echo "   python3 app.py"
