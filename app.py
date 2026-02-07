#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version production ultra-stable (Render / Gunicorn ready)
"""

from flask import Flask, redirect, Response, request, render_template, send_from_directory, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import os
import logging
from pathlib import Path

from config import AppConfig

# Blueprints - IMPORT DEPUIS BLUEPRINTS
from blueprints.pdf import pdf_bp
from blueprints.api import api_bp
from blueprints.stats import stats_bp
from blueprints.admin import admin_bp
from blueprints.conversion import conversion_bp
from blueprints.legal.routes import legal_bp  # IMPORT CORRECT !

# ✅ AJOUTER ICI - Imports OCR conditionnels
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

# ============================================================
# LOGGING PRODUCTION
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

def check_and_create_templates():
    """Vérifie et crée les templates manquants"""
    import os
    from pathlib import Path
    
    required = [
        'conversion/csv_to_excel.html',
        'conversion/excel_to_csv.html',
        'conversion/pdf_to_image.html',
        'conversion/pdf_to_doc.html',
        'conversion/pdf_to_excel.html',
        'conversion/pdf_to_pdf.html',
        'conversion/pdf_to_ppt.html',
        'errors/404.html',
        'errors/500.html'
    ]
    
    for template in required:
        path = Path('templates') / template
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"""<!DOCTYPE html>
<html>
<head><title>{template}</title></head>
<body>
    <h1>{template}</h1>
    <p>Page en développement</p>
    <a href="/">← Retour à l'accueil</a>
