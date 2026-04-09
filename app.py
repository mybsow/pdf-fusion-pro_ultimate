#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version production ultra-stable (Render / Gunicorn ready)
"""

from flask import (Flask, redirect, Response, request, render_template,
                   send_from_directory, jsonify, session, url_for)
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import tempfile
import os
import logging
from pathlib import Path
from flask_babel import Babel
from config import AppConfig   # ajustez l'import selon votre structure


os.environ['OMP_THREAD_LIMIT'] = '1'  # Limite les threads d'OCR

# ============================================================
# Logging — configuré en premier
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================
# Variables OCR globales
# ============================================================
try:
    import pytesseract
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
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

from config import AppConfig

# ============================================================
# Factory — toute la configuration EST dans create_app()
# ============================================================
def create_app():
    logger.info("🚀 Initialisation Flask...")

    app = Flask(__name__)   # ✅ créé ICI, pas au niveau module

    # --------------------------------------------------------
    # Configuration Flask
    # --------------------------------------------------------
    app.config.from_object(AppConfig)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", AppConfig.SECRET_KEY)
    app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
    app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # ✅ Cookies de session sécurisés (indispensable sur Render HTTPS)
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 jours

    # Proxy reverse
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # --------------------------------------------------------
    # Langues
    # --------------------------------------------------------
    app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = os.path.join(
        os.path.dirname(__file__), 'translations'
    )
    app.config['LANGUAGES'] = {
        'fr': {'name': 'Français',   'flag': 'fr'},
        'en': {'name': 'English',    'flag': 'gb'},
        'es': {'name': 'Español',    'flag': 'es'},
        'de': {'name': 'Deutsch',    'flag': 'de'},
        'it': {'name': 'Italiano',   'flag': 'it'},
        'pt': {'name': 'Português',  'flag': 'pt'},
        'nl': {'name': 'Nederlands', 'flag': 'nl'},
        'ar': {'name': 'العربية',    'flag': 'sa'},
        'zh': {'name': '中文',        'flag': 'cn'},
        'ja': {'name': '日本語',      'flag': 'jp'},
        'ru': {'name': 'Русский',    'flag': 'ru'},
    }

    # --------------------------------------------------------
    # Babel
    # --------------------------------------------------------
    def get_locale():
        """Détermine la langue — appelé par Babel à chaque requête."""
        try:
            lang = session.get('language')
            if lang and lang in app.config.get('LANGUAGES', {}):
                return lang
            return (
                request.accept_languages.best_match(
                    list(app.config.get('LANGUAGES', {}).keys())
                ) or 'fr'
            )
        except Exception:
            return 'fr'

    # ✅ Babel initialisé ici, APRÈS la config, avec get_locale dans la même portée
    babel = Babel(app, locale_selector=get_locale)

    # --------------------------------------------------------
    # Répertoires
    # --------------------------------------------------------
    def init_app_dirs():
        base_dir = Path(__file__).parent
        for d in ['data/contacts', 'data/ratings', 'uploads', 'temp', 'logs']:
            (base_dir / d).mkdir(parents=True, exist_ok=True)
        contacts_file = base_dir / 'data' / 'contacts.json'
        if not contacts_file.exists():
            contacts_file.write_text('[]', encoding='utf-8')

    AppConfig.initialize()
    init_app_dirs()

    # --------------------------------------------------------
    # Blueprints
    # --------------------------------------------------------
    from blueprints.pdf import pdf_bp
    from blueprints.api import api_bp
    from blueprints.stats import stats_bp
    from blueprints.admin import admin_bp
    from blueprints.conversion import conversion_bp
    from blueprints.legal import legal_bp

    for bp, prefix in [
        (pdf_bp,        "/pdf"),
        (api_bp,        "/api"),
        (legal_bp,      None),
        (stats_bp,      None),
        (admin_bp,      "/admin"),
        (conversion_bp, "/conversion"),
    ]:
        if prefix:
            app.register_blueprint(bp, url_prefix=prefix)
        else:
            app.register_blueprint(bp)

    # --------------------------------------------------------
    # Context processor
    # --------------------------------------------------------
    @app.context_processor
    def inject_globals():
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
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        if "static" in request.path:
            response.headers["Cache-Control"] = "public, max-age=31536000"
        return response

    # --------------------------------------------------------
    # OCR probe (helper interne)
    # --------------------------------------------------------
    def _ocr_probe():
        import shutil, subprocess
        status = {
            "enabled": bool(AppConfig.OCR_ENABLED),
            "tesseract": None,
            "poppler": None,
            "lang_fra": None,
            "python_packages": {
                "pytesseract": PYTESSERACT_AVAILABLE,
                "Pillow": False,
                "pdf2image": PDF2IMAGE_AVAILABLE,
                "opencv-python": OPENCV_AVAILABLE,
            },
            "errors": [],
        }
        try:
            try:
                from PIL import Image
                status["python_packages"]["Pillow"] = True
            except ImportError:
                pass

            if not AppConfig.OCR_ENABLED:
                return status

            paths = [
                '/usr/bin/tesseract', '/usr/local/bin/tesseract',
                '/bin/tesseract', shutil.which("tesseract"),
            ]
            tesseract_path = next((p for p in paths if p and os.path.exists(p)), None)
            status["tesseract"] = tesseract_path
            status["poppler"] = shutil.which("pdftoppm") or '/usr/bin/pdftoppm'

            if tesseract_path and PYTESSERACT_AVAILABLE:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                version = pytesseract.get_tesseract_version()
                status["tesseract"] = f"{tesseract_path} (v{version})"
                try:
                    langs = pytesseract.get_languages(config='')
                    status["lang_fra"] = "fra" in langs
                except Exception:
                    result = subprocess.run(
                        [tesseract_path, '--list-langs'],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        langs = result.stdout.strip().split('\n')[1:]
                        status["lang_fra"] = "fra" in langs
        except Exception as e:
            status["errors"].append(str(e))
        return status

    # --------------------------------------------------------
    # Routes principales
    # --------------------------------------------------------
    @app.route('/')
    def index():
        return redirect('/pdf')

    @app.route("/pdf")
    def redirect_pdf():
        return redirect("/pdf/", code=301)

    @app.route('/conversion')
    def redirect_conversion():
        return redirect('/conversion/', code=301)

    @app.route('/language/<language>')
    def set_language(language):
        """Change la langue de l'utilisateur."""
        if language in app.config['LANGUAGES']:
            session['language'] = language
            session.permanent = True
            session.modified = True
            app.logger.info(f"Langue changée: {language}")
        referrer = request.referrer
        if referrer and request.host in referrer:
            return redirect(referrer)
        return redirect(url_for('pdf.pdf_index'))

    # --------------------------------------------------------
    # SEO / Sitemap / Health
    # --------------------------------------------------------
    @app.route('/ads.txt')
    def ads():
        return send_from_directory('.', 'ads.txt')


    # ─────────────────────────────────────────────────────────────
    # ROBOTS.TXT
    # ─────────────────────────────────────────────────────────────

    @app.route('/robots.txt')
    def robots():
        # AppConfig.DOMAIN est déjà propre (sans schéma, sans slash final)
        # Exemple : "pdf-fusion-pro-ultimate-ltd.onrender.com"
        domain = AppConfig.DOMAIN  # ← pas besoin de rstrip ni replace ici

        content = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            # Pages techniques / admin — à ne jamais indexer
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
            # Pages de gestion exposées dans conversion/index.html
            "Disallow: /conversion/dependencies\n"
            "Disallow: /conversion/clean-temp\n"
            "Disallow: /conversion/api/\n"
            # Paramètres de langue (contenu dupliqué)
            "Disallow: /language/\n"
            "\n"
            f"Sitemap: https://{domain}/sitemap.xml\n"
        )
        return Response(content, mimetype="text/plain")


    # ─────────────────────────────────────────────────────────────
    # SITEMAP.XML
    # ─────────────────────────────────────────────────────────────

    @app.route('/sitemap.xml')
    def sitemap():
        domain   = AppConfig.DOMAIN          # propre, sans schéma
        base_url = f"https://{domain}"
        today    = datetime.now().strftime('%Y-%m-%d')

        # (path, changefreq, priority)
        # Règle : "/" supprimé car il redirige vers /pdf/ → contenu dupliqué.
        # Les pages /language/* sont exclues (même contenu, URL différente).
        pages = [
            # ── Pages principales ──────────────────────────────────
            ("/pdf/",                          "daily",   "1.0"),
            ("/conversion/",                   "weekly",  "0.9"),

            # ── Outils PDF ─────────────────────────────────────────
            ("/pdf/merge",                     "weekly",  "0.8"),
            ("/pdf/split",                     "weekly",  "0.8"),
            ("/pdf/rotate",                    "weekly",  "0.8"),
            ("/pdf/compress",                  "weekly",  "0.8"),

            # ── Conversions vers PDF ────────────────────────────────
            ("/conversion/word-en-pdf",        "weekly",  "0.8"),
            ("/conversion/excel-en-pdf",       "weekly",  "0.8"),
            ("/conversion/powerpoint-en-pdf",  "weekly",  "0.8"),
            ("/conversion/image-en-pdf",       "weekly",  "0.8"),
            ("/conversion/jpg-en-pdf",         "weekly",  "0.7"),
            ("/conversion/png-en-pdf",         "weekly",  "0.7"),
            ("/conversion/html-en-pdf",        "weekly",  "0.7"),
            ("/conversion/txt-en-pdf",         "weekly",  "0.7"),

            # ── Conversions depuis PDF ──────────────────────────────
            ("/conversion/pdf-en-word",        "weekly",  "0.8"),
            ("/conversion/pdf-en-doc",         "weekly",  "0.7"),
            ("/conversion/pdf-en-excel",       "weekly",  "0.8"),
            ("/conversion/pdf-en-ppt",         "weekly",  "0.7"),
            ("/conversion/pdf-en-image",       "weekly",  "0.8"),
            ("/conversion/pdf-en-pdfa",        "weekly",  "0.7"),
            ("/conversion/pdf-en-html",        "weekly",  "0.7"),
            ("/conversion/pdf-en-txt",         "weekly",  "0.7"),

            # ── Outils PDF avancés ──────────────────────────────────
            ("/conversion/proteger-pdf",       "weekly",  "0.7"),
            ("/conversion/deverrouiller-pdf",  "weekly",  "0.7"),
            ("/conversion/redact-pdf",         "weekly",  "0.7"),
            ("/conversion/edit-pdf",           "weekly",  "0.7"),
            ("/conversion/sign-pdf",           "weekly",  "0.7"),
            ("/conversion/prepare-form",       "weekly",  "0.7"),

            # ── Autres conversions ──────────────────────────────────
            ("/conversion/image-en-word",      "weekly",  "0.7"),
            ("/conversion/image-en-excel",     "weekly",  "0.7"),
            ("/conversion/csv-en-excel",       "weekly",  "0.7"),
            ("/conversion/excel-en-csv",       "weekly",  "0.7"),

            # ── Pages institutionnelles ─────────────────────────────
            ("/about",                         "monthly", "0.5"),
            ("/contact",                       "monthly", "0.5"),
            ("/legal",                         "yearly",  "0.3"),
            ("/privacy",                       "yearly",  "0.3"),
            ("/terms",                         "yearly",  "0.3"),
        ]

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9'
            ' http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">',
        ]

        for path, freq, priority in pages:
            xml_lines.append(
                f"  <url>"
                f"<loc>{base_url}{path}</loc>"
                f"<lastmod>{today}</lastmod>"
                f"<changefreq>{freq}</changefreq>"
                f"<priority>{priority}</priority>"
                f"</url>"
            )

        xml_lines.append('</urlset>')

        return Response(
            "\n".join(xml_lines),
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
            "ocr_available": bool(
                probe["enabled"] and probe["tesseract"] and probe["poppler"]
            ),
            "tesseract": probe["tesseract"],
            "poppler":   probe["poppler"],
            "lang_fra":  probe["lang_fra"],
        })

    # --------------------------------------------------------
    # Routes OCR
    # --------------------------------------------------------
    @app.route('/test-ocr')
    def test_ocr():
        return jsonify(_ocr_probe())

    @app.route('/test-tesseract')
    def test_tesseract():
        try:
            if not PYTESSERACT_AVAILABLE:
                return jsonify({"error": "pytesseract non disponible"}), 500
            paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/bin/tesseract']
            cmd = next((p for p in paths if os.path.exists(p)), None)
            if not cmd:
                return jsonify({"error": "Tesseract non trouvé"}), 500
            pytesseract.pytesseract.tesseract_cmd = cmd
            version = pytesseract.get_tesseract_version()
            langs = pytesseract.get_languages(config='')
            return jsonify({
                "status": "OK",
                "tesseract_version": str(version),
                "tesseract_path": cmd,
                "available_languages": langs,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/force-install-ocr')
    def force_install_ocr():
        import sys
        packages = [
            'pytesseract==0.3.10', 'pdf2image==1.16.3',
            'Pillow==10.0.0', 'opencv-python-headless==4.8.1.78',
        ]
        results = []
        for pkg in packages:
            try:
                import subprocess as _sp
                r = _sp.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    capture_output=True, text=True, timeout=60
                )
                results.append(
                    f"✅ {pkg} installé" if r.returncode == 0
                    else f"❌ {pkg}: {r.stderr[:200]}"
                )
            except Exception as e:
                results.append(f"❌ {pkg}: {e}")
        return jsonify({"installation_results": results})

    # --------------------------------------------------------
    # Routes debug
    # --------------------------------------------------------
    @app.route('/debug-config')
    def debug_config():
        from flask_babel import get_locale as babel_get_locale
        return jsonify({
            'session_language': session.get('language', 'fr'),
            'current_locale':   str(babel_get_locale()),
            'languages_in_config': list(app.config.get('LANGUAGES', {}).keys()),
        })

    @app.route('/debug-translations')
    def debug_translations():
        from flask_babel import get_locale as babel_get_locale, gettext
        trans_dir = Path(app.config['BABEL_TRANSLATION_DIRECTORIES'])
        result = {
            'current_locale':       str(babel_get_locale()),
            'session_language':     session.get('language', 'fr'),
            'babel_default':        app.config.get('BABEL_DEFAULT_LOCALE', 'fr'),
            'translations_dir':     str(trans_dir),
            'translations_dir_exists': trans_dir.exists(),
            'languages': [],
            'test_translation':     gettext('Convertisseur de fichiers'),
        }
        if trans_dir.exists():
            for lang_dir in sorted(trans_dir.iterdir()):
                if lang_dir.is_dir():
                    mo = lang_dir / 'LC_MESSAGES' / 'messages.mo'
                    po = lang_dir / 'LC_MESSAGES' / 'messages.po'
                    result['languages'].append({
                        'lang':      lang_dir.name,
                        'mo_exists': mo.exists(),
                        'mo_size':   mo.stat().st_size if mo.exists() else 0,
                        'po_exists': po.exists(),
                    })
        return jsonify(result)

    @app.route('/debug-language')
    def debug_language():
        from flask_babel import get_locale, gettext
        trans_dir = app.config.get('BABEL_TRANSLATION_DIRECTORIES', 'translations')
        mo_files = {
            lang: os.path.exists(
                os.path.join(trans_dir, lang, 'LC_MESSAGES', 'messages.mo')
            )
            for lang in ['fr','en','es','de','it','pt','nl','ru','ja','zh','ar']
        }
        return jsonify({
            'session_language':  session.get('language', 'non défini'),
            'babel_locale':      str(get_locale()),
            'test_translations': {
                'word_to_pdf': gettext('Word vers PDF'),
                'merge_pdf':   gettext('Fusionner PDF'),
            },
            'mo_files_exist':    mo_files,
            'translations_dir':  trans_dir,
            'translations_dir_exists': os.path.exists(trans_dir),
            'available_languages': list(app.config.get('LANGUAGES', {}).keys()),
        })

    @app.route('/debug-session')
    def debug_session():
        return jsonify({
            'session_contents':  dict(session),
            'session_modified':  session.modified,
            'session_permanent': session.permanent,
            'cookie_secure':     app.config.get('SESSION_COOKIE_SECURE'),
            'cookie_httponly':   app.config.get('SESSION_COOKIE_HTTPONLY'),
            'secret_key_set':    bool(app.secret_key),
        })

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
        html = "<h1>Fichiers statiques</h1><ul>"
        for f in sorted(files):
            html += f'<li><a href="/static/{f}">{f}</a></li>'
        return html + "</ul>"

    @app.route('/debug/system')
    def debug_system():
        import subprocess
        paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/bin/tesseract']
        checks = [{
            'path': p,
            'exists': os.path.exists(p),
            'executable': os.access(p, os.X_OK) if os.path.exists(p) else False
        } for p in paths]
        try:
            r = subprocess.run(
                ['/usr/bin/tesseract', '--version'],
                capture_output=True, text=True
            )
            cmd_test = {
                'success': r.returncode == 0,
                'output': r.stdout[:200],
                'error': r.stderr[:200],
            }
        except Exception as e:
            cmd_test = {'error': str(e)}
        return jsonify({'system_checks': checks, 'command_test': cmd_test})

    @app.route('/reload-translations')
    def reload_translations():
        """Force le rechargement des traductions Babel."""
        from flask_babel import refresh
        refresh()
        return jsonify({
            'status': 'reloaded',
            'current_locale': str(get_locale()),
            'session_language': session.get('language', 'fr'),
        })

    # --------------------------------------------------------
    # Gestion des erreurs
    # --------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        try:
            return render_template("errors/404.html"), 404
        except Exception:
            return "<h1>Erreur 404</h1>", 404

    @app.errorhandler(413)
    def too_large(e):
        try:
            return render_template("errors/413.html"), 413
        except Exception:
            return "<h1>Erreur 413 - Fichier trop volumineux</h1>", 413

    @app.errorhandler(500)
    def server_error(e):
        try:
            return render_template("errors/500.html"), 500
        except Exception:
            return "<h1>Erreur 500</h1>", 500

    # --------------------------------------------------------
    # Filtres Jinja
    # --------------------------------------------------------
    @app.template_filter('filesize')
    def filesize_filter(value):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    logger.info("✅ Application Flask prête")
    return app


# ============================================================
# Entrypoint — un seul appel à create_app()
# ============================================================
application = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=False)