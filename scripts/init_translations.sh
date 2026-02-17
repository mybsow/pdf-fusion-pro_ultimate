#!/bin/bash
# Script d'initialisation des traductions

echo "🔧 Initialisation des traductions..."

# Créer le dossier translations s'il n'existe pas
mkdir -p translations

# Extraire les textes
echo "📤 Extraction des textes à traduire..."
pybabel extract -F babel.cfg -o messages.pot .

# Langues à initialiser
LANGUAGES=("en" "es" "de" "it" "pt" "ar" "zh" "ja" "ru" "nl")

for lang in "${LANGUAGES[@]}"
do
    if [ ! -d "translations/$lang" ]; then
        echo "🌍 Création de la langue: $lang"
        pybabel init -i messages.pot -d translations -l $lang
    else
        echo "🔄 Mise à jour de la langue: $lang"
        pybabel update -i messages.pot -d translations -l $lang
    fi
done

# Compiler les traductions
echo "🔨 Compilation des traductions..."
pybabel compile -d translations

echo "✅ Initialisation terminée !"