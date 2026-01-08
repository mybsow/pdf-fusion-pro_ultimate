"""
Blueprint principal pour les outils PDF
"""

from flask import Blueprint

pdf_bp = Blueprint(
    'pdf',
    __name__,
    template_folder='../../templates',
    static_folder='../../static'
)

from . import routes