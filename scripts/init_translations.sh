#!/bin/bash

echo "🔧 RESTAURATION ET EXTRACTION SÉLECTIVE"
echo "========================================"

# 1. Restauration
echo -e "\n📦 Étape 1: Restauration des fichiers .po..."
for lang in pt it de ja ru ar fr nl zh es en; do
    po_file="translations/$lang/LC_MESSAGES/messages.po"
    if [ -f "$po_file.empty.bak" ]; then
        cp "$po_file.empty.bak" "$po_file"
        echo "  ✅ $lang restauré"
    elif [ -f "$po_file.final.bak" ]; then
        cp "$po_file.final.bak" "$po_file"
        echo "  ✅ $lang restauré (backup final)"
    else
        echo "  ⚠️ Backup non trouvé pour $lang"
    fi
done

# 2. Vérification rapide
echo -e "\n🔍 Vérification de la restauration..."
pybabel compile -d translations 2>&1 | grep "error" || echo "  ✅ Aucune erreur"

# 3. Création du fichier de configuration
cat > babel.cfg << 'EOF'
[python: **/blueprints/**.py]
[python: **/managers/**.py]
[python: **/utils/**.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
EOF

# 4. Extraction sélective
echo -e "\n📦 Extraction des messages (uniquement blueprints, managers, utils, templates)..."
pybabel extract -F babel.cfg -o messages.pot blueprints/ managers/ utils/ templates/

# 5. Mise à jour
echo -e "\n🔄 Mise à jour des catalogues..."
pybabel update -i messages.pot -d translations --no-fuzzy-matching

# 6. Compilation finale
echo -e "\n🔄 Compilation finale..."
pybabel compile -d translations

if [ $? -eq 0 ]; then
    echo -e "\n✅ SUCCÈS ! Toutes les traductions sont prêtes."
else
    echo -e "\n⚠️ Des erreurs persistent. Vérifiez manuellement."
fi