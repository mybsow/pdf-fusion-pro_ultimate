#!/bin/bash

echo "========================================="
echo "LOCALISATION DES TEXTES À TRADUIRE"
echo "========================================="
echo ""

# Liste des textes à rechercher
declare -a texts=(
    "Extraction OCR"
    "Tesseract OCR — détection automatique des colonnes et en-têtes"
    "Word format: Le fichier généré est au format DOCX"
    "Le PDF/A est une version standardisée"
    "Warning: La conversion en PDF/A"
    "PDF format: Compatible avec tous les lecteurs PDF"
    "Les animations et transitions ne sont pas conservées"
    "Les polices sont intégrées pour une reproduction fidèle"
)

for text in "${texts[@]}"; do
    echo "=== $text ==="
    grep -rn "$text" --include="*.html" --include="*.py" . 2>/dev/null | while read line; do
        echo "  $line"
    done
    echo ""
done

echo "========================================="
echo "RÉSUMÉ PAR FICHIER"
echo "========================================="
echo ""

# Compter les occurrences par fichier
for file in $(find . -name "*.html" -o -name "*.py" | grep -v "__pycache__"); do
    count=$(grep -c "{{ _(" "$file" 2>/dev/null || echo 0)
    if [ $count -gt 0 ]; then
        echo "$file: $count textes à traduire"
    fi
done | sort -t: -k2 -rn | head -20
