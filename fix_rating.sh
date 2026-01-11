#!/bin/bash

echo "=== CORRECTION DU SYSTÈME D'ÉVALUATION ==="
echo

# 1. Vérifier la présence de get_rating_html
echo "1. Vérification de la fonction get_rating_html:"
if grep -q "def get_rating_html():" blueprints/pdf/routes.py; then
    echo "   ✅ Fonction présente"
else
    echo "   ❌ Fonction absente"
fi

# 2. Vérifier l'utilisation dans les routes
echo "2. Vérification de l'utilisation dans les routes:"
ROUTES_WITH_RATING=$(grep -n "rating_html=get_rating_html()" blueprints/pdf/routes.py | wc -l)
echo "   Routes avec rating_html: $ROUTES_WITH_RATING"

# 3. Vérifier {{ rating_html }} dans le template
echo "3. Vérification du template:"
if grep -q "{{ rating_html }}" blueprints/pdf/routes.py; then
    echo "   ✅ {{ rating_html }} présent dans le template"
else
    echo "   ❌ {{ rating_html }} absent du template"
fi

# 4. Tester la syntaxe
echo "4. Test de syntaxe:"
python -m py_compile blueprints/pdf/routes.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Syntaxe correcte"
else
    echo "   ❌ Erreur de syntaxe"
    python -m py_compile blueprints/pdf/routes.py
fi

# 5. Tester avec une page simple
echo "5. Test rapide du HTML généré:"
python3 -c "
def get_rating_html():
    html = '''<div id=\"ratingPopup\">Test</div>'''
    return html

print('Fonction test:')
print(get_rating_html()[:50] + '...')
"

echo
echo "=== CORRECTIONS À APPLIQUER ==="
echo "1. Utilisez la version corrigée de get_rating_html()"
echo "2. Assurez-vous que rating_html est passé aux routes"
echo "3. Vérifiez que {{ rating_html }} est dans le template"
