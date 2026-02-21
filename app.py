#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version production ultra-stable (Render / Gunicorn ready)
"""

from flask import Flask, redirect, Response, request, render_template, send_from_directory, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import tempfile
import os
import logging
from pathlib import Path
from flask_babel import Babel, _
from flask import request, session

# ============================================================
# Création de l'app Flask
# ============================================================
app = Flask(__name__)

# ============================================================
# Variables OCR globales
# ============================================================
try:
    import pytesseract # type: ignore
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

try:
    import cv2
    OPENCV_AVAILABLE = True
    cv2.setNumThreads(0)
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from pdf2image import convert_from_path # type: ignore
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from config import AppConfig

# ============================================================
# Logging production
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================
# Configuration Flask
# ============================================================
app.config.from_object(AppConfig)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", AppConfig.SECRET_KEY)
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
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

# Configuration des langues supportées
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'  # Langue par défaut
app.config['BABEL_TRANSLATION_DIRECTORIES'] = './translations'
app.config['LANGUAGES'] = {
    'fr': {'name': 'Français', 'flag': 'fr'},
    'en': {'name': 'English', 'flag': 'gb'},
    'es': {'name': 'Español', 'flag': 'es'},
    'de': {'name': 'Deutsch', 'flag': 'de'},
    'it': {'name': 'Italiano', 'flag': 'it'},
    'pt': {'name': 'Português', 'flag': 'pt'},
    'nl': {'name': 'Nederlands', 'flag': 'nl'},
    'ar': {'name': 'العربية', 'flag': 'sa'},
    'zh': {'name': '中文', 'flag': 'cn'},
    'ja': {'name': '日本語', 'flag': 'jp'},
    'ru': {'name': 'Русский', 'flag': 'ru'},
}
# ============================================================
# Fonction pour déterminer la langue
# ============================================================
def get_locale():
    # 1. Vérifier si l'utilisateur a choisi une langue en session
    if 'language' in session:
        return session['language']
    # 2. Sinon, utiliser la langue du navigateur
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

# Initialiser Babel
babel = Babel(app, locale_selector=get_locale)

# ============================================================
# Fonctions d'initialisation
# ============================================================
def check_and_create_templates():
    required = [
        'conversion/csv_to_excel.html',
        'conversion/excel_to_csv.html',
        'conversion/pdf_to_image.html',
        'conversion/pdf_to_doc.html',
        'conversion/pdf_to_excel.html',
        'conversion/pdf_to_pdf.html',
        'conversion/pdf_to_ppt.html',
        'errors/404.html',
        'errors/413.html',
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

def init_app_dirs():
    base_dir = Path(__file__).parent
    dirs = ['data/contacts', 'data/ratings', 'uploads', 'temp', 'logs']
    for d in dirs:
        path = base_dir / d
        path.mkdir(parents=True, exist_ok=True)
    contacts_file = base_dir / 'data' / 'contacts.json'
    if not contacts_file.exists():
        contacts_file.write_text('[]', encoding='utf-8')

# ============================================================
# Create App complet
# ============================================================
def create_app():
    logger.info("🚀 Initialisation Flask...")
    AppConfig.initialize()
    init_app_dirs()
    check_and_create_templates()

    # --------------------------------------------------------
    # Import Blueprints
    # --------------------------------------------------------
    from blueprints.pdf import pdf_bp
    from blueprints.api import api_bp
    from blueprints.stats import stats_bp
    from blueprints.admin import admin_bp
    from blueprints.conversion import conversion_bp
    from blueprints.legal import legal_bp

    blueprints = [
        (pdf_bp, "/pdf"),
        (api_bp, "/api"),
        (legal_bp, None),
        (stats_bp, None),
        (admin_bp, "/admin"),
        (conversion_bp, "/conversion")
    ]
    for bp, prefix in blueprints:
        if prefix:
            app.register_blueprint(bp, url_prefix=prefix)
        else:
            app.register_blueprint(bp)

    # Redirection /conversion vers /conversion/
    @app.route('/conversion')
    def redirect_conversion():
        return redirect('/conversion/', code=301)

    # --------------------------------------------------------
    # Context processor pour config
    # --------------------------------------------------------
    @app.context_processor
    def inject_config():
        return dict(
            config=app.config,
            languages=app.config.get('LANGUAGES', {})
        )

    # --------------------------------------------------------
    # Security headers
    # --------------------------------------------------------
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if "static" in request.path:
            response.headers["Cache-Control"] = "public, max-age=31536000"
        return response

    # ============================================================
    # OCR Probe
    # ============================================================
    def _ocr_probe():
        import shutil
        import subprocess
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
            try:
                from PIL import Image
                status["python_packages"]["Pillow"] = True
            except ImportError:
                status["python_packages"]["Pillow"] = False

            if not AppConfig.OCR_ENABLED:
                return status

            possible_paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/bin/tesseract', shutil.which("tesseract")]
            tesseract_path = next((p for p in possible_paths if p and os.path.exists(p)), None)
            status["tesseract"] = tesseract_path
            status["poppler"] = shutil.which("pdftoppm") or '/usr/bin/pdftoppm'

            if tesseract_path and PYTESSERACT_AVAILABLE:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                version = pytesseract.get_tesseract_version()
                status["tesseract"] = f"{tesseract_path} (v{version})"
                try:
                    langs = pytesseract.get_languages(config='')
                    status["lang_fra"] = "fra" in langs
                except:
                    result = subprocess.run([tesseract_path, '--list-langs'], capture_output=True, text=True)
                    if result.returncode == 0:
                        langs = result.stdout.strip().split('\n')[1:]
                        status["lang_fra"] = "fra" in langs
        except Exception as e:
            status["errors"].append(str(e))

        return status

    # --------------------------------------------------------
    # Routes OCR
    # --------------------------------------------------------
    @app.route('/test-ocr')
    def test_ocr():
        probe = _ocr_probe()
        return jsonify(probe)

    @app.route('/test-tesseract')
    def test_tesseract():
        try:
            if not PYTESSERACT_AVAILABLE:
                return jsonify({"error": "pytesseract non disponible", "installed": False}), 500
            tesseract_cmd = next((p for p in ['/usr/bin/tesseract','/usr/local/bin/tesseract','/bin/tesseract'] if os.path.exists(p)), None)
            if not tesseract_cmd:
                return jsonify({"error": "Tesseract non trouvé", "python_package": True}), 500
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            version = pytesseract.get_tesseract_version()
            langs = pytesseract.get_languages(config='') if PYTESSERACT_AVAILABLE else []
            return jsonify({"status": "OK","tesseract_version": str(version),"tesseract_path": tesseract_cmd,"available_languages": langs})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/force-install-ocr')
    def force_install_ocr():
        import subprocess, sys
        packages = ['pytesseract==0.3.10','pdf2image==1.16.3','Pillow==10.0.0','opencv-python-headless==4.8.1.78']
        results = []
        for package in packages:
            try:
                cmd = [sys.executable, "-m", "pip", "install", package]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    results.append(f"✅ {package} installé")
                else:
                    results.append(f"❌ {package} erreur: {result.stderr[:200]}")
            except Exception as e:
                results.append(f"❌ {package} exception: {str(e)}")
        return jsonify({"installation_results": results})

    # ============================================================
    # Routes système et sitemap
    # ============================================================
    @app.route('/')
    def index():
        return redirect('/pdf')
    
    @app.route("/pdf")
    def redirect_pdf():
        return redirect("/pdf/", code=301)
    
    # Route pour changer de langue
    @app.route('/language/<language>')
    def set_language(language):
        if language in app.config['LANGUAGES']:
            session['language'] = language
        return redirect(request.referrer or url_for('pdf.pdf_index'))

    # ------------------- SEO / sitemap / Health -------------------
    @app.route('/ads.txt')
    def ads():
        return send_from_directory('.', 'ads.txt')

    # Route pour robots.txt à la racine du projet
    @app.route('/robots.txt')
    def robots():
        return send_from_directory('.', 'robots.txt')

    @app.route('/sitemap.xml')
    def sitemap():
        domain = AppConfig.DOMAIN.rstrip("/")
        base_url = f"https://{domain}"
        today = datetime.now().strftime('%Y-%m-%d')
        pages = [
            ("/", "daily", "1.0"),
            ("/pdf", "weekly", "0.9"),
            ("/conversion/", "weekly", "0.8"),
            ("/test-ocr", "weekly", "0.8"),
            ("/contact", "monthly", "0.7"),
            ("/about", "monthly", "0.6"),
            ("/legal", "yearly", "0.4"),
            ("/privacy", "yearly", "0.4"),
            ("/terms", "yearly", "0.4"),
        ]
        xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for path, freq, priority in pages:
            clean_path = path if path.startswith('/') else f"/{path}"
            url = f"{base_url}{clean_path}"
            xml.append(f"  <url><loc>{url}</loc><lastmod>{today}</lastmod><changefreq>{freq}</changefreq><priority>{priority}</priority></url>")
        xml.append('</urlset>')
        return Response("\n".join(xml), mimetype="application/xml", headers={"Cache-Control": "public, max-age=3600"})
    
    
    @app.route('/google6f0d847067bbd18a.html')
    def google_verification():
        """Retourne directement le contenu de vérification"""
        return Response(
            "google-site-verification: google6f0d847067bbd18a.html", 
            mimetype="text/html"
        )

    @app.route('/health')
    def health():
        probe = _ocr_probe()
        return jsonify({
            "status": "healthy",
            "ocr_available": bool(probe["enabled"] and probe["tesseract"] and probe["poppler"]),
            "tesseract": probe["tesseract"],
            "poppler": probe["poppler"],
            "lang_fra": probe["lang_fra"]
        })

    # ============================================================
    # Routes debug
    # ============================================================
    @app.route('/debug/static-files')
    def debug_static_files():
        base_dir = Path(__file__).parent / 'static'
        files = []
        def scan_dir(path, prefix=""):
            for item in path.iterdir():
                if item.is_file():
                    files.append(f"{prefix}/{item.name}" if prefix else item.name)
                elif item.is_dir():
                    scan_dir(item, f"{prefix}/{item.name}" if prefix else item.name)
        if base_dir.exists():
            scan_dir(base_dir)
        html = "<h1>Fichiers statiques disponibles</h1><ul>"
        for file in sorted(files):
            html += f'<li><a href="/static/{file}">{file}</a></li>'
        html += "</ul>"
        return html

    @app.route('/debug/system')
    def debug_system():
        import subprocess
        paths_to_check = ['/usr/bin/tesseract','/usr/local/bin/tesseract','/bin/tesseract']
        checks = [{'path':p,'exists':os.path.exists(p),'executable':os.access(p,os.X_OK) if os.path.exists(p) else False} for p in paths_to_check]
        try:
            result = subprocess.run(['/usr/bin/tesseract','--version'], capture_output=True, text=True)
            cmd_test = {'success': result.returncode == 0,'output':result.stdout[:200],'error':result.stderr[:200]}
        except Exception as e:
            cmd_test = {'error': str(e)}
        return jsonify({'system_checks': checks,'command_test': cmd_test})

    @app.route('/debug-config')
    def debug_config():
        """Route de diagnostic pour vérifier la configuration"""
        from flask_babel import get_locale
        
        return jsonify({
            'session_language': session.get('language', 'fr'),
            'current_locale': str(get_locale()),
            'languages_in_config': list(app.config.get('LANGUAGES', {}).keys()),
            'config_keys': list(app.config.keys()),
            'has_config_processor': 'config' in dict(app.context_processor(lambda: {})())
        })

    @app.route('/debug-languages')
    def debug_languages():
        """Vérifie la configuration des langues"""
        return jsonify({
            'session_language': session.get('language', 'fr'),
            'languages_in_config': list(app.config.get('LANGUAGES', {}).keys()),
            'config_keys': list(app.config.keys()),
            'has_languages': 'LANGUAGES' in app.config
        })

    @app.route('/debug-translations')
    def debug_translations():
        """Vérifie l'état des traductions"""
        import os
        from pathlib import Path
        from flask_babel import get_locale, gettext
        
        trans_dir = Path('translations')
        result = {
            'current_locale': str(get_locale()),
            'session_language': session.get('language', 'fr'),
            'babel_default': app.config.get('BABEL_DEFAULT_LOCALE', 'fr'),
            'translations_dir_exists': trans_dir.exists(),
            'languages': [],
            'test_translations': {
                'fr': gettext('PDF Fusion Pro - Outils PDF Gratuits'),
                'en': gettext('PDF Fusion Pro - Outils PDF Gratuits'),  # Même chaîne pour test
            }
        }
        
        if trans_dir.exists():
            for lang_dir in trans_dir.iterdir():
                if lang_dir.is_dir():
                    mo_file = lang_dir / 'LC_MESSAGES' / 'messages.mo'
                    po_file = lang_dir / 'LC_MESSAGES' / 'messages.po'
                    result['languages'].append({
                        'lang': lang_dir.name,
                        'mo_exists': mo_file.exists(),
                        'mo_size': mo_file.stat().st_size if mo_file.exists() else 0,
                        'po_exists': po_file.exists(),
                        'po_size': po_file.stat().st_size if po_file.exists() else 0
                    })
        
        return jsonify(result)
    
    

