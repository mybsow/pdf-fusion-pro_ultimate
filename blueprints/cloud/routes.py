# blueprints/cloud/routes.py
import os
import tempfile
from flask import session, jsonify, request, send_file, current_app
from . import cloud_bp
from .providers import GoogleDriveProvider, OneDriveProvider, DropboxProvider, iCloudProvider

# Initialisation des providers
providers = {
    'google': GoogleDriveProvider(),
    'onedrive': OneDriveProvider(),
    'dropbox': DropboxProvider(),
    'icloud': iCloudProvider(),
}

@cloud_bp.route('/auth/<provider>')
def auth(provider):
    """Redirige vers l'authentification du provider"""
    if provider not in providers:
        return jsonify({'error': 'Provider non supporté'}), 400
    
    auth_url = providers[provider].get_auth_url()
    return jsonify({'auth_url': auth_url})

@cloud_bp.route('/callback/<provider>')
def callback(provider):
    """Callback après authentification"""
    if provider not in providers:
        return jsonify({'error': 'Provider non supporté'}), 400
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return jsonify({'error': error}), 400
    
    if not code:
        return jsonify({'error': 'Code manquant'}), 400
    
    try:
        token = providers[provider].exchange_code(code)
        session[f'{provider}_token'] = token
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cloud_bp.route('/files/<provider>')
def get_files(provider):
    """Récupère la liste des fichiers"""
    if provider not in providers:
        return jsonify({'error': 'Provider non supporté'}), 400
    
    token = session.get(f'{provider}_token')
    if not token:
        return jsonify({'error': 'Non authentifié'}), 401
    
    path = request.args.get('path', '/')
    
    try:
        files = providers[provider].list_files(token, path)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cloud_bp.route('/download/<provider>')
def download_file(provider):
    """Télécharge un fichier depuis le cloud"""
    if provider not in providers:
        return jsonify({'error': 'Provider non supporté'}), 400
    
    token = session.get(f'{provider}_token')
    if not token:
        return jsonify({'error': 'Non authentifié'}), 401
    
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({'error': 'Chemin manquant'}), 400
    
    try:
        # Télécharger le fichier
        file_data, filename = providers[provider].download_file(token, file_path)
        
        # Créer un fichier temporaire
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cloud_bp.route('/logout/<provider>')
def logout(provider):
    """Déconnecte le provider"""
    if provider in session:
        session.pop(f'{provider}_token', None)
    return jsonify({'success': True})