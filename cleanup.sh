#!/bin/bash
echo "Nettoyage des processus Flask..."
# Tuer tous les processus Python Flask
pkill -f "python.*app\.py" 2>/dev/null
pkill -f "flask" 2>/dev/null
pkill -f "gunicorn" 2>/dev/null

# Libérer le port 5000
echo "Libération du port 5000..."
for pid in $(lsof -ti:5000); do
    echo "  Arrêt du processus $pid"
    kill -9 $pid 2>/dev/null
done

# Vérification
echo "Vérification..."
if lsof -i:5000 >/dev/null 2>&1; then
    echo "❌ Port 5000 toujours utilisé"
    lsof -i:5000
else
    echo "✅ Port 5000 libre"
fi

# Nettoyer les fichiers temporaires
echo "Nettoyage des fichiers temporaires..."
rm -f app.log 2>/dev/null
rm -f nohup.out 2>/dev/null

echo "Prêt !"
