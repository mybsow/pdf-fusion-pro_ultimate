"""
Routes pour les outils PDF
Version ULTRA ROBUSTE — Production Ready
"""

import io
import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import (
    render_template,
    request,
    jsonify,
    send_file,
    after_this_request,
    current_app
)

from config import AppConfig
from pypdf import PdfReader, PdfWriter

from managers import stats_manager
from . import pdf_bp
from .engine import PDFEngine

# Initialiser dossiers
AppConfig.initialize()

# ⭐ limite anti PDF bomb (à ajuster)
MAX_PAGES_PER_FILE = 500


# ============================================================
# HELPERS
# ============================================================

def save_temp_file(file, subfolder="general"):
    """
    Sauvegarde sécurisée sur disque.
    Protège contre :
    - fichiers vides
    - fichiers énormes
    - faux PDF
    """

    if not file or file.filename == "":
        raise ValueError("Fichier invalide")

    temp_dir = AppConfig.get_conversion_temp_dir(subfolder)
    temp_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{Path(file.filename).suffix.lower()}"
    path = temp_dir / filename

    file.save(path)

    size = path.stat().st_size

    if size == 0:
        path.unlink(missing_ok=True)
        raise ValueError("Fichier vide")

    if size > AppConfig.MAX_CONTENT_SIZE:
        path.unlink(missing_ok=True)
        raise ValueError("Fichier trop volumineux")

    return path


def validate_pdf(path: Path):
    """
    Vérifie qu'un fichier est un vrai PDF.
    """
    with open(path, "rb") as f:
        header = f.read(4)

    if header != b"%PDF":
        path.unlink(missing_ok=True)
        raise ValueError("Fichier corrompu ou non-PDF")


def cleanup_files(paths):
    for p in paths:
        try:
            Path(p).unlink(missing_ok=True)
        except Exception:
            pass


# ============================================================
# INDEX
# ============================================================

@pdf_bp.route("/", methods=["GET"])
def pdf_index():
    return render_template("pdf/index.html")


# ==========================================
# LECTURE SÉCURISÉE DES FICHIERS
# ==========================================

def read_uploaded_pdf(file):
    if not file or file.filename == "":
        raise ValueError("Fichier invalide")

    if not file.filename.lower().endswith(".pdf"):
        raise ValueError(f"{file.filename} n'est pas un PDF")

    file.stream.seek(0)
    data = file.read()
    
    if len(data) > AppConfig.MAX_CONTENT_SIZE:
        raise ValueError("Fichier trop volumineux")

    if not data:
        raise ValueError(f"{file.filename} est vide")

    if not data.startswith(b"%PDF"):
        raise ValueError(f"{file.filename} est corrompu ou non-PDF")

    return data


# ============================================================
# MERGE — FULL DISK MODE
# ============================================================

@pdf_bp.route("/merge", methods=["GET", "POST"])
def merge():
    if request.method == "GET":
        return render_template("pdf/merge.html")

    temp_paths = []

    try:
        if "files" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400

        files = request.files.getlist("files")

        if len(files) < 2:
            return jsonify({"error": "Au moins 2 PDF requis"}), 400

        if len(files) > AppConfig.MAX_FILES_PER_CONVERSION:
            return jsonify({"error": f"Maximum {AppConfig.MAX_FILES_PER_CONVERSION} fichiers"}), 400

        writer = PdfWriter()
        total_pages = 0

        for f in files:
            path = save_temp_file(f, "pdf")
            validate_pdf(path)

            temp_paths.append(path)

            reader = PdfReader(str(path), strict=False)
            
            if len(reader.pages) > 500:  # ⭐ limite anti PDF bomb
                raise ValueError(f"Fichier {f.filename} contient trop de pages")

            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1

        output_path = AppConfig.get_conversion_temp_dir("pdf") / f"{uuid.uuid4()}_merged.pdf"

        with open(output_path, "wb") as out:
            writer.write(out)

        temp_paths.append(output_path)

        stats_manager.increment("merges")
        stats_manager.increment("total_operations")

        @after_this_request
        def cleanup(response):
            cleanup_files(temp_paths)
            return response

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf"
        )

    except ValueError as e:
        cleanup_files(temp_paths)
        return jsonify({"error": str(e)}), 400

    except Exception:
        cleanup_files(temp_paths)
        current_app.logger.exception("Merge PDF échoué")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ============================================================
