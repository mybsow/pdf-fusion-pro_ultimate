# blueprints/pdf/__init__.py
from flask import Blueprint

# Création du blueprint PDF
pdf_bp = Blueprint(
    'pdf', 
    __name__,
    template_folder='../../templates/pdf',
    static_folder='../../static',
    url_prefix='/pdf'
)

# Import des routes APRÈS création
from . import routes