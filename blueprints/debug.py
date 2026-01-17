"""
Blueprint de débogage pour l'administration
"""

import os
import json
from pathlib import Path
from flask import Blueprint, jsonify
from managers.contact_manager import contact_manager
from managers.rating_manager import rating_manager
from managers.stats_manager import stats_manager

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/data')
def debug_data():
    """Endpoint de débogage pour vérifier les données"""
    
    messages = contact_manager.get_all_sorted()
    ratings = rating_manager.get_all_ratings(force_refresh=True)
    
    # Informations sur les fichiers
    contacts_exists = os.path.exists('data/contacts.json')
    ratings_dir_exists = os.path.exists('data/ratings')
    
    if contacts_exists:
        try:
            with open('data/contacts.json', 'r') as f:
                contacts_content = json.load(f)
        except:
            contacts_content = []
    else:
        contacts_content = []
    
    return jsonify({
        'contacts': {
            'file_exists': contacts_exists,
            'count': len(messages),
            'sample': messages[:3] if messages else []
        },
        'ratings': {
            'directory_exists': ratings_dir_exists,
            'count': len(ratings),
            'sample': ratings[:3] if ratings else []
        },
        'stats': {
            'total_operations': stats_manager.get_stat("total_operations", 0),
            'merges': stats_manager.get_stat("merges", 0),
            'splits': stats_manager.get_stat("splits", 0),
            'rotations': stats_manager.get_stat("rotations", 0),
            'compressions': stats_manager.get_stat("compressions", 0)
        }
    })
