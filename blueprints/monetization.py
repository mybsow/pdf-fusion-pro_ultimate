# blueprints/monetization.py
from flask import Blueprint, session, jsonify, request, current_app, render_template, redirect, url_for
import uuid
import time
from datetime import datetime, timedelta

monetization_bp = Blueprint('monetization', __name__, url_prefix='/monetization')

# Stockage temporaire (en production, utilisez Redis ou une base de données)
ad_sessions = {}

@monetization_bp.route('/ad-gate/<conversion_id>')
def ad_gate(conversion_id):
    """Affiche la page avec la publicité obligatoire"""
    session_data = ad_sessions.get(conversion_id)
    if not session_data:
        return redirect(url_for('pdf.pdf_index'))
    
    return render_template('monetization/ad_gate.html', 
                         conversion_id=conversion_id,
                         conversion_url=session_data.get('return_url'))

@monetization_bp.route('/api/request-ad', methods=['POST'])
def request_ad():
    """Demande une publicité avant conversion"""
    conversion_id = str(uuid.uuid4())
    ad_sessions[conversion_id] = {
        'status': 'pending',
        'created_at': time.time(),
        'expires_at': time.time() + 3600,
        'return_url': request.json.get('return_url', '/')
    }
    return jsonify({'conversion_id': conversion_id})

@monetization_bp.route('/api/ad-complete', methods=['POST'])
def ad_complete():
    """Appelé quand la publicité est terminée"""
    data = request.json
    conversion_id = data.get('conversion_id')
    
    if conversion_id in ad_sessions:
        ad_sessions[conversion_id]['status'] = 'completed'
        # Stocker dans la session utilisateur
        session['ad_completed'] = True
        session['ad_completed_at'] = datetime.now().isoformat()
        return jsonify({'success': True})
    
    return jsonify({'success': False}), 404

@monetization_bp.route('/api/verify-ad/<conversion_id>')
def verify_ad(conversion_id):
    """Vérifie si la publicité a été regardée"""
    session_data = ad_sessions.get(conversion_id)
    if session_data and session_data['status'] == 'completed':
        return jsonify({'valid': True, 'token': conversion_id})
    return jsonify({'valid': False})