#!/bin/bash
echo "=== TEST COMPLET DU SYSTÈME D'ÉVALUATION ==="
echo

# 1. Test santé
echo "1. Test de santé de l'application:"
HEALTH=$(curl -s http://127.0.0.1:5000/health)
if echo "$HEALTH" | grep -q '"status": "healthy"'; then
    echo "   ✅ Application saine"
else
    echo "   ❌ Problème de santé"
    echo "$HEALTH"
fi

# 2. Test présence popup
echo "2. Vérification du popup dans le HTML:"
if curl -s http://127.0.0.1:5000/ | grep -q "ratingPopup"; then
    echo "   ✅ Code HTML présent"
else
    echo "   ❌ Code HTML absent"
fi

# 3. Test API valide
echo "3. Test API d'évaluation (valide):"
API_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://127.0.0.1:5000/api/rating \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "feedback": "Test automatique", "page": "/"}')

HTTP_CODE=$(echo "$API_RESPONSE" | tail -1)
BODY=$(echo "$API_RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API fonctionnelle"
    echo "   Réponse: $BODY"
else
    echo "   ❌ API en erreur (code: $HTTP_CODE)"
fi

# 4. Test API invalide
echo "4. Test API d'évaluation (invalide):"
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://127.0.0.1:5000/api/rating \
  -H "Content-Type: application/json" \
  -d '{"rating": 10}')

INVALID_CODE=$(echo "$INVALID_RESPONSE" | tail -1)
if [ "$INVALID_CODE" = "400" ]; then
    echo "   ✅ Validation fonctionne"
else
    echo "   ❌ Validation défaillante (code: $INVALID_CODE)"
fi

# 5. Vérification données
echo "5. Vérification des données:"
if [ -f "data/ratings.json" ]; then
    COUNT=$(python3 -c "import json; data=json.load(open('data/ratings.json')); print(len(data))" 2>/dev/null || echo "0")
    echo "   ✅ $COUNT évaluation(s) enregistrée(s)"
    
    # Afficher la dernière
    echo "   Dernière évaluation:"
    python3 -c "
import json
try:
    with open('data/ratings.json') as f:
        data = json.load(f)
    if data:
        last = data[-1]
        print(f'    Note: {last[\"rating\"]}/5')
        print(f'    Feedback: {last.get(\"feedback\", \"(vide)\")}')
        print(f'    Date: {last[\"timestamp\"][:19]}')
except Exception as e:
    print(f'    Erreur: {e}')
" 2>/dev/null
else
    echo "   ⚠️  Fichier non créé"
fi

echo
echo "=== TESTS TERMINÉS ==="
echo
echo "Pour tester visuellement:"
echo "1. Ouvrez http://127.0.0.1:5000/"
echo "2. Attendez 30 secondes pour le popup"
echo "3. Testez l'interface complète"
echo
echo "Logs de l'application: tail -f app.log"
