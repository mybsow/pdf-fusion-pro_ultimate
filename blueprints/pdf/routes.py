"""
Routes principales pour les outils PDF (version refactorisée avec templates séparés)
"""

import io
import base64
import zipfile
import os
from datetime import datetime
# AJOUTEZ CES IMPORTS :
from flask import render_template, jsonify, request, redirect, url_for
from . import pdf_bp
from config import AppConfig
from .engine import PDFEngine
from managers.stats_manager import stats_manager
from managers.contact_manager import contact_manager
from managers.rating_manager import rating_manager
from utils.middleware import setup_middleware


# ============================================================
# ROUTES DE PAGES
# ============================================================

@pdf_bp.route('/')
def index():
    """Page d'accueil principale"""
    return render_template(
        'pdf/index.html',
        title="PDF Fusion Pro – Fusionner, Diviser, Tourner, Compresser PDF Gratuit",
        description="Outil PDF en ligne 100% gratuit. Fusionnez plusieurs PDFs en un seul, divisez des PDFs par pages, tournez des pages PDF et compressez des fichiers PDF sans perte de qualité. Aucune inscription requise, traitement sécurisé dans votre navigateur.",
        config=AppConfig,
        current_year=datetime.now().year,
        rating_html=get_rating_html()
    )

@pdf_bp.route('/fusion-pdf')
def merge():
    """Page dédiée à la fusion PDF"""
    return render_template(
        'pdf/merge.html',
        title="Fusionner PDF - Outil gratuit pour combiner des fichiers PDF",
        description="Fusionnez gratuitement plusieurs fichiers PDF en un seul document organisé. Interface intuitive, rapide et sécurisée. Aucune inscription requise.",
        config=AppConfig,
        current_year=datetime.now().year,
        rating_html=get_rating_html()
    )

@pdf_bp.route('/division-pdf')
def split():
    """Page dédiée à la division PDF"""
    return render_template(
        'pdf/split.html',
        title="Diviser PDF - Extraire des pages de fichiers PDF",
        description="Divisez vos fichiers PDF par pages ou plages spécifiques. Téléchargez les pages séparément ou en archive ZIP. Simple et efficace.",
        config=AppConfig,
        current_year=datetime.now().year,
        rating_html=get_rating_html()
    )

@pdf_bp.route('/rotation-pdf')
def rotate():
    """Page dédiée à la rotation PDF"""
    return render_template(
        'pdf/rotate.html',
        title="Tourner PDF - Corriger l'orientation des pages PDF",
        description="Tournez les pages de vos PDFs à 90°, 180° ou 270°. Corrigez l'orientation de documents scannés facilement.",
        config=AppConfig,
        current_year=datetime.now().year,
        rating_html=get_rating_html()
    )

@pdf_bp.route('/compression-pdf')
def compress():
    """Page dédiée à la compression PDF"""
    return render_template(
        'pdf/compress.html',
        title="Compresser PDF - Réduire la taille des fichiers PDF",
        description="Compressez vos fichiers PDF pour réduire leur taille sans perte de qualité notable. Optimisez l'espace de stockage et le partage.",
        config=AppConfig,
        current_year=datetime.now().year,
        rating_html=get_rating_html()
    )

# ============================================================
# ROUTES POST DIRECTES (pour FormData)
# ============================================================

