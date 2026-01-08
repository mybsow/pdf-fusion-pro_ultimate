"""
Blueprint pour les pages légales
"""

from flask import Blueprint

legal_bp = Blueprint(
    'legal',
    __name__,
    template_folder='../../templates/legal'
)

from . import routes