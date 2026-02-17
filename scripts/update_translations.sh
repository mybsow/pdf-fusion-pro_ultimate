#!/bin/bash
# Script de mise à jour des traductions

echo "🔄 Mise à jour des traductions..."

# Extraire les nouveaux textes
echo "📤 Extraction des nouveaux textes..."
pybabel extract -F babel.cfg -o messages.pot .

# Mettre à jour toutes les langues
for lang in translations/*/ ; do
    if [ -d "$lang" ]; then
        lang_code=$(basename $lang)
        echo "🌍 Mise à jour de $lang_code..."
        pybabel update -i messages.pot -d translations -l $lang_code
    fi
done

# Recompiler
echo "🔨 Recompilation..."
pybabel compile -d translations

echo "✅ Mise à jour terminée !"