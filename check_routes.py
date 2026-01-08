from app import create_app
app = create_app()

print("📋 Routes disponibles dans l'application :")
print("=" * 60)

# Triez les routes par URL
rules = sorted(app.url_map.iter_rules(), key=lambda x: x.rule)

for rule in rules:
    methods = ', '.join(rule.methods - {'OPTIONS', 'HEAD'})
    print(f"{rule.rule:40} -> {rule.endpoint:30} [{methods}]")

print("\n🔍 Recherche de conflits sur '/' :")
root_routes = [r for r in rules if r.rule == '/']
if root_routes:
    print(f"Trouvé {len(root_routes)} route(s) pour '/':")
    for route in root_routes:
        print(f"  - {route.endpoint}")
else:
    print("Aucune route trouvée pour '/'")
