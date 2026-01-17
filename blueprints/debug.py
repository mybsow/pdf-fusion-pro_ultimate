"""
Blueprint de débogage pour l'administration
"""

import os
import json
from pathlib import Path
from flask import Blueprint, jsonify, render_template_string
from managers.contact_manager import contact_manager
from managers.rating_manager import rating_manager
from managers.stats_manager import stats_manager

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/')
def debug_home():
    """Page d'accueil du debug"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug - PDF Fusion Pro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>🔧 Debug Dashboard</h1>
            <p>Outils de débogage pour PDF Fusion Pro</p>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📊 Données brutes</h5>
                            <p class="card-text">Accéder aux données JSON brutes</p>
                            <a href="/debug/data" class="btn btn-primary">Voir les données</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📁 Fichiers</h5>
                            <p class="card-text">Vérifier l'existence des fichiers</p>
                            <a href="/debug/files" class="btn btn-info">Vérifier fichiers</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">⚙️ Configuration</h5>
                            <p class="card-text">Voir la configuration de l'app</p>
                            <a href="/debug/config" class="btn btn-warning">Configuration</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="/admin" class="btn btn-secondary">Retour à l'admin</a>
                <a href="/" class="btn btn-outline-secondary">Retour à l'accueil</a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@debug_bp.route('/data')
def debug_data():
    """Endpoint de débogage pour vérifier les données"""
    
    messages = contact_manager.get_all_sorted()
    ratings = rating_manager.get_all_ratings(force_refresh=True)
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'contacts': {
            'total': len(messages),
            'unseen': contact_manager.get_unseen_count(),
            'recent': messages[:5] if messages else []
        },
        'ratings': {
            'total': len(ratings),
            'stats': rating_manager.get_stats(),
            'recent': ratings[:5] if ratings else []
        },
        'operations': {
            'total': stats_manager.get_stat("total_operations", 0),
            'merges': stats_manager.get_stat("merges", 0),
            'splits': stats_manager.get_stat("splits", 0),
            'rotations': stats_manager.get_stat("rotations", 0),
            'compressions': stats_manager.get_stat("compressions", 0)
        }
    })

@debug_bp.route('/files')
def debug_files():
    """Vérifier l'existence des fichiers"""
    import os
    from pathlib import Path
    
    files_info = {
        'data_dir': {
            'exists': Path('data').exists(),
            'is_dir': Path('data').is_dir() if Path('data').exists() else False
        },
        'contacts_json': {
            'path': 'data/contacts.json',
            'exists': Path('data/contacts.json').exists(),
            'size': Path('data/contacts.json').stat().st_size if Path('data/contacts.json').exists() else 0
        },
        'ratings_dir': {
            'path': 'data/ratings',
            'exists': Path('data/ratings').exists(),
            'is_dir': Path('data/ratings').is_dir() if Path('data/ratings').exists() else False,
            'file_count': len(list(Path('data/ratings').glob('*.json'))) if Path('data/ratings').exists() else 0
        }
    }
    
    return jsonify(files_info)

@debug_bp.route('/config')
def debug_config():
    """Afficher la configuration"""
    import os
    
    config_info = {
        'environment': {
            'python_version': os.sys.version,
            'working_directory': os.getcwd(),
            'flask_env': os.environ.get('FLASK_ENV', 'Not set'),
            'render': os.environ.get('RENDER', 'Not set')
        },
        'app_config': {
            'name': 'PDF Fusion Pro',
            'version': '6.1-Material-Pro',
            'max_file_size': '50MB'
        },
        'paths': {
            'app_py': os.path.exists('app.py'),
            'requirements': os.path.exists('requirements.txt'),
            'runtime': os.path.exists('runtime.txt')
        }
    }
    
    return jsonify(config_info)

# Import nécessaire pour datetime
from datetime import datetime
