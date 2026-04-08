# blueprints/monetization.py
"""
Module de monétisation — Gestion des publicités et du système de grâce (ad-gate)
"""

from flask import (
    Blueprint, session, jsonify, request,
    render_template, redirect, url_for, flash, current_app
)

import uuid
import random
import base64
from datetime import datetime, timedelta
import logging
import tempfile
import os
import time
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

# ✅ CORRECTION : Ne PAS ajouter url_prefix ici (il sera ajouté lors de l'enregistrement dans app.py)
monetization_bp = Blueprint('monetization', __name__)

# Répertoire temporaire pour les fichiers en attente de conversion
UPLOAD_TMP_DIR = os.path.join(tempfile.gettempdir(), "myapp_uploads")
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers session & Publicité
# ---------------------------------------------------------------------------

def _get_random_grace_seconds() -> int:
    """Génère une durée aléatoire entre 15 et 20 minutes (900s à 1200s)."""
    return random.randint(15 * 60, 20 * 60)


def ad_is_valid() -> bool:
    """Vérifie si la publicité a été complétée et si le délai de grâce n'est pas expiré."""
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
    """Marque la publicité comme complétée et définit le prochain délai d'expiration."""
    grace = _get_random_grace_seconds()
    now = datetime.now()
    expires_at = now + timedelta(seconds=grace)

    session['ad_completed'] = True
    session['ad_completed_at'] = now.isoformat()
    session['ad_expires_at'] = expires_at.isoformat()
    session['ad_grace_seconds'] = grace
    session.modified = True

    logger.info(f"[Ad] Publicité complétée. Prochaine pub dans {grace // 60} minutes ({grace}s).")


# ---------------------------------------------------------------------------
# Gestion des requêtes en attente (Persistance pendant la pub)
# ---------------------------------------------------------------------------

def save_pending_request(conversion_type: str, form_data: dict, request_files) -> str:
    """
    Sauvegarde temporairement les fichiers et les données du formulaire sur le disque
    pendant que l'utilisateur regarde la publicité.
    """
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

            # Validation basique de l'extension
            if allowed_extensions and ext not in allowed_extensions:
                logger.warning(f"[{conversion_type}] Fichier refusé: {filename}")
                continue

            # Création d'un fichier temporaire sécurisé sur disque
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

    # Stockage des métadonnées en session
    session['pending_conversion'] = {
        'id': conversion_id,
        'conversion_type': conversion_type,
        'form_data': form_data,
        'files': saved_files,
        'timestamp': time.time()
    }

    session.modified = True
    return conversion_id


def load_pending_request(conversion_id: str) -> dict | None:
    """Récupère et supprime la requête en attente de la session."""
    pending = session.get('pending_conversion')
    if not pending or pending.get('id') != conversion_id:
        return None
    # NE PAS retirer de la session ici, attendre que la conversion réussisse
    # session.pop('pending_conversion', None)  ← à supprimer
    return pending


def serialize_files_to_base64(request_files) -> dict:
    """
    Alternative : Encode les fichiers directement en base64 pour la session.
    Attention : Peut saturer la taille des cookies de session si les fichiers sont gros.
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


# ---------------------------------------------------------------------------
# Restauration et Nettoyage
# ---------------------------------------------------------------------------

def restore_files_from_paths(files_dict: dict):
    """Ouvre les fichiers temporaires et les transforme en objets FileStorage pour Flask."""
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


def cleanup_old_tmp_files(max_age_minutes=60):
    """Supprime les fichiers temporaires orphelins de plus d'une heure."""
    now = time.time()
    if not os.path.exists(UPLOAD_TMP_DIR):
        return

    for f in os.listdir(UPLOAD_TMP_DIR):
        path = os.path.join(UPLOAD_TMP_DIR, f)
        if os.path.isfile(path):
            if now - os.path.getmtime(path) > max_age_minutes * 60:
                try:
                    os.remove(path)
                    logger.debug(f"Nettoyage fichier temporaire : {f}")
                except Exception as e:
                    logger.error(f"Erreur nettoyage {f}: {e}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@monetization_bp.route('/ad-gate/<conversion_id>')
def ad_gate(conversion_id):
    """Affiche la page de publicité avant de procéder à la conversion."""
    pending = session.get('pending_conversion')
    
    if not pending or pending.get('id') != conversion_id:
        flash("Votre session de conversion a expiré ou est invalide.", "warning")
        return redirect(url_for('conversion.index'))
    
    # Durée de la pub (15 secondes)
    ad_duration = 15
    
    return render_template(
        'monetization/ad_gate.html',
        conversion_id=conversion_id,
        conversion_type=pending.get('conversion_type'),
        ad_duration=ad_duration
    )


@monetization_bp.route('/api/ad-complete', methods=['POST'])
def ad_complete():
    """Appelé par le JavaScript de la page de pub quand elle est terminée."""
    data = request.get_json(silent=True) or {}
    conversion_id = data.get('conversion_id')

    pending = session.get('pending_conversion')

    if not pending or pending.get('id') != conversion_id:
        return jsonify({'success': False, 'error': 'ID de conversion invalide'}), 400

    mark_ad_completed()

    return jsonify({
        'success': True,
        'resume_url': url_for('monetization.resume_conversion', conversion_id=conversion_id)
    })


@monetization_bp.route('/resume/<conversion_id>')
def resume_conversion(conversion_id):
    """Reprend le processus de conversion après la publicité."""
    if not ad_is_valid():
        flash("Veuillez d'abord visionner la publicité.", "warning")
        return redirect(url_for('conversion.index'))

    pending = load_pending_request(conversion_id)

    if not pending:
        flash("Données de conversion introuvables. Veuillez réessayer.", "error")
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

        # Logique de traitement selon le nombre de fichiers attendus
        if config.get('max_files', 1) > 1:
            files = restored_files.get('files') or restored_files.get('file') or []
            result = process_conversion(conversion_type, files=files, form_data=form_data)
        else:
            file_list = restored_files.get('file') or restored_files.get('files') or []
            file = file_list[0] if file_list else None

            if not file:
                flash("Le fichier à convertir est introuvable.", "error")
                return redirect(url_for('conversion.index'))

            result = process_conversion(conversion_type, file=file, form_data=form_data)
            if not (isinstance(result, dict) and 'error' in result):
                session.pop('pending_conversion', None)  # succès → nettoyer
                session.modified = True

        # Gestion des erreurs de conversion
        if isinstance(result, dict) and 'error' in result:
            flash(result['error'], 'error')
            return redirect(url_for('conversion.universal_converter', conversion_type=conversion_type))

        return result

    except Exception as e:
        logger.error(f"Erreur lors de la reprise de conversion : {e}")
        flash("Une erreur technique est survenue lors du traitement.", "error")
        return redirect(url_for('conversion.index'))

    finally:
        # 1. Fermeture impérative des flux de fichiers
        for f in opened_files:
            try:
                f.close()
            except:
                pass

        # 2. Suppression immédiate des fichiers temporaires après usage
        for field_files in files_dict.values():
            for f in field_files:
                path = f.get('path')
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le fichier temporaire {path}: {e}")


@monetization_bp.route('/api/status')
def ad_status():
    """Retourne l'état actuel de la publicité pour le client (JS)."""
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
