from flask import Blueprint, jsonify
from managers.contact_manager import contact_manager
from managers.rating_manager import rating_manager
import os

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/data')
def debug_data():
    """Endpoint de débogage pour vérifier les données"""
    
    messages = contact_manager.get_all_sorted()
    ratings = rating_manager.get_all_ratings(force_refresh=True)
    
    return jsonify({
        'contacts_file_exists': os.path.exists('data/contacts.json'),
        'contacts_count': len(messages),
        'contacts_sample': messages[:3] if messages else [],
        'ratings_dir_exists': os.path.exists('data/ratings'),
        'ratings_files': [f for f in os.listdir('data/ratings') if f.endswith('.json')],
        'ratings_count': len(ratings),
        'ratings_sample': ratings[:3] if ratings else []
    })