# Ajoutez ceci DANS votre app.py (après les autres routes)

    @app.route('/debug/static-check')
    def debug_static_check():
        """Vérifie les fichiers statiques"""
        import os
        from pathlib import Path
        
        static_dir = Path('static')
        result = {
            'static_exists': static_dir.exists(),
            'js_components': [],
            'js_pages': [],
            'css_files': []
        }
        
        if static_dir.exists():
            # Vérifier js/components
            js_components = static_dir / 'js' / 'components'
            if js_components.exists():
                result['js_components'] = [f.name for f in js_components.glob('*.js')]
            
            # Vérifier js/pages
            js_pages = static_dir / 'js' / 'pages'
            if js_pages.exists():
                result['js_pages'] = [f.name for f in js_pages.glob('*.js')]
            
            # Vérifier css
            css_dir = static_dir / 'css'
            if css_dir.exists():
                result['css_files'] = [f.name for f in css_dir.glob('*.css')]
        
        return jsonify(result)

    # ============================================================
    # Erreurs et filtres Jinja
    # ============================================================
    @app.errorhandler(404)
    def not_found(e):
        try:
            return render_template("errors/404.html"), 404
        except:
            return "<h1>Erreur 404</h1>", 404

    @app.errorhandler(413)
    def too_large(e):
        try:
            return render_template("errors/413.html"), 413
        except:
            return "<h1>Erreur 413 - Fichier trop volumineux</h1>", 413

    @app.errorhandler(500)
    def server_error(e):
        try:
            return render_template("errors/500.html"), 500
        except:
            return "<h1>Erreur 500</h1>", 500

    @app.template_filter('filesize')
    def filesize(value):
        for unit in ['B','KB','MB','GB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024

    return app

# ============================================================
# Entrypoint
# ============================================================
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