@pdf_bp.route('/merge', methods=['POST'])
def handle_merge():
    """Traitement direct de fusion PDF (FormData)"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"error": "Aucun fichier valide"}), 400
        
        pdfs = []
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                pdfs.append(file.read())
        
        if not pdfs:
            return jsonify({"error": "Aucun PDF valide"}), 400
        
        merged_pdf, page_count = PDFEngine.merge(pdfs)
        stats_manager.increment("merges")
        
        from flask import send_file
        import io
        
        return send_file(
            io.BytesIO(merged_pdf),
            as_attachment=True,
            download_name=f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@pdf_bp.route('/split', methods=['POST'])
def handle_split():
    """Traitement direct de division PDF (FormData)"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        file = request.files['files']
        if not file or file.filename == '':
            return jsonify({"error": "Fichier manquant"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Format non supporté"}), 400
        
        pdf_bytes = file.read()
        pages = request.form.get('pages', 'all')
        
        split_files = PDFEngine.split(pdf_bytes, 'range', pages)
        stats_manager.increment("splits")
        
        # Créer un ZIP avec les fichiers splités
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, pdf_data in enumerate(split_files, 1):
                zip_file.writestr(f"page_{i:03d}.pdf", pdf_data)
        
        zip_buffer.seek(0)
        
        from flask import send_file
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"split_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mimetype='application/zip'
        )
    
    except Exception as e:
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@pdf_bp.route('/rotate', methods=['POST'])
def handle_rotate():
    """Traitement direct de rotation PDF (FormData)"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        file = request.files['files']
        if not file or file.filename == '':
            return jsonify({"error": "Fichier manquant"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Format non supporté"}), 400
        
        pdf_bytes = file.read()
        angle = int(request.form.get('angle', 90))
        pages = request.form.get('pages', 'all')
        
        rotated_pdf, total_pages, rotated_count = PDFEngine.rotate(pdf_bytes, angle, pages)
        stats_manager.increment("rotations")
        
        from flask import send_file
        import io
        
        return send_file(
            io.BytesIO(rotated_pdf),
            as_attachment=True,
            download_name=f"rotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@pdf_bp.route('/compress', methods=['POST'])
def handle_compress():
    """Traitement direct de compression PDF (FormData)"""
    try:
        if 'files' not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        file = request.files['files']
        if not file or file.filename == '':
            return jsonify({"error": "Fichier manquant"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Format non supporté"}), 400
        
        pdf_bytes = file.read()
        compressed_pdf, page_count = PDFEngine.compress(pdf_bytes)
        stats_manager.increment("compressions")
        
        from flask import send_file
        import io
        
        return send_file(
            io.BytesIO(compressed_pdf),
            as_attachment=True,
            download_name=f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500
    

# ============================================================
# ROUTES GET SIMPLIFIÉES (Redirections)
# ============================================================

@pdf_bp.route('/merge', methods=['GET'])
def merge_short():
    """Redirige vers la page complète de fusion PDF"""
    return redirect(url_for('pdf.merge'))

@pdf_bp.route('/split', methods=['GET'])
def split_short():
    """Redirige vers la page complète de division PDF"""
    return redirect(url_for('pdf.split'))

@pdf_bp.route('/rotate', methods=['GET'])
def rotate_short():
    """Redirige vers la page complète de rotation PDF"""
    return redirect(url_for('pdf.rotate'))

@pdf_bp.route('/compress', methods=['GET'])
def compress_short():
    """Redirige vers la page complète de compression PDF"""
    return redirect(url_for('pdf.compress'))

# ============================================================
# API ENDPOINTS
# ============================================================

@pdf_bp.route('/api/merge', methods=["POST"])
def api_merge():
    """API pour fusionner des PDFs"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "files" not in data:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        files_b64 = data["files"]
        if not isinstance(files_b64, list):
            return jsonify({"error": "Format de fichiers invalide"}), 400
        
        pdfs = []
        for file_data in files_b64:
            if "data" in file_data:
                try:
                    pdfs.append(base64.b64decode(file_data["data"]))
                except (base64.binascii.Error, TypeError):
                    return jsonify({"error": "Format Base64 invalide"}), 400
        
        if not pdfs:
            return jsonify({"error": "Aucun PDF valide fourni"}), 400
        
        merged_pdf, page_count = PDFEngine.merge(pdfs)
        stats_manager.increment("merges")
        
        return jsonify({
            "success": True,
            "filename": f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(merged_pdf).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500


@pdf_bp.route('/api/split', methods=["POST"])
def api_split():
    """API pour diviser un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        
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
        return jsonify({"error": "Erreur interne du serveur"}), 500


@pdf_bp.route('/api/split_zip', methods=["POST"])
def api_split_zip():
    """API pour diviser un PDF et retourner un ZIP"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        
        zip_data, zip_name = PDFEngine.create_zip(split_files)
        
        return jsonify({
            "success": True,
            "filename": zip_name,
            "count": len(split_files),
            "data": base64.b64encode(zip_data).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500


@pdf_bp.route('/api/rotate', methods=["POST"])
def api_rotate():
    """API pour tourner les pages d'un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        angle = int(data.get("angle", 90))
        pages = data.get("pages", "all")
        
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
        return jsonify({"error": "Erreur interne du serveur"}), 500


@pdf_bp.route('/api/compress', methods=["POST"])
def api_compress():
    """API pour compresser un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        compressed_pdf, page_count = PDFEngine.compress(pdf_bytes)
        stats_manager.increment("compressions")
        
        return jsonify({
            "success": True,
            "filename": f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(compressed_pdf).decode()
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500


@pdf_bp.route('/api/preview', methods=["POST"])
def api_preview():
    """API pour générer des aperçus de PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        previews, total_pages = PDFEngine.preview(pdf_bytes)
        stats_manager.increment("previews")
        
        return jsonify({
            "success": True,
            "previews": previews,
            "total_pages": total_pages
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500


@pdf_bp.route('/health')
def health_check():
    """Endpoint de santé de l'application"""
    return jsonify({
        "status": "healthy",
        "app": AppConfig.NAME,
        "version": AppConfig.VERSION,
        "developer": AppConfig.DEVELOPER_NAME,
        "email": AppConfig.DEVELOPER_EMAIL,
        "hosting": AppConfig.HOSTING,
        "domain": AppConfig.DOMAIN,
        "timestamp": datetime.now().isoformat(),
        "total_operations": stats_manager.get_stat("total_operations", 0),
        "merges": stats_manager.get_stat("merges", 0),
        "splits": stats_manager.get_stat("splits", 0),
        "rotations": stats_manager.get_stat("rotations", 0),
        "compressions": stats_manager.get_stat("compressions", 0),
        "conversions": stats_manager.get_stat("conversions", 0),
        "previews": stats_manager.get_stat("previews", 0),
        "user_sessions": stats_manager.get_stat("user_sessions", 0)
    })


@pdf_bp.route('/api/rating', methods=["POST"])
def api_rating():
    """API pour enregistrer les évaluations"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        rating = data.get("rating", 0)
        feedback = data.get("feedback", "")
        
        # Enregistrer dans les statistiques
        stats_manager.increment("ratings")
        
        return jsonify({
            "success": True,
            "message": "Évaluation enregistrée",
            "rating": rating
        })
    
    except Exception as e:
        return jsonify({"error": "Erreur interne du serveur"}), 500


# ============================================================
# UTILITAIRES
# ============================================================
def get_rating_html():
    """Génère le HTML pour le système d'évaluation"""
    return '''
    <!-- Système d'évaluation -->
    <div id="ratingPopup" style="display:none;position:fixed;bottom:20px;right:20px;background:white;border-radius:12px;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,0.15);z-index:9999;width:300px;max-width:90%;">
        <div style="position:relative">
            <button onclick="closeRatingPopup()" style="position:absolute;top:5px;right:5px;background:none;border:none;font-size:20px;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;" aria-label="Fermer">&times;</button>
            
            <!-- Message d'invitation -->
            <div id="ratingInvitation" style="text-align:center;">
                <div style="font-size:32px;margin-bottom:10px;">★</div>
                <h5 style="margin-bottom:8px;font-size:1.1rem;">Votre avis compte !</h5>
                <p style="font-size:0.9rem;color:#666;margin-bottom:15px;line-height:1.4;">
                    Comment évaluez-vous votre expérience avec notre outil PDF ?
                </p>
            </div>
            
            <!-- Étoiles -->
            <div style="font-size:24px;margin-bottom:15px;text-align:center;" id="starsContainer">
                <span style="cursor:pointer" onmouseover="highlightStars(1)" onclick="rate(1)" aria-label="1 étoile">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(2)" onclick="rate(2)" aria-label="2 étoiles">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(3)" onclick="rate(3)" aria-label="3 étoiles">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(4)" onclick="rate(4)" aria-label="4 étoiles">☆</span>
                <span style="cursor:pointer" onmouseover="highlightStars(5)" onclick="rate(5)" aria-label="5 étoiles">☆</span>
            </div>
            
            <!-- Section feedback (cachée au début) -->
            <div id="feedbackSection" style="display:none">
                <p style="font-size:0.9rem;color:#666;margin-bottom:10px;">
                    Merci ! Avez-vous des suggestions d'amélioration ?
                </p>
                <textarea id="feedback" placeholder="Vos commentaires (optionnel)" style="width:100%;margin-bottom:10px;padding:8px;border-radius:6px;border:1px solid #ddd;font-size:14px;min-height:60px;" rows="2"></textarea>
                <button onclick="submitRating()" style="background:#4361ee;color:white;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;width:100%;font-size:14px;">Envoyer mon évaluation</button>
            </div>
            
            <!-- Bouton pour refuser poliment -->
            <div id="skipSection" style="text-align:center;margin-top:10px;">
                <button onclick="skipRating()" style="background:none;border:none;color:#888;font-size:0.85rem;cursor:pointer;text-decoration:underline;">
                    Peut-être plus tard
                </button>
            </div>
        </div>
    </div>
    
    <!-- Bouton déclencheur -->
    <div id="ratingTrigger" style="position:fixed;bottom:20px;right:20px;background:#4361ee;color:white;width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:9998;box-shadow:0 4px 12px rgba(67,97,238,0.3);" onclick="showRating()" aria-label="Évaluer l\'application" title="Donnez votre avis">
        ★
        <div style="position:absolute;top:-5px;right:-5px;background:#ff4757;color:white;font-size:0.7rem;width:18px;height:18px;border-radius:50%;display:flex;align-items:center;justify-content:center;">
            !
        </div>
    </div>
    
    <script>
    let selectedRating = 0;
    
    function showRating() {
        document.getElementById("ratingPopup").style.display = "block";
        document.getElementById("ratingTrigger").style.display = "none";
        resetRatingPopup();
    }
    
    function resetRatingPopup() {
        const stars = document.querySelectorAll("#starsContainer span");
        stars.forEach(star => {
            star.textContent = "☆";
            star.style.color = "#ccc";
        });
        
        document.getElementById("ratingInvitation").style.display = "block";
        document.getElementById("feedbackSection").style.display = "none";
        document.getElementById("skipSection").style.display = "block";
        document.getElementById("feedback").value = "";
        selectedRating = 0;
    }
    
    function closeRatingPopup() {
        document.getElementById("ratingPopup").style.display = "none";
        document.getElementById("ratingTrigger").style.display = "flex";
    }
    
    function highlightStars(num) {
        const stars = document.querySelectorAll("#starsContainer span");
        stars.forEach((star, index) => {
            star.textContent = index < num ? "★" : "☆";
            star.style.color = index < num ? "#ffc107" : "#ccc";
        });
    }
    
    function rate(num) {
        selectedRating = num;
        highlightStars(num);
        
        document.getElementById("ratingInvitation").style.display = "none";
        document.getElementById("feedbackSection").style.display = "block";
        document.getElementById("skipSection").style.display = "none";
        
        setTimeout(() => {
            document.getElementById("feedback").focus();
        }, 100);
    }
    
    function skipRating() {
        closeRatingPopup();
        const date = new Date();
        date.setDate(date.getDate() + 7);
        localStorage.setItem("ratingSkippedUntil", date.toISOString());
    }
    
    function submitRating() {
        const feedback = document.getElementById("feedback").value;
        
        fetch("/api/rating", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({rating: selectedRating, feedback: feedback, page: window.location.pathname})
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                document.getElementById("ratingPopup").innerHTML = \'<div style="text-align:center;padding:20px"><div style="color:#4CAF50;font-size:40px;margin-bottom:15px;">✓</div><h5 style="margin-bottom:10px;">Merci pour votre retour !</h5><p style="color:#666;font-size:0.9rem;">Votre évaluation nous aide à améliorer notre service.</p></div>\';
                
                localStorage.setItem("hasRated", "true");
                
                setTimeout(() => {
                    closeRatingPopup();
                }, 3000);
            }
        })
        .catch(error => {
            console.error("Erreur:", error);
            alert("Une erreur est survenue. Veuillez réessayer.");
        });
    }
    
    function shouldShowRating() {
        if (localStorage.getItem("hasRated")) {
            return false;
        }
        
        const skippedUntil = localStorage.getItem("ratingSkippedUntil");
        if (skippedUntil) {
            const skipDate = new Date(skippedUntil);
            if (new Date() < skipDate) {
                return false;
            }
        }
        
        return true;
    }
    
    setTimeout(() => {
        if (shouldShowRating()) {
            showRating();
        }
    }, 30000);
    
    window.showRating = showRating;
    window.closeRatingPopup = closeRatingPopup;
    window.highlightStars = highlightStars;
    window.rate = rate;
    window.submitRating = submitRating;
    window.skipRating = skipRating;
    </script>
    '''
