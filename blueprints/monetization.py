# blueprints/monetization.py
"""
Système de monétisation par publicité.

Logique :
- Première conversion → pub obligatoire
- Fenêtre de grâce : 10 à 20 minutes aléatoires après visionnage
- Après expiration → nouvelle pub requise
- Les fichiers uploadés sont sérialisés en base64 dans la session Flask
  pour survivre à la redirection (pas de fichiers temporaires sur disque)
"""

from flask import (Blueprint, session, jsonify, request,
                   render_template, redirect, url_for, flash, current_app)
import uuid
import random
from datetime import datetime, timedelta
import base64
import json
import logging

logger = logging.getLogger(__name__)

monetization_bp = Blueprint('monetization', __name__, url_prefix='/monetization')

# ---------------------------------------------------------------------------
# Helpers session
# ---------------------------------------------------------------------------

def _grace_seconds() -> int:
    """Retourne une durée de grâce aléatoire entre 10 et 20 minutes."""
    return random.randint(10 * 60, 20 * 60)


def ad_is_valid() -> bool:
    """
    Renvoie True si l'utilisateur a regardé une pub récemment
    et que la fenêtre de grâce n'est pas expirée.
    """
    if not session.get('ad_completed'):
        return False

    expires_at_str = session.get('ad_expires_at')
    if not expires_at_str:
        return False

    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        return datetime.now() < expires_at
    except (ValueError, TypeError):
        return False


def mark_ad_completed():
    """Marque la pub comme vue et fixe l'expiration (10-20 min aléatoires)."""
    grace = _grace_seconds()
    expires_at = datetime.now() + timedelta(seconds=grace)
    session['ad_completed'] = True
    session['ad_completed_at'] = datetime.now().isoformat()
    session['ad_expires_at'] = expires_at.isoformat()
    session['ad_grace_seconds'] = grace
    session.modified = True
    logger.info(f"[Ad] Pub complétée, grâce = {grace}s, expire à {expires_at.isoformat()}")


def save_pending_request(conversion_type: str, form_data: dict, files_dict: dict) -> str:
    """
    Sérialise les fichiers uploadés en base64 dans la session.
    Retourne un conversion_id unique.

    files_dict : { field_name: [ {filename, content_type, data_b64}, ... ] }
    """
    conversion_id = str(uuid.uuid4())
    session['pending_conversion'] = {
        'id': conversion_id,
        'conversion_type': conversion_type,
        'form_data': form_data,
        'files': files_dict,
        'created_at': datetime.now().isoformat(),
    }
    session.modified = True
    return conversion_id


def load_pending_request(conversion_id: str) -> dict | None:
    """
    Charge et supprime la requête en attente de la session.
    Retourne None si non trouvée ou ID ne correspond pas.
    """
    pending = session.get('pending_conversion')
    if not pending or pending.get('id') != conversion_id:
        return None
    # On consomme la requête
    session.pop('pending_conversion', None)
    session.modified = True
    return pending


def serialize_files(request_files) -> dict:
    """
    Lit tous les fichiers de la requête Flask et les encode en base64.
    Retourne un dict { field_name: [ {filename, content_type, data_b64}, ... ] }
    """
    result = {}
    for field_name in request_files:
        file_list = request_files.getlist(field_name)
        serialized = []
        for f in file_list:
            if not f or not f.filename:
                continue
            f.stream.seek(0)
            raw = f.stream.read()
            serialized.append({
                'filename': f.filename,
                'content_type': f.content_type or 'application/octet-stream',
                'data_b64': base64.b64encode(raw).decode('utf-8'),
            })
        if serialized:
            result[field_name] = serialized
    return result


