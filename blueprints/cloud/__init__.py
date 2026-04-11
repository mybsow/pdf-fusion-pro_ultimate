# blueprints/cloud/__init__.py
from flask import Blueprint

cloud_bp = Blueprint('cloud', __name__, url_prefix='/cloud')

from . import routes