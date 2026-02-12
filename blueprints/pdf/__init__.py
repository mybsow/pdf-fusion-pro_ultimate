# /workspaces/pdf-fusion-pro_ultimate/blueprints/pdf/__init__.py
"""
Blueprint principal pour les outils PDF
"""

from flask import Blueprint

# Création du blueprint PDF
pdf_bp = Blueprint(
    'pdf', 
    __name__,
    template_folder='../../templates/pdf',
    static_folder='../../static',
    url_prefix='/pdf'
)

# N'importez PAS routes ici !!!
# from . import routes  ← SUPPRIMEZ CETTE LIGNE