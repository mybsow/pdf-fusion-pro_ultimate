#!/bin/bash
# scripts/init_translations.sh

echo "🌍 Initialisation des traductions..."

# Créer le dossier des traductions
mkdir -p translations

# Langues supportées
LANGUAGES=("en" "es" "de" "it" "pt" "ar" "zh" "ja" "ru" "nl")

# Extraire les textes
echo "📤 Extraction des textes..."
pybabel extract -F babel.cfg -o messages.pot .

# Initialiser chaque langue
for lang in "${LANGUAGES[@]}"; do
    if [ ! -d "translations/$lang" ]; then
        echo "🌍 Création de la langue: $lang"
        pybabel init -i messages.pot -d translations -l $lang
    else
        echo "🔄 Mise à jour de: $lang"
        pybabel update -i messages.pot -d translations -l $lang
    fi
done

# Compiler les traductions
echo "🔨 Compilation..."
pybabel compile -d translations

echo "✅ Traductions initialisées !"