# SPLIT — DISK MODE
# ============================================================

@pdf_bp.route("/split", methods=["GET", "POST"])
def split():
    if request.method == "GET":
        return render_template("pdf/split.html")

    temp_paths = []

    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400

        path = save_temp_file(request.files["file"], "pdf")
        validate_pdf(path)

        temp_paths.append(path)

        reader = PdfReader(str(path), strict=False)
        
        if len(reader.pages) > 500:  # ⭐ limite anti PDF bomb
            raise ValueError("Fichier contient trop de pages")

        output_files = []
        temp_dir = AppConfig.get_conversion_temp_dir("pdf")

        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)

            output_path = temp_dir / f"{uuid.uuid4()}_page_{i+1}.pdf"

            with open(output_path, "wb") as f:
                writer.write(f)

            output_files.append(output_path)
            temp_paths.append(output_path)

        # ZIP si plusieurs
        if len(output_files) > 1:
            zip_bytes, zip_name = PDFEngine.create_zip_from_paths(output_files)

            stats_manager.increment("splits")
            stats_manager.increment("total_operations")

            @after_this_request
            def cleanup(response):
                cleanup_files(temp_paths)
                return response

            return send_file(
                io.BytesIO(zip_bytes),
                as_attachment=True,
                download_name=zip_name,
                mimetype="application/zip"
            )

        # Sinon un seul
        @after_this_request
        def cleanup(response):
            cleanup_files(temp_paths)
            return response

        return send_file(
            output_files[0],
            as_attachment=True,
            download_name="split.pdf",
            mimetype="application/pdf"
        )

    except ValueError as e:
        cleanup_files(temp_paths)
        return jsonify({"error": str(e)}), 400

    except Exception:
        cleanup_files(temp_paths)
        current_app.logger.exception("Split crash")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ============================================================
# ROTATE — DISK MODE
# ============================================================

@pdf_bp.route("/rotate", methods=["GET", "POST"])
def rotate():
    if request.method == "GET":
        return render_template("pdf/rotate.html")

    temp_paths = []

    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400
            
        path = save_temp_file(request.files["file"], "pdf")
        validate_pdf(path)

        temp_paths.append(path)

        angle = int(request.form.get("angle", 90))

        reader = PdfReader(str(path), strict=False)
        
        if len(reader.pages) > 500:  # ⭐ limite anti PDF bomb
            raise ValueError("Fichier contient trop de pages")
        
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)

        output_path = AppConfig.get_conversion_temp_dir("pdf") / f"{uuid.uuid4()}_rotated.pdf"

        with open(output_path, "wb") as f:
            writer.write(f)

        temp_paths.append(output_path)

        stats_manager.increment("rotations")
        stats_manager.increment("total_operations")

        @after_this_request
        def cleanup(response):
            cleanup_files(temp_paths)
            return response

        return send_file(
            output_path,
            as_attachment=True,
            download_name="rotation.pdf",
            mimetype="application/pdf"
        )

    except ValueError as e:
        cleanup_files(temp_paths)
        return jsonify({"error": str(e)}), 400

    except Exception:
        cleanup_files(temp_paths)
        current_app.logger.exception("Rotate crash")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ============================================================
# COMPRESS — SAFE MODE
# ============================================================

@pdf_bp.route("/compress", methods=["GET", "POST"])
def compress():
    if request.method == "GET":
        return render_template("pdf/compress.html")

    temp_paths = []

    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400
            
        path = save_temp_file(request.files["file"], "pdf")
        validate_pdf(path)

        temp_paths.append(path)

        reader = PdfReader(str(path), strict=False)
        
        if len(reader.pages) > 500:  # ⭐ limite anti PDF bomb
            raise ValueError("Fichier contient trop de pages")
        
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.add_metadata(reader.metadata)

        output_path = AppConfig.get_conversion_temp_dir("pdf") / f"{uuid.uuid4()}_compressed.pdf"

        with open(output_path, "wb") as f:
            writer.write(f)

        temp_paths.append(output_path)

        stats_manager.increment("compressions")
        stats_manager.increment("total_operations")

        @after_this_request
        def cleanup(response):
            cleanup_files(temp_paths)
            return response

        return send_file(
            output_path,
            as_attachment=True,
            download_name="compresse.pdf",
            mimetype="application/pdf"
        )

    except ValueError as e:
        cleanup_files(temp_paths)
        return jsonify({"error": str(e)}), 400

    except Exception:
        cleanup_files(temp_paths)
        current_app.logger.exception("Compress crash")
        return jsonify({"error": "Erreur interne serveur"}), 500


