#!/bin/bash
# scripts/update_translations.sh

echo "🔄 MISE À JOUR DE TOUTES LES TRADUCTIONS"
echo "=========================================="

# Extraire les nouveaux textes
echo "📤 Extraction des textes..."
pybabel extract -F babel.cfg -o messages.pot .

# Liste des langues
LANGUAGES=("en" "es" "de" "it" "pt" "ar" "zh" "ja" "ru" "nl")

# Mettre à jour chaque langue
for lang in "${LANGUAGES[@]}"; do
    if [ -d "translations/$lang" ]; then
        echo "🔄 Mise à jour de $lang..."
        pybabel update -i messages.pot -d translations -l $lang
    else
        echo "🌍 Création de $lang..."
        pybabel init -i messages.pot -d translations -l $lang
    fi
done

# Compiler
echo "🔨 Compilation..."
pybabel compile -d translations

# Vérification
echo ""
echo "📊 STATISTIQUES DES TRADUCTIONS"
echo "================================"
for lang in "${LANGUAGES[@]}"; do
    if [ -f "translations/$lang/LC_MESSAGES/messages.po" ]; then
        total=$(grep -c "msgid" "translations/$lang/LC_MESSAGES/messages.po" 2>/dev/null || echo "0")
        translated=$(grep -c "msgstr" "translations/$lang/LC_MESSAGES/messages.po" 2>/dev/null || echo "0")
        echo "🌍 $lang : $total messages, $translated traduits"
    fi
done

echo ""
echo "✅ Mise à jour terminée !"
