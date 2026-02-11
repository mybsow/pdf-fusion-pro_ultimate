"""
Routes pour les outils PDF
Version ultra robuste production
"""

import io
from datetime import datetime

from flask import (
    Blueprint,
    request,
    jsonify,
    send_file,
    current_app
)

from pathlib import Path
import uuid
from config import AppConfig
from pypdf import PdfReader, PdfWriter

from managers import stats_manager
from . import pdf_bp
from .engine import PDFEngine
from .file_manager import TempFileManager

# Initialiser dossier temporaire dès le démarrage
AppConfig.initialize()

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')

# -------------------------------
# Helper fichier temporaire
# -------------------------------
def save_temp_file(file, subfolder="general"):
    if file.filename == "":
        raise ValueError("Fichier invalide")
    
    temp_dir = AppConfig.get_conversion_temp_dir(subfolder)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    path = temp_dir / filename
    file.save(path)
    
    if path.stat().st_size == 0:
        path.unlink()
        raise ValueError("Fichier vide")
    
    return path


def cleanup_files(paths):
    for p in paths:
        try:
            if Path(p).exists():
                Path(p).unlink()
        except Exception:
            pass



# ==========================================
# LECTURE SÉCURISÉE DES FICHIERS
# ==========================================

def read_uploaded_pdf(file):
    """
    Lecture sécurisée d'un PDF uploadé.
    Protège contre :
    - stream déjà lu
    - fichiers vides
    - faux PDF
    """

    if not file or file.filename == "":
        raise ValueError("Fichier invalide")

    if not file.filename.lower().endswith(".pdf"):
        raise ValueError(f"{file.filename} n'est pas un PDF")

    # ⭐ CRITIQUE : reset du stream
    file.stream.seek(0)
    data = file.read()

    if not data:
        raise ValueError(f"{file.filename} est vide")

    # Vérifie la signature PDF
    if not data.startswith(b"%PDF"):
        raise ValueError(f"{file.filename} est corrompu ou non-PDF")

    return data


# ==========================================
# MERGE
# ==========================================

@pdf_bp.route("/merge", methods=["POST"])
def merge_pdf():
    temp_paths = []

    try:
        if "files" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400

        files = request.files.getlist("files")

        if len(files) > AppConfig.MAX_FILES_PER_CONVERSION:
            return jsonify({"error": f"Maximum {AppConfig.MAX_FILES_PER_CONVERSION} fichiers"}), 400

        # Sauvegarder les fichiers sur disque
        for f in files:
            path = save_temp_file(f, "pdf")
            temp_paths.append(path)

        # Merge PDF disque → disque
        writer = PdfWriter()
        total_pages = 0

        for path in temp_paths:
            reader = PdfReader(str(path), strict=False)
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1

        output_path = AppConfig.get_conversion_temp_dir("pdf") / f"{uuid.uuid4()}_merged.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)

        temp_paths.append(output_path)

        return send_file(
            output_path,
            as_attachment=True,
            download_name="fusion.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        current_app.logger.exception("Merge PDF échoué")
        return jsonify({"error": str(e)}), 500

    finally:
        cleanup_files(temp_paths)


# -------------------------------
# Route OCR image → texte
# -------------------------------
@pdf_bp.route("/ocr", methods=["POST"])
def ocr_image():
    import pytesseract # type: ignore
    from PIL import Image

    temp_paths = []

    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400

        file = request.files["file"]
        path = save_temp_file(file, "images")
        temp_paths.append(path)

        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang=AppConfig.OCR_DEFAULT_LANGUAGE, config=AppConfig.OCR_CONFIG)

        return jsonify({"text": text})

    except Exception as e:
        current_app.logger.exception("OCR échoué")
        return jsonify({"error": str(e)}), 500

    finally:
        cleanup_files(temp_paths)


# ==========================================
# SPLIT
# ==========================================

@pdf_bp.route("/split", methods=["POST"])
def handle_split():
    try:

        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400

        file = request.files["file"]

        try:
            pdf_bytes = read_uploaded_pdf(file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        mode = request.form.get("mode", "all")
        arg = request.form.get("pages", "")

        output_files = PDFEngine.split(pdf_bytes, mode, arg)

        if not output_files:
            return jsonify({"error": "Aucune page générée"}), 400

        # Si plusieurs fichiers → ZIP
        if len(output_files) > 1:

            zip_bytes, zip_name = PDFEngine.create_zip(output_files)

            return send_file(
                io.BytesIO(zip_bytes),
                as_attachment=True,
                download_name=zip_name,
                mimetype="application/zip"
            )

        # Sinon un seul PDF
        return send_file(
            io.BytesIO(output_files[0]),
            as_attachment=True,
            download_name=f"split_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf"
        )

    except Exception:
        current_app.logger.exception("Crash /split")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ==========================================
# ROTATE
# ==========================================

@pdf_bp.route("/rotate", methods=["POST"])
def handle_rotate():
    try:

        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400

        file = request.files["file"]

        try:
            pdf_bytes = read_uploaded_pdf(file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        angle = int(request.form.get("angle", 90))
        pages = request.form.get("pages", "all")

        rotated_pdf, total_pages, rotated_count = PDFEngine.rotate(
            pdf_bytes,
            angle,
            pages
        )

        current_app.logger.info(
            f"Rotation PDF — {rotated_count}/{total_pages} pages"
        )

        return send_file(
            io.BytesIO(rotated_pdf),
            as_attachment=True,
            download_name=f"rotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf"
        )

    except Exception:
        current_app.logger.exception("Crash /rotate")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ==========================================
# COMPRESS
# ==========================================

@pdf_bp.route("/compress", methods=["POST"])
def handle_compress():
    try:

        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400

        file = request.files["file"]

        try:
            pdf_bytes = read_uploaded_pdf(file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        compressed_pdf, total_pages = PDFEngine.compress(pdf_bytes)

        current_app.logger.info(
            f"Compression PDF — {total_pages} pages"
        )

        return send_file(
            io.BytesIO(compressed_pdf),
            as_attachment=True,
            download_name=f"compresse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf"
        )

    except Exception:
        current_app.logger.exception("Crash /compress")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ==========================================
# PREVIEW (Base64)
# ==========================================

@pdf_bp.route("/preview", methods=["POST"])
def handle_preview():
    try:

        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier reçu"}), 400

        file = request.files["file"]

        try:
            pdf_bytes = read_uploaded_pdf(file)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        previews, total_pages = PDFEngine.preview(pdf_bytes)

        return jsonify({
            "previews": previews,
            "total_pages": total_pages
        })

    except Exception:
        current_app.logger.exception("Crash /preview")
        return jsonify({"error": "Erreur interne serveur"}), 500


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
