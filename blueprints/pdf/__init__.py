"""
Blueprint principal pour les outils PDF
"""

from flask import Blueprint

# Version minimaliste et sûre
pdf_bp = Blueprint('pdf', __name__)

# Ne pas importer routes ici pour éviter les imports circulaires
# L'import sera fait par app.py