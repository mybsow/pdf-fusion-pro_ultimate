# blueprints/monetization.py

from flask import (
    Blueprint, session, jsonify, request,
    render_template, redirect, url_for, flash, current_app
)

import uuid
import random
from datetime import datetime, timedelta
import logging
import tempfile
import os
import time  # ❗ manquant
from werkzeug.utils import secure_filename

from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

monetization_bp = Blueprint('monetization', __name__, url_prefix='/monetization')

UPLOAD_TMP_DIR = os.path.join(tempfile.gettempdir(), "myapp_uploads")
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers session
# ---------------------------------------------------------------------------

def _grace_seconds() -> int:
    return random.randint(10 * 60, 20 * 60)


def ad_is_valid() -> bool:
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
    grace = _grace_seconds()
    expires_at = datetime.now() + timedelta(seconds=grace)

    session['ad_completed'] = True
    session['ad_completed_at'] = datetime.now().isoformat()
    session['ad_expires_at'] = expires_at.isoformat()
    session['ad_grace_seconds'] = grace
    session.modified = True

    logger.info(f"[Ad] Pub complétée, grâce = {grace}s")


# ---------------------------------------------------------------------------
# Sauvegarde requête
# ---------------------------------------------------------------------------

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
    pending = session.get('pending_conversion')
    if not pending or pending.get('id') != conversion_id:
        return None

    session.pop('pending_conversion', None)
    session.modified = True

    return pending


# ---------------------------------------------------------------------------
# RESTAURATION FICHIERS
# ---------------------------------------------------------------------------

def restore_files_from_paths(files_dict: dict):
    result = {}
    opened_files = []

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


# ---------------------------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------------------------

def cleanup_old_tmp_files(max_age_minutes=60):
    now = time.time()

    for f in os.listdir(UPLOAD_TMP_DIR):
        path = os.path.join(UPLOAD_TMP_DIR, f)

        if os.path.isfile(path):
            if now - os.path.getmtime(path) > max_age_minutes * 60:
                try:
                    os.remove(path)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@monetization_bp.route('/ad-gate/<conversion_id>')
def ad_gate(conversion_id):
    pending = session.get('pending_conversion')

    if not pending or pending.get('id') != conversion_id:
        flash("Session expirée.", "warning")
        return redirect(url_for('conversion.index'))

    return render_template(
        'monetization/ad_gate.html',
        conversion_id=conversion_id,
        conversion_type=pending.get('conversion_type')
    )


@monetization_bp.route('/api/ad-complete', methods=['POST'])
def ad_complete():
    data = request.get_json(silent=True) or {}
    conversion_id = data.get('conversion_id')

    pending = session.get('pending_conversion')

    if not pending or pending.get('id') != conversion_id:
        return jsonify({'success': False}), 400

    mark_ad_completed()

    return jsonify({
        'success': True,
        'resume_url': url_for('monetization.resume_conversion', conversion_id=conversion_id)
    })


@monetization_bp.route('/resume/<conversion_id>')
def resume_conversion(conversion_id):
    if not ad_is_valid():
        flash("Session expirée.", "warning")
        return redirect(url_for('conversion.index'))

    pending = load_pending_request(conversion_id)

    if not pending:
        flash("Données introuvables.", "error")
        return redirect(url_for('conversion.index'))

    from blueprints.conversion import process_conversion, CONVERSION_MAP

    conversion_type = pending['conversion_type']
    form_data = pending.get('form_data', {})
    files_dict = pending.get('files', {})

    restored_files, opened_files = restore_files_from_paths(files_dict)

    try:
        config = CONVERSION_MAP.get(conversion_type, {})
        if not config:
            flash("Type de conversion inconnu.", "error")
            return redirect(url_for('conversion.index'))

        if config.get('max_files', 1) > 1:
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
            return redirect(url_for('conversion.universal_converter', conversion_type=conversion_type))

        return result

    finally:
        # fermeture fichiers
        for f in opened_files:
            try:
                f.close()
            except:
                pass

        # suppression fichiers temporaires
        for field_files in files_dict.values():
            for f in field_files:
                path = f.get('path')
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.warning(f"Cleanup failed: {e}")


@monetization_bp.route('/api/status')
def ad_status():
    valid = ad_is_valid()
    expires_at = session.get('ad_expires_at')

    remaining = None
    if expires_at:
        try:
            delta = datetime.fromisoformat(expires_at) - datetime.now()
            remaining = max(0, int(delta.total_seconds()))
        except:
            pass

    return jsonify({
        'ad_valid': valid,
        'expires_at': expires_at,
        'remaining_seconds': remaining,
    })