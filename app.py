#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - App principale
i18n ultra-rapide + OCR + routes SEO / santé
"""

import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, redirect, Response, request, render_template, session, jsonify, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_babel import Babel
import subprocess
import shutil

# ============================================================
# Logging
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# Création app
# ============================================================
app = Flask(__name__)
from config import AppConfig
app.config.from_object(AppConfig)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", AppConfig.SECRET_KEY)
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# ============================================================
# Langues
# ============================================================
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
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

def get_locale():
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

babel = Babel(app, locale_selector=get_locale)

# ============================================================
# i18n préchargé
# ============================================================
import gettext
translations_cache = {}

def load_translations():
    base = Path(app.config['BABEL_TRANSLATION_DIRECTORIES'])
    for lang_dir in base.iterdir():
        if lang_dir.is_dir():
            mo_file = lang_dir / 'LC_MESSAGES' / 'messages.mo'
            if mo_file.exists():
                try:
                    translations_cache[lang_dir.name] = gettext.GNUTranslations(open(mo_file, 'rb'))
                    logger.info(f"✅ Traductions {lang_dir.name} chargées en mémoire")
                except Exception as e:
                    logger.error(f"Erreur traduction {lang_dir.name}: {e}")

load_translations()

def _(message):
    lang = get_locale()
    t = translations_cache.get(lang)
    if t:
        return t.gettext(message)
    return message

# ============================================================
# OCR
# ============================================================
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

def _ocr_probe():
    status = {
        "enabled": AppConfig.OCR_ENABLED,
        "tesseract": None,
        "poppler": shutil.which("pdftoppm"),
        "lang_fra": False
    }

    if not AppConfig.OCR_ENABLED:
        return status

    tesseract_path = shutil.which("tesseract")
    if tesseract_path and PYTESSERACT_AVAILABLE:
        try:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            langs = pytesseract.get_languages(config="")
            status["tesseract"] = tesseract_path
            status["lang_fra"] = "fra" in langs
        except Exception:
            pass

    return status

# ============================================================
# Initialisation dossiers/templates
# ============================================================
def init_app_dirs():
    base_dir = Path(__file__).parent
    for d in ['data/contacts', 'data/ratings', 'uploads', 'temp', 'logs']:
        (base_dir / d).mkdir(parents=True, exist_ok=True)
    contacts_file = base_dir / 'data' / 'contacts.json'
    if not contacts_file.exists():
        contacts_file.write_text('[]', encoding='utf-8')

# ============================================================
# Création app complète
# ============================================================
def create_app():
    logger.info("🚀 Initialisation Flask...")
    AppConfig.initialize()
    init_app_dirs()
    check_and_create_templates()

    # ------------------- Blueprints -------------------
    from blueprints.pdf import pdf_bp
    from blueprints.api import api_bp
    from blueprints.stats import stats_bp
    from blueprints.admin import admin_bp
    from blueprints.conversion import conversion_bp
    from blueprints.legal import legal_bp

    for bp, prefix in [
        (pdf_bp, "/pdf"),
        (api_bp, "/api"),
        (legal_bp, None),
        (stats_bp, None),
        (admin_bp, "/admin"),
        (conversion_bp, "/conversion")
    ]:
        if prefix:
            app.register_blueprint(bp, url_prefix=prefix)
        else:
            app.register_blueprint(bp)

    # ------------------- Routes -------------------
    @app.route('/')
    def index():
        return redirect('/pdf')

    @app.route('/conversion')
    def redirect_conversion():
        return redirect('/conversion/', code=301)

    @app.route("/pdf")
    def redirect_pdf():
        return redirect("/pdf/", code=301)

    @app.route('/language/<language>')
    def set_language(language):
        if language in app.config['LANGUAGES']:
            session['language'] = language
        return redirect(request.referrer or url_for('pdf.pdf_index'))

    # ------------------- SEO / sitemap -------------------
    @app.route('/ads.txt')
    def ads():
        return Response("google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0", mimetype="text/plain")

    @app.route('/robots.txt')
    def robots():
        domain = AppConfig.DOMAIN.rstrip("/")
        return Response(f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://{domain}/sitemap.xml\n",
                        mimetype="text/plain")

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

    # ------------------- Health check -------------------
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


    # ------------------- Context Jinja -------------------
    @app.context_processor
    def inject_globals():
        return dict(languages=app.config["LANGUAGES"], _=_)

    # ------------------- Filters -------------------
    @app.template_filter('filesize')
    def filesize(value):
        for unit in ['B','KB','MB','GB','TB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024

    # ------------------- Error handlers -------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500


    # ------------------- Debug OCR (dev only) -------------------
    if app.debug:

        @app.route("/test-ocr")
        def test_ocr():
            return jsonify(_ocr_probe())

        @app.route("/force-install-ocr")
        def force_install_ocr():
            import sys
            packages = ["pytesseract", "pdf2image", "Pillow", "opencv-python-headless"]
            results = []
            for pkg in packages:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)
                    results.append(f"{pkg} installé")
                except Exception as e:
                    results.append(f"{pkg} erreur: {e}")
            return jsonify(results)

# ============================================================
# Entrypoint
# ============================================================
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