def deserialize_files(files_dict: dict) -> dict:
    """
    Reconstruit des objets fichier-like à partir du dict sérialisé.
    Retourne un dict { field_name: [ FileProxy, ... ] }
    """
    from io import BytesIO

    class FileProxy:
        """Simule un FileStorage Werkzeug minimal."""
        def __init__(self, filename, content_type, data: bytes):
            self.filename = filename
            self.content_type = content_type
            self._data = data
            self.stream = BytesIO(data)

        def read(self) -> bytes:
            self.stream.seek(0)
            return self.stream.read()

        def seek(self, pos: int):
            self.stream.seek(pos)

        def save(self, dst):
            import shutil
            self.stream.seek(0)
            if hasattr(dst, 'write'):
                shutil.copyfileobj(self.stream, dst)
            else:
                with open(dst, 'wb') as fh:
                    shutil.copyfileobj(self.stream, fh)

    result = {}
    for field_name, file_list in files_dict.items():
        proxies = []
        for item in file_list:
            raw = base64.b64decode(item['data_b64'])
            proxies.append(FileProxy(item['filename'], item['content_type'], raw))
        result[field_name] = proxies
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@monetization_bp.route('/ad-gate/<conversion_id>')
def ad_gate(conversion_id: str):
    """Page interstitielle affichant la publicité."""
    pending = session.get('pending_conversion')
    if not pending or pending.get('id') != conversion_id:
        flash("Session expirée, veuillez recommencer.", "warning")
        return redirect(url_for('conversion.index'))

    conversion_type = pending.get('conversion_type', '')
    return render_template(
        'monetization/ad_gate.html',
        conversion_id=conversion_id,
        conversion_type=conversion_type,
    )


@monetization_bp.route('/api/ad-complete', methods=['POST'])
def ad_complete():
    """
    Appelé en AJAX par le template quand la pub est terminée.
    Marque la session et renvoie l'URL de reprise.
    """
    data = request.get_json(silent=True) or {}
    conversion_id = data.get('conversion_id')

    pending = session.get('pending_conversion')
    if not pending or pending.get('id') != conversion_id:
        return jsonify({'success': False, 'error': 'Session invalide'}), 400

    mark_ad_completed()

    resume_url = url_for(
        'monetization.resume_conversion',
        conversion_id=conversion_id
    )
    return jsonify({'success': True, 'resume_url': resume_url})


@monetization_bp.route('/resume/<conversion_id>')
def resume_conversion(conversion_id: str):
    """
    Reprend la conversion après visionnage de la pub.
    Reconstruit les fichiers depuis la session et délègue à conversion.py.
    """
    if not ad_is_valid():
        flash("Session publicitaire invalide ou expirée.", "warning")
        return redirect(url_for('conversion.index'))

    pending = load_pending_request(conversion_id)
    if not pending:
        flash("Données de conversion introuvables, veuillez recommencer.", "error")
        return redirect(url_for('conversion.index'))

    conversion_type = pending['conversion_type']
    form_data = pending.get('form_data', {})
    files_dict = pending.get('files', {})

    # Reconstruire les fichiers
    restored_files = deserialize_files(files_dict)

    # Importer process_conversion depuis conversion.py et l'appeler directement
    from blueprints.conversion import process_conversion, CONVERSION_MAP

    config = CONVERSION_MAP.get(conversion_type, {})
    if not config:
        flash(f"Type de conversion inconnu : {conversion_type}", "error")
        return redirect(url_for('conversion.index'))

    # Déterminer file / files selon max_files
    if config.get('max_files', 1) > 1:
        # Chercher 'files' puis 'file'
        files = restored_files.get('files') or restored_files.get('file') or []
        result = process_conversion(conversion_type, files=files, form_data=form_data)
    else:
        file_list = restored_files.get('file') or restored_files.get('files') or []
        file = file_list[0] if file_list else None
        if not file:
            flash("Fichier manquant.", "error")
            return redirect(url_for('conversion.index'))
        result = process_conversion(conversion_type, file=file, form_data=form_data)

    if isinstance(result, dict) and 'error' in result:
        flash(result['error'], 'error')
        return redirect(url_for('conversion.universal_converter',
                                conversion_type=conversion_type))

    return result


@monetization_bp.route('/api/status')
def ad_status():
    """Renvoie le statut de la session publicitaire (utile pour debug/front)."""
    valid = ad_is_valid()
    expires_at = session.get('ad_expires_at')
    remaining = None
    if expires_at:
        try:
            delta = datetime.fromisoformat(expires_at) - datetime.now()
            remaining = max(0, int(delta.total_seconds()))
        except Exception:
            pass

    return jsonify({
        'ad_valid': valid,
        'expires_at': expires_at,
        'remaining_seconds': remaining,
    })