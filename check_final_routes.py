from app import create_app
app = create_app()

print("Routes finales :")
print("=" * 60)

# Routes pour la racine
print("\nRoutes pour '/':")
for rule in app.url_map.iter_rules():
    if rule.rule == '/':
        print(f"  - {rule.endpoint}")

# Toutes les routes
print("\nToutes les routes :")
for rule in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    print(f"{rule.rule:40} -> {rule.endpoint}")
