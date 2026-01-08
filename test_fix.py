#!/usr/bin/env python3
print("Recherche des blueprints disponibles...")

# Test 1: pdf blueprint
print("\n1. Recherche dans blueprints.pdf:")
import blueprints.pdf
print("   Contenu:", [x for x in dir(blueprints.pdf) if not x.startswith('_')])

# Test 2: api blueprint  
print("\n2. Recherche dans blueprints.api:")
import blueprints.api
print("   Contenu:", [x for x in dir(blueprints.api) if not x.startswith('_')])

# Test 3: legal blueprint
print("\n3. Recherche dans blueprints.legal:")
import blueprints.legal
print("   Contenu:", [x for x in dir(blueprints.legal) if not x.startswith('_')])

# Test 4: stats blueprint
print("\n4. Recherche dans blueprints.stats:")
import blueprints.stats
print("   Contenu:", [x for x in dir(blueprints.stats) if not x.startswith('_')])

print("\n5. Test d'import depuis routes.py:")
try:
    from blueprints.pdf.routes import bp as pdf_bp
    print("   ✓ pdf_bp trouvé dans routes.py")
except ImportError as e:
    print(f"   ✗ Erreur: {e}")
