"""
Blueprint principal pour les outils PDF
"""

from flask import Blueprint

# Créer le blueprint - C'EST CE QUE app.py ESSAIE D'IMPORTER
pdf_bp = Blueprint(
    'pdf',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)

# Importer les routes APRÈS avoir créé le blueprint
# pour éviter les imports circulaires
from blueprints.pdf import routes