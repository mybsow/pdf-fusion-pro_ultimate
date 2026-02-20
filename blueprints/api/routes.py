"""
Routes API pour les opérations PDF
"""

from flask import Blueprint, request, jsonify, current_app, request, jsonify
from flask_babel import gettext as _
from pathlib import Path
import json
import os
from datetime import datetime
import base64
from . import api_bp
from blueprints.pdf.engine import PDFEngine
from config import AppConfig
from managers import stats_manager
from managers.stats_manager import StatisticsManager  # Importez l'instance
from managers.rating_manager import RatingManager
from managers.contact_manager import ContactManager

contact_manager = ContactManager()
rating_manager = RatingManager()
stats_manager = StatisticsManager()


api_bp = Blueprint("api_bp", __name__)

# ============================
# UTILITAIRES
# ============================
def get_locale_from_request():
    """
    Récupère la langue pour l'API.
    Priorité : paramètre GET/POST ?lang=fr|en
    Sinon défaut fr
    """
    lang = request.args.get("lang") or request.form.get("lang")
    if lang in ["fr", "en"]:
        return lang
    return "fr"

def translate(text):
    """
    Traduction selon le paramètre lang.
    """
    lang = get_locale_from_request()
    # Flask-Babel utilise current_app et le context, mais ici on peut forcer si besoin
    # Sinon, on retourne juste text pour éviter de toucher à session
    try:
        return _(text)
    except Exception:
        return text

# ============================
# ENDPOINT EXEMPLE - RATING
# ============================
@api_bp.route("/rating", methods=["POST"])
def api_rating():
    """
    Enregistre une note utilisateur (1-5) et un feedback.
    JSON attendu: { "rating": 3, "feedback": "texte optionnel" }
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": translate("Données manquantes")}), 400
        
        rating = data.get("rating", 0)
        feedback = data.get("feedback", "").strip()
        page = data.get("page", "unknown")
        
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            return jsonify({"error": translate("Note invalide (1-5)")}), 400
        
        stats_manager.increment("ratings")
        stats_manager.increment(f"rating_{rating}")

        if feedback:
            try:
                ratings_file = Path(__file__).parent.parent / 'data' / 'ratings.json'
                ratings_file.parent.mkdir(parents=True, exist_ok=True)
                
                ratings = []
                if ratings_file.exists():
                    ratings = json.loads(ratings_file.read_text())
                
                ratings.append({
                    "timestamp": datetime.now().isoformat(),
                    "rating": rating,
                    "feedback": feedback,
                    "page": page,
                    "ip": request.remote_addr[:15] if request.remote_addr else "unknown"
                })
                # Conserver seulement les 1000 derniers
                ratings = ratings[-1000:]
                ratings_file.write_text(json.dumps(ratings, indent=2))
            except Exception as e:
                current_app.logger.error(f"Erreur sauvegarde rating: {e}")

        return jsonify({
            "success": True,
            "message": translate("Merci pour votre évaluation !"),
            "rating": rating
        })

    except Exception:
        current_app.logger.exception("Erreur API rating")
        return jsonify({"error": translate("Erreur interne serveur")}), 500

# ============================
# EXEMPLE ENDPOINT HEALTH
# ============================
@api_bp.route("/health", methods=["GET"])
def api_health():
    """
    Endpoint santé API
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_operations": stats_manager.get_stat("total_operations", 0),
        "ratings": stats_manager.get_stat("ratings", 0)
    })

# ============================
# AUTRES ENDPOINTS JSON
# ============================
# Exemple : traduction rapide
@api_bp.route("/translate", methods=["GET"])
def api_translate():
    """
    Test traduction via paramètre ?word=...
    """
    word = request.args.get("word", "")
    if not word:
        return jsonify({"error": translate("Mot manquant")}), 400

    translations = {}
    for lang in ["fr", "en"]:
        translations[lang] = _(word)
    
    return jsonify({
        "word": word,
        "translations": translations,
        "requested_lang": get_locale_from_request()
    })


@api_bp.route('/preview', methods=["POST"])
def api_preview():
    """API pour générer des aperçus de PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        # Génération des aperçus
        previews, total_pages = PDFEngine.preview(pdf_bytes)
        stats_manager.increment("previews")
        
        return jsonify({
            "success": True,
            "previews": previews,
            "total_pages": total_pages
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur interne du serveur"}), 500
