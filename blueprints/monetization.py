

Commencer l'essai gratuit

Partager
Analyse de l'erreur
L'erreur critique se trouve à la ligne 45 de vos logs :
Plain Text
2026-04-07 14:25:02,057 [ERROR] universal_converter error: name 'base64' is not defined
Cause du problème
Il s'agit d'une erreur Python classique : le module base64 est utilisé dans votre fonction universal_converter sans avoir été importé au préalable. En Python, même les modules de la bibliothèque standard doivent être explicitement importés.
Contexte dans les logs
Le déclenchement de l'erreur correspond à une requête POST /conversion/word-en-pdf (ligne 46), ce qui signifie qu'un utilisateur a tenté de convertir un fichier Word en PDF, et c'est lors de ce traitement que la fonction universal_converter a échoué.
Correction à apporter
Dans le fichier Python contenant la fonction universal_converter (probablement un fichier de routes ou de services), ajoutez l'import manquant en haut du fichier :
Python
import base64
Exemple de code corrigé
Python
import base64  # ← Ajouter cette ligne en haut du fichier

def universal_converter(...):
    # ... votre code utilisant base64
    encoded = base64.b64encode(data)
    # ...
Points à vérifier
Élément
Détail
Fichier concerné
Celui qui contient la fonction universal_converter
Emplacement de l'import
En haut du fichier, avec les autres imports
Module
base64 (bibliothèque standard Python, pas besoin de pip install)
Route affectée
POST /conversion/word-en-pdf
Après avoir ajouté l'import, redéployez votre application sur Render et la conversion Word → PDF devrait fonctionner correctement.
pasted_content_2.txt
Texte · 9.86 KB
voici mon code monetization.py pour afficher la pub toutes les 15 à 20 minutes avant l'utilisation des outils de conversion. Merci de le corriger et l'améliorer:

Lite
Je vais analyser votre fichier monetization.py pour corriger l'erreur d'importation et optimiser la logique d'affichage des publicités.
Lite
J'ai corrigé et amélioré votre fichier monetization.py. Voici les modifications apportées :
🛠 Corrections effectuées
Imports manquants : Ajout de import base64 et import time qui causaient les erreurs NameError.
Gestion des erreurs : Ajout de blocs try/except et de logs plus précis pour éviter les crashs lors du traitement des fichiers ou du nettoyage.
Nettoyage sécurisé : Amélioration de la fonction cleanup_old_tmp_files pour éviter les erreurs si le dossier n'existe pas encore.
🚀 Améliorations de la logique
Intervalle de 15-20 min : La fonction _get_random_grace_seconds a été ajustée pour respecter strictement votre demande (900 à 1200 secondes).
Persistance des données :
Les fichiers sont sauvegardés temporairement sur le disque pendant que l'utilisateur regarde la publicité.
La session ne stocke que les chemins d'accès, ce qui évite de saturer la mémoire ou les cookies de session avec des données binaires lourdes.
Sécurité :
Utilisation de secure_filename pour tous les fichiers sauvegardés.
Suppression immédiate des fichiers temporaires dans le bloc finally après la conversion, qu'elle réussisse ou qu'elle échoue.
Expérience utilisateur : Messages flash plus explicites en cas d'expiration de session ou de fichiers manquants.
Vous pouvez remplacer votre fichier actuel par celui en pièce jointe. N'oubliez pas de redéployer votre application sur Render après la modification.
monetization_corrected.py
Code · 11.67 KB
Voir tous les fichiers de cette tâche
Après analyse, la principale erreur était l'absence d'import `base64` dans `universal_converter`. J'ai corrigé et amélioré `monetization.py`, notamment la gestion des fichiers temporaires, la sécurité, et la logique de session.

Tâche terminée
Comment était ce résultat ?
Suggestions de suivi




monetization_corrected.py
# blueprints/monetization.py

from flask import (
    Blueprint, session, jsonify, request,
    render_template, redirect, url_for, flash, current_app
)

import uuid
import random
import base64  # ✅ Import ajouté pour corriger l'erreur 'base64' is not defined
from datetime import datetime, timedelta
import logging
import tempfile
import os
import time  # ✅ Import ajouté pour corriger l'erreur 'time' is not defined
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

monetization_bp = Blueprint('monetization', __name__, url_prefix='/monetization')

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

    # On retire de la session pour éviter les doubles traitements
    session.pop('pending_conversion', None)
    session.modified = True

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

    return render_template(
        'monetization/ad_gate.html',
        conversion_id=conversion_id,
        conversion_type=pending.get('conversion_type')
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
Manus