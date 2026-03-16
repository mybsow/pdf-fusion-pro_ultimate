#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version production ultra-stable (Render / Gunicorn ready)
"""

from flask import Flask, redirect, Response, request, render_template, send_from_directory, jsonify, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import tempfile
import os
import logging
from pathlib import Path
from flask_babel import Babel

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
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(os.path.dirname(__file__), 'translations')
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
# Babel — locale_selector lit directement la session
# ============================================================
def get_locale():
    """Détermine la langue à utiliser pour Babel"""
    # 1. Priorité absolue à la session
    if 'language' in session:
        lang = session['language']
        # Récupérer les langues depuis app.config (déjà initialisé)
        languages = app.config.get('LANGUAGES', {})
        if lang in languages:
            return lang
    # 2. Fallback sur la langue du navigateur
    return request.accept_languages.best_match(app.config.get('LANGUAGES', {}).keys()) or 'fr'

# IMPORTANT: Initialiser Babel APRÈS avoir configuré app.config
babel = Babel(app, locale_selector=get_locale)


# ============================================================
# Fonctions d'initialisation
# ============================================================
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
    # Context processor
    # IMPORTANT : ne pas injecter _() ici — Flask-Babel le fait automatiquement
    # --------------------------------------------------------
    @app.context_processor
    def inject_globals():
        from config import AppConfig
        return dict(
            Config=AppConfig,
            session=session,
            current_lang=session.get('language', 'fr'),
            languages=app.config.get('LANGUAGES', {}),
            current_year=datetime.now().year,
            datetime=datetime,
            app_name=AppConfig.NAME,
            developer_name=AppConfig.DEVELOPER_NAME,
            hosting=AppConfig.HOSTING,
            domain=AppConfig.DOMAIN,
            adsense_id='ca-pub-8967416460526921',
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
            tesseract_cmd = next((p for p in ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/bin/tesseract'] if os.path.exists(p)), None)
            if not tesseract_cmd:
                return jsonify({"error": "Tesseract non trouvé", "python_package": True}), 500
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            version = pytesseract.get_tesseract_version()
            langs = pytesseract.get_languages(config='') if PYTESSERACT_AVAILABLE else []
            return jsonify({"status": "OK", "tesseract_version": str(version), "tesseract_path": tesseract_cmd, "available_languages": langs})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/force-install-ocr')
    def force_install_ocr():
        import subprocess, sys
        packages = ['pytesseract==0.3.10', 'pdf2image==1.16.3', 'Pillow==10.0.0', 'opencv-python-headless==4.8.1.78']
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
        """Change la langue de l'utilisateur"""
        if language in app.config['LANGUAGES']:
            session['language'] = language
            session.permanent = True
            # Force la sauvegarde de la session
            session.modified = True
            
            # Log pour debug
            app.logger.info(f"Langue changée: {language}")
        
        # Redirection
        referrer = request.referrer
        if referrer and request.host in referrer:
            return redirect(referrer)
        return redirect(url_for('pdf.pdf_index'))

    # ------------------- SEO / sitemap / Health -------------------
    @app.route('/ads.txt')
    def ads():
        return send_from_directory('.', 'ads.txt')

    @app.route('/robots.txt')
    def robots():
        domain = AppConfig.DOMAIN.rstrip("/")
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            "# Bloquer routes debug et système\n"
            "Disallow: /admin/\n"
            "Disallow: /uploads/\n"
            "Disallow: /temp/\n"
            "Disallow: /debug/\n"
            "Disallow: /debug-config\n"
            "Disallow: /debug-translations\n"
            "Disallow: /test-ocr\n"
            "Disallow: /test-tesseract\n"
            "Disallow: /force-install-ocr\n"
            "Disallow: /health\n"
            "\n"
            f"Sitemap: https://{domain}/sitemap.xml\n"
            "\n"
            "# PDF Fusion Pro - Développé par MYBSOW\n"
            "# Contact: banousow@gmail.com\n"
        )
        return Response(content, mimetype="text/plain")


    @app.route('/sitemap.xml')
    def sitemap():
        domain = AppConfig.DOMAIN.rstrip("/")
        base_url = f"https://{domain}"
        today = datetime.now().strftime('%Y-%m-%d')

        pages = [
            # ── Pages principales ──────────────────────────────────
            ("/",                               "daily",   "1.0"),
            ("/pdf/",                           "weekly",  "0.9"),

            # ── Outils PDF ────────────────────────────────────────
            ("/pdf/merge",                      "weekly",  "0.8"),
            ("/pdf/split",                      "weekly",  "0.8"),
            ("/pdf/rotate",                     "weekly",  "0.8"),
            ("/pdf/compress",                   "weekly",  "0.8"),

            # ── Convertir en PDF ──────────────────────────────────
            ("/conversion/",                    "weekly",  "0.8"),
            ("/conversion/word-en-pdf",         "weekly",  "0.7"),
            ("/conversion/excel-en-pdf",        "weekly",  "0.7"),
            ("/conversion/powerpoint-en-pdf",   "weekly",  "0.7"),
            ("/conversion/image-en-pdf",        "weekly",  "0.7"),
            ("/conversion/jpg-en-pdf",          "weekly",  "0.6"),
            ("/conversion/png-en-pdf",          "weekly",  "0.6"),
            ("/conversion/html-en-pdf",         "weekly",  "0.6"),
            ("/conversion/txt-en-pdf",          "weekly",  "0.6"),

            # ── Convertir depuis PDF ───────────────────────────────
            ("/conversion/pdf-en-word",         "weekly",  "0.7"),
            ("/conversion/pdf-en-doc",          "weekly",  "0.6"),
            ("/conversion/pdf-en-excel",        "weekly",  "0.7"),
            ("/conversion/pdf-en-ppt",          "weekly",  "0.6"),
            ("/conversion/pdf-en-image",        "weekly",  "0.7"),
            ("/conversion/pdf-en-pdfa",         "weekly",  "0.6"),
            ("/conversion/pdf-en-html",         "weekly",  "0.6"),
            ("/conversion/pdf-en-txt",          "weekly",  "0.6"),

            # ── Outils PDF avancés ────────────────────────────────
            ("/conversion/proteger-pdf",        "weekly",  "0.6"),
            ("/conversion/deverrouiller-pdf",   "weekly",  "0.6"),
            ("/conversion/redact-pdf",          "weekly",  "0.6"),
            ("/conversion/edit-pdf",            "weekly",  "0.6"),
            ("/conversion/sign-pdf",            "weekly",  "0.6"),
            ("/conversion/prepare-form",        "weekly",  "0.6"),

            # ── Conversions diverses ──────────────────────────────
            ("/conversion/image-en-word",       "weekly",  "0.6"),
            ("/conversion/image-en-excel",      "weekly",  "0.6"),
            ("/conversion/csv-en-excel",        "weekly",  "0.6"),
            ("/conversion/excel-en-csv",        "weekly",  "0.6"),

            # ── Pages légales (doivent exister dans legal blueprint) ──
            ("/about",                          "monthly", "0.5"),
            ("/contact",                        "monthly", "0.5"),
            ("/legal",                          "yearly",  "0.3"),
            ("/privacy",                        "yearly",  "0.3"),
            ("/terms",                          "yearly",  "0.3"),
        ]

        xml = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]
        for path, freq, priority in pages:
            xml.append(
                f"  <url>"
                f"<loc>{base_url}{path}</loc>"
                f"<lastmod>{today}</lastmod>"
                f"<changefreq>{freq}</changefreq>"
                f"<priority>{priority}</priority>"
                f"</url>"
            )
        xml.append('</urlset>')

        return Response(
            "\n".join(xml),
            mimetype="application/xml",
            headers={"Cache-Control": "public, max-age=3600"}
        )

    @app.route('/google6f0d847067bbd18a.html')
    def google_verification():
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
        paths_to_check = ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/bin/tesseract']
        checks = [{'path': p, 'exists': os.path.exists(p), 'executable': os.access(p, os.X_OK) if os.path.exists(p) else False} for p in paths_to_check]
        try:
            result = subprocess.run(['/usr/bin/tesseract', '--version'], capture_output=True, text=True)
            cmd_test = {'success': result.returncode == 0, 'output': result.stdout[:200], 'error': result.stderr[:200]}
        except Exception as e:
            cmd_test = {'error': str(e)}
        return jsonify({'system_checks': checks, 'command_test': cmd_test})

    @app.route('/debug-config')
    def debug_config():
        from flask_babel import get_locale as babel_get_locale
        return jsonify({
            'session_language': session.get('language', 'fr'),
            'current_locale': str(babel_get_locale()),
            'languages_in_config': list(app.config.get('LANGUAGES', {}).keys()),
        })

    @app.route('/debug-translations')
    def debug_translations():
        from flask_babel import get_locale as babel_get_locale, gettext
        trans_dir = Path(app.config['BABEL_TRANSLATION_DIRECTORIES'])
        result = {
            'current_locale': str(babel_get_locale()),
            'session_language': session.get('language', 'fr'),
            'babel_default': app.config.get('BABEL_DEFAULT_LOCALE', 'fr'),
            'translations_dir': str(trans_dir),
            'translations_dir_exists': trans_dir.exists(),
            'languages': [],
            'test_translation': gettext('Convertisseur de fichiers'),
        }
        if trans_dir.exists():
            for lang_dir in sorted(trans_dir.iterdir()):
                if lang_dir.is_dir():
                    mo_file = lang_dir / 'LC_MESSAGES' / 'messages.mo'
                    po_file = lang_dir / 'LC_MESSAGES' / 'messages.po'
                    result['languages'].append({
                        'lang': lang_dir.name,
                        'mo_exists': mo_file.exists(),
                        'mo_size': mo_file.stat().st_size if mo_file.exists() else 0,
                        'po_exists': po_file.exists(),
                    })
        return jsonify(result)
    
    @app.route('/debug-language')
    def debug_language():
        """Vérifie la configuration de la langue"""
        from flask_babel import get_locale, gettext
        import os
        
        # Langue actuelle
        current_session_lang = session.get('language', 'non défini')
        current_babel_locale = str(get_locale())
        
        # Test de traduction
        test_word = gettext('Word vers PDF')
        test_merge = gettext('Fusionner PDF')
        
        # Vérification des fichiers .mo
        trans_dir = app.config.get('BABEL_TRANSLATION_DIRECTORIES', 'translations')
        mo_files = {}
        
        for lang in ['fr', 'en', 'es', 'de', 'it', 'pt', 'nl', 'ru', 'ja', 'zh', 'ar']:
            mo_path = os.path.join(trans_dir, lang, 'LC_MESSAGES', 'messages.mo')
            mo_files[lang] = os.path.exists(mo_path)
        
        return jsonify({
            'session_language': current_session_lang,
            'babel_locale': current_babel_locale,
            'test_translations': {
                'word_to_pdf': test_word,
                'merge_pdf': test_merge,
            },
            'mo_files_exist': mo_files,
            'translations_dir': trans_dir,
            'translations_dir_exists': os.path.exists(trans_dir),
            'available_languages': list(app.config.get('LANGUAGES', {}).keys()),
        })

    @app.route('/debug/static-check')
    def debug_static_check():
        static_dir = Path('static')
        result = {
            'static_exists': static_dir.exists(),
            'js_components': [],
            'js_pages': [],
            'css_files': []
        }
        if static_dir.exists():
            js_components = static_dir / 'js' / 'components'
            if js_components.exists():
                result['js_components'] = [f.name for f in js_components.glob('*.js')]
            js_pages = static_dir / 'js' / 'pages'
            if js_pages.exists():
                result['js_pages'] = [f.name for f in js_pages.glob('*.js')]
            css_dir = static_dir / 'css'
            if css_dir.exists():
                result['css_files'] = [f.name for f in css_dir.glob('*.css')]
        return jsonify(result)
    
    @app.route('/debug-session')
    def debug_session():
        """Vérifie la session"""
        return jsonify({
            'session_contents': dict(session),
            'session_modified': session.modified,
            'session_permanent': session.permanent,
            'cookie_secure': app.config.get('SESSION_COOKIE_SECURE'),
            'cookie_httponly': app.config.get('SESSION_COOKIE_HTTPONLY'),
            'secret_key_set': bool(app.secret_key),
        })

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
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024

    return app

@app.route('/reload-translations')
def reload_translations():
    """Force le rechargement des traductions"""
    import sys
    from flask_babel import refresh
    
    refresh()  # Force Babel à recharger les catalogues
    
    # Vider le cache des traductions
    if hasattr(babel, 'list_translations'):
        babel.list_translations.cache_clear()
    
    return jsonify({
        'status': 'reloaded',
        'current_locale': str(get_locale()),
        'session_language': session.get('language', 'fr')
    })


# ============================================================
# Entrypoint
# ============================================================
application = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=True)