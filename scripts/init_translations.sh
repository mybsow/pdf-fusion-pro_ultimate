#!/bin/bash
# scripts/init_translations.sh

set -e

echo "🌍 INITIALISATION DES TRADUCTIONS"
echo "================================="

# Vérifier que pybabel est disponible
if ! command -v pybabel &> /dev/null; then
    echo "❌ pybabel non trouvé. Installation..."
    pip install Flask-Babel Babel
fi

# Créer le dossier translations
mkdir -p translations

# Extraire les textes
echo "📤 Extraction des textes..."
pybabel extract -F babel.cfg -o messages.pot .

# Liste des langues
LANGUAGES=("en" "es" "de" "it" "pt" "ar" "zh" "ja" "ru" "nl")

# Initialiser chaque langue
for lang in "${LANGUAGES[@]}"; do
    if [ ! -d "translations/$lang" ]; then
        echo "🌍 Création de la langue: $lang"
        pybabel init -i messages.pot -d translations -l $lang
        
        # Ajouter des traductions par défaut (optionnel)
        if [ -f "scripts/translations/$lang.po" ]; then
            echo "📝 Ajout des traductions pré-définies pour $lang"
            cp "scripts/translations/$lang.po" "translations/$lang/LC_MESSAGES/messages.po"
        fi
    else
        echo "🔄 Mise à jour de: $lang"
        pybabel update -i messages.pot -d translations -l $lang
    fi
done

# Compiler les traductions
echo "🔨 Compilation..."
pybabel compile -d translations

# Afficher les fichiers générés
echo "📁 Fichiers compilés:"
find translations -name "*.mo" | sed 's/^/   /'

echo "================================="
echo "✅ INITIALISATION TERMINÉE"
