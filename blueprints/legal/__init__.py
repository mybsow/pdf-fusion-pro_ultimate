from flask import Blueprint
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # remonte jusqu’au dossier racine du projet

legal_bp = Blueprint(
    'legal',
    __name__,
    template_folder=str(BASE_DIR / 'templates'),
    static_folder=str(BASE_DIR / 'static')
)

from . import routes
