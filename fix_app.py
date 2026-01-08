import re

with open('app.py', 'r') as f:
    content = f.read()

# Trouvons et remplaçons la fonction root
root_pattern = r"@app\.route\('/'\)\s+def root\(\):.*?\n\n"
root_replacement = '''@app.route('/')
def root():
    """Route racine - utilise le blueprint PDF"""
    from blueprints.pdf.routes import home as pdf_home
    return pdf_home()

'''

content = re.sub(root_pattern, root_replacement, content, flags=re.DOTALL)

# Supprimons la fonction index en double
index_pattern = r"@app\.route\('/'\)\s+def index\(\):.*?\n\n"
content = re.sub(index_pattern, '', content, flags=re.DOTALL)

with open('app.py', 'w') as f:
    f.write(content)

print("✅ app.py corrigé !")
