from flask import Blueprint

legal_bp = Blueprint(
    'legal',
    __name__,
    template_folder='../../templates',   # IMPORTANT
    static_folder='../../static'
)

from . import routes
