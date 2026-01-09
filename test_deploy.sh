#!/bin/bash
echo "=== Test avant déploiement ==="

# Test 1: Vérifiez les imports
echo "1. Test des imports..."
python -c "
try:
    from app import create_app
    app = create_app()
    print('   ✅ app.py fonctionne')
except Exception as e:
    print(f'   ❌ Erreur: {e}')
"

# Test 2: Vérifiez le blueprint PDF
echo "2. Test du blueprint PDF..."
python -c "
try:
    from blueprints.pdf import pdf_bp
    print('   ✅ Blueprint PDF importé')
except Exception as e:
    print(f'   ❌ Erreur: {e}')
"

# Test 3: Vérifiez les routes
echo "3. Test des routes..."
python -c "
from app import create_app
app = create_app()

with app.test_client() as client:
    routes_to_test = ['/', '/health', '/robots.txt']
    for route in routes_to_test:
        response = client.get(route)
        status = '✅' if response.status_code in [200, 302] else '❌'
        print(f'   {status} {route} ({response.status_code})')
"

echo "=== Tests terminés ==="
