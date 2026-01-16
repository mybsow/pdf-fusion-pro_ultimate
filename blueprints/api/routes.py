"""
Routes API pour les opérations PDF
"""

from flask import request, jsonify
import json
import os
from datetime import datetime
import base64
from . import api_bp
from blueprints.pdf.engine import PDFEngine
from config import AppConfig
from managers.stats_manager import stats_manager  # Importez l'instance
from managers.rating_manager import rating_manager
from managers.contact_manager import contact_manager


@api_bp.route('/merge', methods=["POST"])
def api_merge():
    """API pour fusionner des PDFs"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "files" not in data:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        files_b64 = data["files"]
        if not isinstance(files_b64, list):
            return jsonify({"error": "Format de fichiers invalide"}), 400
        
        # Décodage des PDFs
        pdfs = []
        for file_data in files_b64:
            if "data" in file_data:
                try:
                    pdfs.append(base64.b64decode(file_data["data"]))
                except (base64.binascii.Error, TypeError):
                    return jsonify({"error": "Format Base64 invalide"}), 400
        
        if not pdfs:
            return jsonify({"error": "Aucun PDF valide fourni"}), 400
        
        # Fusion
        merged_pdf, page_count = PDFEngine.merge(pdfs)
        stats_manager.increment("merges")
        
        return jsonify({
            "success": True,
            "filename": f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(merged_pdf).decode()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur interne du serveur"}), 500

@api_bp.route('/split', methods=["POST"])
def api_split():
    """API pour diviser un PDF"""
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
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        # Division
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        
        # Préparation des résultats
        result_files = []
        for i, pdf_data in enumerate(split_files):
            result_files.append({
                "filename": f"split_{i+1:03d}.pdf",
                "data": base64.b64encode(pdf_data).decode()
            })
        
        return jsonify({
            "success": True,
            "count": len(split_files),
            "files": result_files
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur interne du serveur"}), 500

@api_bp.route('/split_zip', methods=["POST"])
def api_split_zip():
    """API pour diviser un PDF et retourner un ZIP"""
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
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        # Division
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        stats_manager.increment("zip_downloads")
        
        # Création du ZIP
        zip_data, zip_name = PDFEngine.create_zip(split_files)
        
        return jsonify({
            "success": True,
            "filename": zip_name,
            "count": len(split_files),
            "data": base64.b64encode(zip_data).decode()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur interne du serveur"}), 500

@api_bp.route('/rotate', methods=["POST"])
def api_rotate():
    """API pour tourner les pages d'un PDF"""
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
        
        angle = int(data.get("angle", 90))
        pages = data.get("pages", "all")
        
        # Rotation
        rotated_pdf, total_pages, rotated_count = PDFEngine.rotate(pdf_bytes, angle, pages)
        stats_manager.increment("rotations")
        
        return jsonify({
            "success": True,
            "filename": f"rotation_{angle}deg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": total_pages,
            "rotated": rotated_count,
            "data": base64.b64encode(rotated_pdf).decode()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur interne du serveur"}), 500

@api_bp.route('/compress', methods=["POST"])
def api_compress():
    """API pour compresser un PDF"""
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
        
        # Compression
        compressed_pdf, page_count = PDFEngine.compress(pdf_bytes)
        stats_manager.increment("compressions")
        
        return jsonify({
            "success": True,
            "filename": f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(compressed_pdf).decode()
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Erreur interne du serveur"}), 500

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

@api_bp.route("/rating", methods=["POST"])
def submit_rating():
    data = request.get_json(silent=True) or {}

    # Validation stricte
    try:
        rating = int(data.get("rating", 0))
        if rating < 1 or rating > 5:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid rating"}), 400

    rating_manager.save_rating({
        "rating": rating,
        "feedback": data.get("feedback", "").strip() or None,
        "page": data.get("page", "/"),
        "user_agent": request.headers.get("User-Agent", ""),
        "ip": request.remote_addr
    })

    return jsonify({"success": True}), 201

