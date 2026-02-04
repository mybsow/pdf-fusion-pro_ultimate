from flask import Blueprint

legal_bp = Blueprint('legal', __name__, 
                    template_folder='../templates',
                    static_folder='../static')

# Import des routes
from . import routes
