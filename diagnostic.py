#!/usr/bin/env python3
"""
Diagnostic complet
"""

import os
import sys
import traceback

def test_import(module_name, import_stmt):
    try:
        exec(import_stmt, globals())
        return True, None
    except Exception as e:
        return False, str(e)

print("="*70)
print("DIAGNOSTIC COMPLET - PDF FUSION PRO")
print("="*70)

tests = [
    ("1. Configuration", "from config import AppConfig"),
    ("2. Stats Manager", "from utils.stats_manager import stats_manager"),
    ("3. Blueprint PDF", "from blueprints.pdf import pdf_bp"),
    ("4. Blueprint API", "from blueprints.api import api_bp"),
    ("5. Blueprint Legal", "from blueprints.legal import legal_bp"),
    ("6. Blueprint Stats", "from blueprints.stats import stats_bp"),
]

all_ok = True
for name, import_stmt in tests:
    success, error = test_import(name, import_stmt)
    if success:
        print(f"✅ {name}")
    else:
        print(f"❌ {name}")
        print(f"   Erreur: {error}")
        all_ok = False

print("\n" + "="*70)
if all_ok:
    print("✅ TOUS LES IMPORTS FONCTIONNENT")
    print("\nLe problème vient probablement des routes ou des templates.")
else:
    print("⚠️  CERTAINS IMPORTS ÉCHOUENT")
    print("\nCorrigez les imports marqués '❌' avant de continuer.")

# Vérifier la structure des fichiers
print("\n" + "="*70)
print("VÉRIFICATION DE LA STRUCTURE DES FICHIERS")
print("="*70)

required_files = [
    'blueprints/pdf/__init__.py',
    'blueprints/pdf/routes.py',
    'blueprints/api/__init__.py',
    'blueprints/api/routes.py',
    'blueprints/legal/__init__.py',
    'blueprints/legal/routes.py',
    'blueprints/stats/__init__.py',
    'blueprints/stats/routes.py',
]

for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - MANQUANT")
        all_ok = False

print("\n" + "="*70)
if all_ok:
    print("✅ PRÊT POUR LE DÉMARRAGE")
    print("\nExécutez: python app.py")
else:
    print("❌ CORRIGEZ LES PROBLÈMES CI-DESSUS")
