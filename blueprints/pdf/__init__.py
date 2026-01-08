"""
Blueprint principal pour les outils PDF
"""

from flask import Blueprint

# Version minimaliste et sûre
pdf_bp = Blueprint('pdf', __name__)

# IMPORTANT : Il faut importer les routes pour qu'elles soient enregistrées
from . import routes
