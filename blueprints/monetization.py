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
import tempfile
import os
from werkzeug.utils import secure_filename
import tempfile


logger = logging.getLogger(__name__)

monetization_bp = Blueprint('monetization', __name__, url_prefix='/monetization')

UPLOAD_TMP_DIR = os.path.join(tempfile.gettempdir(), "myapp_uploads")
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)

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


def save_pending_request(conversion_type: str, form_data: dict, request_files) -> str:
    from blueprints.conversion import CONVERSION_MAP
    conversion_id = str(uuid.uuid4())

    config = CONVERSION_MAP.get(conversion_type, {})
    accept = config.get('accept', '')

    allowed_extensions = {
        ext.strip().lower()
        for ext in accept.split(',')
        if ext.strip()
    }

    saved_files = {}

    for field_name in request_files:
        file_list = request_files.getlist(field_name)
        paths = []

        for f in file_list:
            if not f or not f.filename:
                continue

            filename = secure_filename(f.filename)
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            # 🔒 validation dynamique basée sur CONVERSION_MAP
            if allowed_extensions and ext not in allowed_extensions:
                logger.warning(f"[{conversion_type}] Fichier refusé: {filename}")
                continue

            tmp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=ext,
                dir=UPLOAD_TMP_DIR
            )
            tmp.close()

            f.save(tmp.name)

            paths.append({
                'path': tmp.name,
                'filename': filename,
                'content_type': f.content_type or 'application/octet-stream'
            })

        if paths:
            saved_files[field_name] = paths

    session['pending_conversion'] = {
        'id': conversion_id,
        'conversion_type': conversion_type,
        'form_data': form_data,
        'files': saved_files,
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


def restore_files_from_paths(files_dict: dict):
    from werkzeug.datastructures import FileStorage

    result = {}
    opened_files = []  # 🔥 track des fichiers ouverts

    for field_name, file_list in files_dict.items():
        restored = []

        for item in file_list:
            path = item.get('path')

            if not path or not os.path.exists(path):
                continue

            f = open(path, 'rb')
            opened_files.append(f)

            restored.append(FileStorage(
                stream=f,
                filename=item.get('filename'),
                content_type=item.get('content_type')
            ))

        if restored:
            result[field_name] = restored

    return result, opened_files

def cleanup_old_tmp_files(max_age_minutes=60):
    now = time.time()
    for f in os.listdir(UPLOAD_TMP_DIR):
        path = os.path.join(UPLOAD_TMP_DIR, f)
        if os.path.isfile(path):
            if now - os.path.getmtime(path) > max_age_minutes * 60:
                try:
                    os.remove(path)
                except:
                    pass

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
    Utilise les fichiers temporaires stockés sur disque.
    """

    import os
    from werkzeug.datastructures import FileStorage

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

    # ------------------------------------------------------------------
    # Reconstruction des fichiers depuis les chemins disque
    # ------------------------------------------------------------------
    restored_files = {}

    for field_name, file_list in files_dict.items():
        restored = []

        for item in file_list:
            path = item.get('path')

            if not path or not os.path.exists(path):
                continue

            f = open(path, 'rb')
            restored.append(FileStorage(
                stream=f,
                filename=item.get('filename'),
                content_type=item.get('content_type')
            ))

        if restored:
            restored_files[field_name] = restored

    # ------------------------------------------------------------------
    # Traitement conversion
    # ------------------------------------------------------------------
    from blueprints.conversion import process_conversion, CONVERSION_MAP

    config = blueprints.conversion.CONVERSION_MAP.get(conversion_type, {})
    if not config:
        flash(f"Type de conversion inconnu : {conversion_type}", "error")
        return redirect(url_for('conversion.index'))

    try:
        # Cas multi fichiers
        if config.get('max_files', 1) > 1:
            files = restored_files.get('files') or restored_files.get('file') or []
            result = process_conversion(conversion_type, files=files, form_data=form_data)

        # Cas fichier unique
        else:
            file_list = restored_files.get('file') or restored_files.get('files') or []
            file = file_list[0] if file_list else None

            if not file:
                flash("Fichier manquant.", "error")
                return redirect(url_for('conversion.index'))

            result = process_conversion(conversion_type, file=file, form_data=form_data)

        # Gestion erreur métier
        if isinstance(result, dict) and 'error' in result:
            flash(result['error'], 'error')
            return redirect(url_for(
                'conversion.universal_converter',
                conversion_type=conversion_type
            ))

        return result

    finally:
        # ------------------------------------------------------------------
        # CLEANUP GARANTI (même si crash)
        # ------------------------------------------------------------------
        for field_files in files_dict.values():
            for f in field_files:
                path = f.get('path')
                if not path:
                    continue

                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    logger.warning(f"Cleanup failed for {path}: {e}")


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