</body>
</html>""")
            logger.info(f"✅ Template créé: {template}")


# ============================================================
# INIT DOSSIERS
# ============================================================

def init_app_dirs():
    base_dir = Path(__file__).parent

    dirs = [
        'data/contacts',
        'data/ratings',
        'uploads',
        'temp',
        'logs'
    ]

    for d in dirs:
        path = base_dir / d
        path.mkdir(parents=True, exist_ok=True)

    contacts_file = base_dir / 'data' / 'contacts.json'
    if not contacts_file.exists():
        contacts_file.write_text('[]', encoding='utf-8')


# ============================================================
# FACTORY
# ============================================================

def create_app():
    
    check_and_create_templates()  # <-- AJOUTEZ CETTE LIGNE

    logger.info("🚀 Initialisation Flask...")

    AppConfig.initialize()
    init_app_dirs()

    app = Flask(__name__)
    app.config.from_object(AppConfig)

    # IMPORTANT
    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY",
        AppConfig.SECRET_KEY
    )

    app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # Proxy reverse
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1
    )

    # ========================================================
    # Inject config dans Jinja
    # ========================================================

    @app.context_processor
    def inject_config():
        return dict(config=app.config)

    # ========================================================
    # SECURITY HEADERS
    # ========================================================

    @app.after_request
    def security_headers(response):

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        if not app.debug:
            response.headers["Strict-Transport-Security"] = \
                "max-age=31536000; includeSubDomains"

        if "static" in request.path:
            response.headers["Cache-Control"] = \
                "public, max-age=31536000"

        return response

    # ========================================================
    # FORCE INSTALL OCR (installation manuelle)
    # ========================================================
    
    @app.route('/force-install-ocr')
    def force_install_ocr():
        """Force l'installation des packages OCR"""
        import subprocess
        import sys
        
        try:
            packages = [
                'pytesseract==0.3.10',
                'pdf2image==1.16.3',
                'Pillow==10.0.0',
                'opencv-python-headless==4.8.1.78'
            ]
            
            results = []
            for package in packages:
                try:
                    # Installer avec pip (sans --user sur Render)
                    cmd = [sys.executable, "-m", "pip", "install", package]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        results.append(f"✅ {package} installé")
                    else:
                        results.append(f"❌ {package} erreur: {result.stderr[:200]}")
                        
                except Exception as e:
                    results.append(f"❌ {package} exception: {str(e)}")
            
            # Tester l'import après installation
            test_results = []
            for pkg_name, import_name in [
                ('pytesseract', 'pytesseract'),
                ('pdf2image', 'pdf2image'),
                ('Pillow', 'PIL.Image'),
                ('opencv', 'cv2')
            ]:
                try:
                    if import_name == 'PIL.Image':
                        from PIL import Image
                        test_results.append(f"✅ {pkg_name} importé")
                    else:
                        __import__(import_name.split('.')[0])
                        test_results.append(f"✅ {pkg_name} importé")
                except ImportError as e:
                    test_results.append(f"❌ {pkg_name}: {e}")
            
            return jsonify({
                "status": "installation forcée terminée",
                "installation_results": results,
                "import_tests": test_results,
                "python_path": sys.executable,
                "python_version": sys.version
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ========================================================
    # Managers (safe import)
    # ========================================================

    try:
        from managers.contact_manager import contact_manager
        from managers.stats_manager import stats_manager
        from utils.middleware import setup_middleware

        setup_middleware(app, stats_manager)

        with app.app_context():
            unseen = contact_manager.get_unseen_count()
            logger.info(f"📨 Messages non lus: {unseen}")

    except Exception as e:
        logger.warning(f"Managers non chargés: {e}")

    # ========================================================
    # BLUEPRINTS
    # ========================================================

    blueprints = [
        (pdf_bp, None),
        (api_bp, "/api"),
        (legal_bp, None),          # PAS de préfixe pour les pages légales
        (stats_bp, None),
        (admin_bp, "/admin"),      # Préfixe pour admin
        (conversion_bp, "/conversion")  # Préfixe pour conversion
    ]

    for bp, prefix in blueprints:
        if prefix:
            app.register_blueprint(bp, url_prefix=prefix)
        else:
            app.register_blueprint(bp)

    # ========================================================
    # CORRECTION ROUTE /conversion
    # ========================================================
    # Le blueprint conversion_bp est enregistré avec le préfixe /conversion
    # Cette redirection évite /conversion/conversion/... depuis d'anciens liens
    @app.route('/conversion')
    def redirect_conversion():
        """Redirige /conversion vers /conversion/ (avec slash)"""
        return redirect('/conversion/')

    # ========================================================
    # OCR: DIAGNOSTIC DYNAMIQUE
    # ========================================================

    def _ocr_probe():
        """
        Vérifie dynamiquement l'état de l'OCR
        """
        status = {
            "enabled": bool(AppConfig.OCR_ENABLED),
            "tesseract": None,
            "poppler": None,
            "lang_fra": None,
            "python_packages": {
                "pytesseract": PYTESSERACT_AVAILABLE,
                "Pillow": False,
                "pdf2image": PDF2IMAGE_AVAILABLE,
                "opencv-python": OPENCV_AVAILABLE
            },
            "errors": []
        }
        
        try:
            import shutil
            import subprocess
            
            # Vérifier Pillow
            try:
                from PIL import Image
                status["python_packages"]["Pillow"] = True
            except ImportError:
                status["python_packages"]["Pillow"] = False
            
            # Si l'OCR est désactivé en config, on skip
            if not AppConfig.OCR_ENABLED:
                return status
            
            # Vérifier Tesseract
            tesseract_path = shutil.which("tesseract")
            status["tesseract"] = tesseract_path
            
            # Vérifier Poppler
            status["poppler"] = shutil.which("pdftoppm") or shutil.which("pdftocairo")
            
            # Si Tesseract est disponible, vérifier les langues
            if tesseract_path and PYTESSERACT_AVAILABLE:
                try:
                    # Configurer pytesseract
                    pytesseract.pytesseract.tesseract_cmd = tesseract_path
                    
                    # Test de version
                    version = pytesseract.get_tesseract_version()
                    status["tesseract"] = f"{tesseract_path} (v{version})"
                    
                    # Test des langues
                    langs = pytesseract.get_languages(config='')
                    status["lang_fra"] = "fra" in langs
                    
                except Exception as e:
                    status["errors"].append(f"pytesseract error: {str(e)}")
            else:
                if not tesseract_path:
                    status["errors"].append("tesseract not found in PATH")
                if not PYTESSERACT_AVAILABLE:
                    status["errors"].append("pytesseract Python package not installed")
            
        except Exception as e:
            status["errors"].append(f"OCR probe error: {str(e)}")
        
        return status

    # Log état OCR au démarrage
    _probe = _ocr_probe()
    logger.info(f"OCR activé (config) : {_probe['enabled']}")
    logger.info(f"Tesseract: {_probe['tesseract']} | Poppler: {_probe['poppler']} | fra: {_probe['lang_fra']}")
    if _probe["errors"]:
        logger.warning(f"OCR diagnostics: {_probe['errors']}")

    # ========================================================
    # TEST TESSERACT SIMPLE
    # ========================================================
    
    @app.route('/test-tesseract')
    def test_tesseract():
        """Test simple de Tesseract"""
        try:
            if not PYTESSERACT_AVAILABLE:
                return jsonify({
                    "error": "pytesseract non disponible",
                    "installed": False,
                    "python_packages": {
                        "pytesseract": PYTESSERACT_AVAILABLE,
                        "Pillow": False,
                        "pdf2image": PDF2IMAGE_AVAILABLE,
                        "opencv-python": OPENCV_AVAILABLE
                    }
                }), 500
            
            # Configuration du chemin Tesseract
            tesseract_cmd = '/usr/bin/tesseract'
            if not os.path.exists(tesseract_cmd):
                tesseract_cmd = '/usr/local/bin/tesseract'
            
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            # Test de version
            version = pytesseract.get_tesseract_version()
            
            # Test des langues
            try:
                langs = pytesseract.get_languages(config='')
            except:
                langs = ["non disponible"]
            
            return jsonify({
                "status": "OK",
                "pytesseract_available": True,
                "tesseract_version": str(version),
                "tesseract_path": tesseract_cmd,
                "available_languages": langs,
                "opencv_available": OPENCV_AVAILABLE,
                "pdf2image_available": PDF2IMAGE_AVAILABLE,
                "python_packages": {
                    "pytesseract": PYTESSERACT_AVAILABLE,
                    "Pillow": False,
                    "pdf2image": PDF2IMAGE_AVAILABLE,
                    "opencv-python": OPENCV_AVAILABLE
                }
            })
            
        except Exception as e:
            return jsonify({
                "error": str(e),
                "pytesseract_available": PYTESSERACT_AVAILABLE,
                "opencv_available": OPENCV_AVAILABLE,
                "pdf2image_available": PDF2IMAGE_AVAILABLE,
                "traceback": str(type(e))
            }), 500

    # ========================================================
    # TEST OCR (page de diagnostic amélioré)
    # ========================================================
    
    @app.route('/test-ocr')
    def test_ocr():
        """Page de test pour vérifier l'état de l'OCR"""
        probe = _ocr_probe()
        
        # Vérifier les packages Python
        python_packages = probe["python_packages"]
        
        # Préparer le HTML des erreurs
        errors_html = ""
        if probe["errors"]:
            # Utiliser <br> pour les sauts de ligne HTML
            errors_formatted = "<br>".join(probe["errors"])
            errors_html = f'<h3>⚠️ Erreurs</h3><div class="status warn"><pre>{errors_formatted}</pre></div>'
        
        # HTML de diagnostic
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Diagnostic OCR - PDF Fusion Pro</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .status {{ padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .ok {{ background:#d1fae5; color:#065f46; border:2px solid #10b981; }}
                .warn {{ background:#fef3c7; color:#92400e; border:2px solid #f59e0b; }}
                .err {{ background:#fee2e2; color:#991b1b; border:2px solid #ef4444; }}
                .info {{ background:#dbeafe; color:#1e40af; border:2px solid #3b82f6; }}
                table {{ width:100%; border-collapse:collapse; margin:20px 0; }}
                th, td {{ padding:12px; text-align:left; border-bottom:1px solid #ddd; }}
                th {{ background:#f8fafc; }}
                .badge {{ display:inline-block; padding:4px 8px; border-radius:4px; font-size:12px; }}
                .badge-ok {{ background:#10b981; color:white; }}
                .badge-err {{ background:#ef4444; color:white; }}
                .badge-warn {{ background:#f59e0b; color:white; }}
                .action-buttons {{ margin: 20px 0; }}
                .action-buttons a {{ 
                    display: inline-block; 
                    padding: 10px 20px; 
                    margin: 5px; 
                    background: #3b82f6; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                }}
            </style>
        </head>
        <body>
            <h1>🧪 Diagnostic OCR - PDF Fusion Pro</h1>
            
            <div class="status {'ok' if probe['tesseract'] and probe['poppler'] else 'err'}">
                <h2>{'✅ OCR Opérationnel' if probe['tesseract'] and probe['poppler'] else '❌ OCR Non Opérationnel'}</h2>
                <p>Configuration: {'Activé' if probe['enabled'] else 'Désactivé'}</p>
            </div>
            
            <div class="action-buttons">
                <a href="/force-install-ocr" onclick="return confirm('Installer les packages OCR manuellement? Cette opération peut prendre 30 secondes.')">
                    🔧 FORCER l'installation OCR
                </a>
                <a href="/test-tesseract" target="_blank">
                    🧪 Tester Tesseract API
                </a>
                <a href="/health" target="_blank">
                    📊 Vérifier santé
                </a>
            </div>
            
            <h3>📦 Packages Python</h3>
            <table>
                <tr><th>Package</th><th>Status</th><th>Action</th></tr>
                {"".join([
                    f'<tr><td>{name}</td><td><span class="badge {"badge-ok" if installed else "badge-err"}">{"✅ Installé" if installed else "❌ Manquant"}</span></td><td>{"pip install " + name if not installed else "✓"}</td></tr>'
                    for name, installed in python_packages.items()
                ])}
            </table>
            
            <h3>🖥️ Dépendances Système</h3>
            <table>
                <tr><th>Dépendance</th><th>Status</th><th>Chemin</th></tr>
                <tr><td>Tesseract OCR</td><td><span class="badge {'badge-ok' if probe['tesseract'] else 'badge-err'}">{'✅ Trouvé' if probe['tesseract'] else '❌ Non trouvé'}</span></td><td>{probe['tesseract'] or '—'}</td></tr>
                <tr><td>Poppler (pdf2image)</td><td><span class="badge {'badge-ok' if probe['poppler'] else 'badge-err'}">{'✅ Trouvé' if probe['poppler'] else '❌ Non trouvé'}</span></td><td>{probe['poppler'] or '—'}</td></tr>
                <tr><td>Langue Française</td><td><span class="badge {'badge-ok' if probe['lang_fra'] else 'badge-warn'}">{'✅ Disponible' if probe['lang_fra'] else '⚠️ Manquante'}</span></td><td>{'tesseract-ocr-fra' if probe['lang_fra'] else 'Installer: apt-get install tesseract-ocr-fra'}</td></tr>
            </table>
            
            <h3>🔧 Configuration Render</h3>
            <div class="status info">
                <p><strong>Si OCR ne fonctionne pas:</strong></p>
                <ol>
                    <li>Cliquez sur "FORCER l'installation OCR" ci-dessus</li>
                    <li>Attendez 30 secondes</li>
                    <li>Rechargez cette page</li>
                    <li>Si toujours KO, redéployez avec Docker</li>
                </ol>
            </div>
            
            {errors_html}
            
            <div class="status">
                <h3>🔗 Liens utiles</h3>
                <p>
                    <a href="/">Accueil</a> • 
                    <a href="/conversion/">Conversions</a> • 
                    <a href="/admin/login">Administration</a> • 
                    <a href="/test-tesseract" target="_blank">Test Tesseract API</a>
                </p>
            </div>
        </body>
        </html>
        """
        return html

    # ========================================================
    # ROUTES SYSTEME
    # ========================================================

    @app.route('/')
    def index():
        return redirect('/pdf')

    @app.route('/ads.txt')
    def ads():
        return Response(
            "google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0",
            mimetype="text/plain"
        )

    @app.route('/robots.txt')
    def robots():

        domain = AppConfig.DOMAIN.rstrip("/")
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin/\n"
            "Disallow: /debug/\n"
            f"Sitemap: https://{domain}/sitemap.xml\n"
        )

        return Response(content, mimetype="text/plain")

    # ========================================================
    # SITEMAP
    # ========================================================

    @app.route('/sitemap.xml')
    def sitemap():

        domain = AppConfig.DOMAIN.rstrip("/")
        base_url = f"https://{domain}"
        today = datetime.now().strftime('%Y-%m-%d')

        pages = [
            "/",                    # Accueil
            "/pdf",                 # Accueil PDF
            "/contact",             # Contact
            "/about",               # À propos
            "/privacy",             # Confidentialité
            "/terms",               # Conditions
            "/legal",               # Mentions légales
            "/conversion/",         # Accueil conversion (avec slash)
            "/test-ocr",            # Test OCR
            "/force-install-ocr",   # Installation OCR
        ]

        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

        for p in pages:
            xml.append(f"""
            <url>
                <loc>{base_url}{p}</loc>
                <lastmod>{today}</lastmod>
                <changefreq>weekly</changefreq>
                <priority>0.8</priority>
            </url>
            """.strip())

        xml.append('</urlset>')

        return Response(
            "\n".join(xml),
            mimetype="application/xml",
            headers={"Cache-Control": "public, max-age=3600"}
        )

    # ========================================================
    # HEALTHCHECK (Render) — dynamique
    # ========================================================

    @app.route('/health')
    def health():
        probe = _ocr_probe()
        return jsonify({
            "status": "healthy",
            "app": AppConfig.NAME,
            "version": AppConfig.VERSION,
            "ocr_available": bool(probe["enabled"] and probe["tesseract"] and probe["poppler"]),
            "tesseract": probe["tesseract"],
            "poppler": probe["poppler"],
            "lang_fra": probe["lang_fra"],
            "python_packages": probe["python_packages"],
            "message": "Application déployée sur Render"
        }), 200

    # ========================================================
    # DEBUG ROUTES
    # ========================================================

    @app.route('/debug/static-files')
    def debug_static_files():
        """Vérifier les fichiers statiques"""
        base_dir = Path(__file__).parent
        static_dir = base_dir / 'static'

        files = []

        def scan_dir(path, prefix=""):
            for item in path.iterdir():
                if item.is_file():
                    files.append(f"{prefix}/{item.name}" if prefix else item.name)
                elif item.is_dir():
                    scan_dir(item, f"{prefix}/{item.name}" if prefix else item.name)

        if static_dir.exists():
            scan_dir(static_dir)

        html = "<h1>Fichiers statiques disponibles</h1>"
        html += "<ul>"
        for file in sorted(files):
            html += f'<li><a href="/static/{file}">{file}</a></li>'
        html += "</ul>"

        return html

    # ========================================================
    # STATIC FILES FIX
    # ========================================================

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Servir les fichiers statiques avec les bons headers"""
        try:
            response = send_from_directory('static', filename)

            # Ajouter les bons headers MIME
            if filename.endswith('.css'):
                response.headers['Content-Type'] = 'text/css'
            elif filename.endswith('.js'):
                response.headers['Content-Type'] = 'application/javascript'
            elif filename.endswith('.html'):
                response.headers['Content-Type'] = 'text/html'

            # Cache pour les fichiers statiques
            response.headers['Cache-Control'] = 'public, max-age=31536000'

            return response
        except Exception as e:
            logger.warning(f"Fichier statique non trouvé: {filename}")
            return "Fichier non trouvé", 404

    # ========================================================
    # ERREURS (avec fallback si templates manquants)
    # ========================================================

    @app.errorhandler(404)
    def not_found(e):
        try:
            return render_template("errors/404.html"), 404
        except:
            return "<h1>Erreur 404 - Page non trouvée</h1><p><a href='/'>Retour à l'accueil</a></p>", 404

    @app.errorhandler(413)
    def too_large(e):
        try:
            return render_template("errors/413.html"), 413
        except:
            return "<h1>Erreur 413 - Fichier trop volumineux</h1><p>Le fichier dépasse la taille maximale autorisée.</p>", 413

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("🔥 ERREUR 500")
        try:
            return render_template("errors/500.html"), 500
        except:
            return "<h1>Erreur 500 - Problème serveur</h1><p>Une erreur interne s'est produite.</p>", 500

    # ========================================================
    # FILTRES JINJA
    # ========================================================

    @app.template_filter('filesize')
    def filesize(value):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024

    logger.info(f"✅ {AppConfig.NAME} v{AppConfig.VERSION} démarré")
    logger.info(f"🔗 URLs disponibles:")
    logger.info(f"   - Accueil: /")
    logger.info(f"   - Conversion: /conversion/")
    logger.info(f"   - Test OCR: /test-ocr")
    logger.info(f"   - Test Tesseract API: /test-tesseract")
    logger.info(f"   - Force Install OCR: /force-install-ocr")
    logger.info(f"   - Health: /health")
    logger.info(f"📦 Packages Python:")
    logger.info(f"   - pytesseract: {'✓' if PYTESSERACT_AVAILABLE else '✗'}")
    logger.info(f"   - opencv-python: {'✓' if OPENCV_AVAILABLE else '✗'}")
    logger.info(f"   - pdf2image: {'✓' if PDF2IMAGE_AVAILABLE else '✗'}")

    return app


# ============================================================
# ENTRYPOINT
# ============================================================

app = create_app()

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
