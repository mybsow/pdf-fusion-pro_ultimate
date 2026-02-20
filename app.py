#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version production ultra-stable (Render / Gunicorn ready)
"""

from flask import Flask, redirect, Response, request, render_template, session, jsonify, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import tempfile
import os
import logging
import polib, re
from flask_wtf import CSRFProtect
from flask_babel import Babel, gettext
from flask_babel import _

# ============================================================
# Création de l'app Flask
# ============================================================
app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# Langues supportées
LANGUAGES = ["fr", "en"]
app.config["LANGUAGES"] = LANGUAGES

# ============================================================
# Configuration
# ============================================================
from config import AppConfig

app.config.from_object(AppConfig)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", AppConfig.SECRET_KEY)
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

# Proxy reverse
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# Configuration Babel
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


# ============================================================
# Logging
# ============================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# BABEL (Flask-Babel >= 3.x compatible)
# ============================================================

def get_locale():
    return session.get("lang", "fr")

babel = Babel(app, locale_selector=get_locale)

# ============================================================
# CSRF PROTECTION
# ============================================================

csrf = CSRFProtect(app)

# ============================================================
# BLUEPRINTS
# ============================================================

# Import ici pour éviter les imports circulaires
from blueprints.legal.routes import legal_bp
from blueprints.pdf.routes import pdf_bp
from blueprints.conversion import conversion_bp
from blueprints.admin import admin_bp
from blueprints.api.routes import api_bp

app.register_blueprint(legal_bp)
app.register_blueprint(pdf_bp)
app.register_blueprint(conversion_bp)
app.register_blueprint(admin_bp)

# -----------------------------
# Blueprints — API
# -----------------------------
# Toutes les routes JSON/API sous /api
# Evite le conflit avec /pdf ou /admin
app.register_blueprint(api_bp, url_prefix="/api")        


# ============================================================
# Fonctions utilitaires
# ============================================================
def compile_all_translations(translations_dir="translations"):
    translations_path = Path(translations_dir)
    fixed_count = 0

    for po_file in translations_path.rglob("*.po"):
        lang_dir = po_file.parent.parent  # remonte à <lang>
        mo_file = lang_dir / "LC_MESSAGES" / "messages.mo"
        mo_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            po = polib.pofile(str(po_file))
            po.save_as_mofile(str(mo_file))
            fixed_count += 1
            print(f"✅ Compilé: {po_file} → {mo_file}")
        except Exception as e:
            print(f"❌ Erreur compilation {po_file}: {e}")
    print(f"Total fichiers compilés: {fixed_count}")

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
# Routes principales
# ============================================================
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
    if language in app.config['LANGUAGES']:
        session['language'] = language
        logger.info(f"Langue changée pour: {language}")
    return redirect(request.referrer or url_for('index'))

@app.route('/test-translation/<word>')
def test_translation(word):
    translations = {}
    for lang in app.config['LANGUAGES'].keys():
        session['language'] = lang
        translations[lang] = gettext(word)
    return jsonify({
        'word': word,
        'translations': translations,
        'current_session': session.get('language', 'fr')
    })

@app.route('/ads.txt')
def ads():
    return Response("google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0", mimetype="text/plain")

@app.route('/robots.txt')
def robots():
    domain = AppConfig.DOMAIN.rstrip("/")
    return Response(f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://{domain}/sitemap.xml\n", mimetype="text/plain")

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
        ("/force-install-ocr", "weekly", "0.8"),
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

# ============================================================
# Template filters et erreurs
# ============================================================
@app.template_filter('filesize')
def filesize(value):
    for unit in [_('B'), _('KB'), _('MB'), _('GB')]:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

@app.errorhandler(404)
def not_found(e):
    try:
        return render_template("errors/404.html"), 404
    except:
        return f"<h1>{_('Erreur 404')}</h1>", 404

@app.errorhandler(413)
def too_large(e):
    try:
        return render_template("errors/413.html"), 413
    except:
        return f"<h1>{_('Erreur 413 - Fichier trop volumineux')}</h1>", 413

@app.errorhandler(500)
def server_error(e):
    try:
        return render_template("errors/500.html"), 500
    except:
        return f"<h1>{_('Erreur 500')}</h1>", 500

# ============================================================
# Initialisation
# ============================================================
def create_app():
    logger.info(_("🚀 Initialisation Flask..."))
    AppConfig.initialize()
    init_app_dirs()
    compile_all_translations()
    return app

app = create_app()

# ============================================================
# Entrypoint
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