# -------------------------------
# OCR image → texte
# -------------------------------
@pdf_bp.route("/ocr", methods=["GET", "POST"])
def ocr_image():

    if request.method == "GET":
        return render_template("pdf/ocr.html")

    import pytesseract
    from PIL import Image

    temp_paths = []

    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400

        file = request.files["file"]

        if not file.filename.lower().endswith(
            ('.png', '.jpg', '.jpeg', '.tiff', '.bmp')
        ):
            return jsonify({"error": "Format non supporté"}), 400

        path = save_temp_file(file, "images")
        temp_paths.append(path)

        img = Image.open(path)

        text = pytesseract.image_to_string(
            img,
            lang=AppConfig.OCR_DEFAULT_LANGUAGE,
            config=AppConfig.OCR_CONFIG
        )

        @after_this_request
        def cleanup(response):
            cleanup_files(temp_paths)
            return response

        return jsonify({
            "success": True,
            "text": text,
            "filename": file.filename
        })

    except pytesseract.TesseractNotFoundError:
        return jsonify({"error": "OCR non disponible"}), 503

    except Exception:
        cleanup_files(temp_paths)
        current_app.logger.exception("OCR échoué")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ============================================================
# PREVIEW PDF — SAFE MODE
# ============================================================
@pdf_bp.route("/preview", methods=["POST"])
def handle_preview():

    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier"}), 400
            
        pdf_bytes = read_uploaded_pdf(request.files["file"])

        previews, total_pages = PDFEngine.preview(pdf_bytes)

        stats_manager.increment("previews")

        return jsonify({
            "success": True,
            "previews": previews,
            "total_pages": total_pages
        })

    except Exception:
        current_app.logger.exception("Crash /preview")
        return jsonify({"error": "Erreur interne serveur"}), 500


# ============================================================
# HEALTH
# ============================================================

@pdf_bp.route('/health')
def health_check():
    """Endpoint de santé de l'application"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "app": AppConfig.NAME,
        "version": AppConfig.VERSION,
        "developer": AppConfig.DEVELOPER_NAME,
        "email": AppConfig.DEVELOPER_EMAIL,
        "hosting": AppConfig.HOSTING,
        "domain": AppConfig.DOMAIN,
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
    """API pour enregistrer les évaluations (POST uniquement)"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Données manquantes"}), 400
        
        rating = data.get("rating", 0)
        feedback = data.get("feedback", "")
        page = data.get("page", "unknown")
        
        # Validation
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"error": "Note invalide (1-5)"}), 400
        
        # Enregistrer dans les statistiques
        stats_manager.increment("ratings")
        stats_manager.increment(f"rating_{rating}")
        
        # Sauvegarder le feedback (optionnel)
        if feedback and feedback.strip():
            try:
                ratings_file = Path(__file__).parent.parent / 'data' / 'ratings.json'
                ratings_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Charger existant
                ratings = []
                if ratings_file.exists():
                    ratings = json.loads(ratings_file.read_text())
                
                # Ajouter nouveau
                ratings.append({
                    "timestamp": datetime.now().isoformat(),
                    "rating": rating,
                    "feedback": feedback.strip(),
                    "page": page,
                    "ip": request.remote_addr[:15] if request.remote_addr else "unknown"
                })
                
                # Garder seulement les 1000 derniers
                ratings = ratings[-1000:]
                
                # Sauvegarder
                ratings_file.write_text(json.dumps(ratings, indent=2))
            except Exception as e:
                current_app.logger.error(f"Erreur sauvegarde rating: {e}")
        
        return jsonify({
            "success": True,
            "message": "Merci pour votre évaluation !",
            "rating": rating
        })
    
    except Exception as e:
        current_app.logger.exception("Erreur API rating")
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
                document.getElementById("ratingPopup").innerHTML = '<div style="text-align:center;padding:20px"><div style="color:#4CAF50;font-size:40px;margin-bottom:15px;">✓</div><h5 style="margin-bottom:10px;">Merci pour votre retour !</h5><p style="color:#666;font-size:0.9rem;">Votre évaluation nous aide à améliorer notre service.</p></div>';
                
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