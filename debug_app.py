#!/usr/bin/env python3
"""
Version de debug pour identifier les problèmes
"""

import os
import sys
import traceback

# Ajouter le répertoire courant au chemin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

print("="*60)
print("DEBUG MODE - PDF FUSION PRO")
print("="*60)

# Créer une app simple pour tester
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Page d'accueil simple - OK"

@app.route('/test-blueprint')
def test_blueprint():
    try:
        from blueprints.pdf import pdf_bp
        return "✅ Blueprint PDF importé avec succès"
    except Exception as e:
        return f"❌ Erreur: {str(e)}<br>{traceback.format_exc()}"

@app.route('/test-config')
def test_config():
    try:
        from config import AppConfig
        return f"✅ Config importée: {AppConfig.NAME} v{AppConfig.VERSION}"
    except Exception as e:
        return f"❌ Erreur: {str(e)}"

@app.route('/test-stats')
def test_stats():
    try:
        from utils.stats_manager import stats_manager
        return f"✅ Stats manager: {stats_manager.stats.get('total_operations', 0)} opérations"
    except Exception as e:
        return f"❌ Erreur: {str(e)}"

if __name__ == '__main__':
    print("\nRoutes disponibles:")
    print("  http://localhost:5000/")
    print("  http://localhost:5000/test-blueprint")
    print("  http://localhost:5000/test-config")
    print("  http://localhost:5000/test-stats")
    print("\nDémarrage du serveur...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)