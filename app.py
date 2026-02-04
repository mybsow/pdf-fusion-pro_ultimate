#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version production ultra-stable (Render / Gunicorn ready)
"""

from flask import Flask, redirect, Response, request, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import os
import logging
from pathlib import Path

from config import AppConfig

# Blueprints - IMPORT CORRECT
from blueprints.pdf import pdf_bp
from blueprints.api import api_bp
from blueprints.stats import stats_bp
from blueprints.admin import admin_bp
from blueprints.conversion import conversion_bp
# IMPORT UNIQUE - Vérifiez où est défini legal_bp
from legal.routes import legal_bp  # SI legal_bp est défini dans legal/routes.py

# ============================================================
# LOGGING PRODUCTION
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


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

    # ⚠️ NE PAS définir SERVER_NAME sur Render
    # cela casse souvent les URLs dynamiques

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

        # Mettez à jour ces URLs pour correspondre à vos vraies routes
        pages = [
            "/",                    # Accueil
            "/pdf",                 # Accueil PDF
            "/pdf/merge",           # Fusion PDF
            "/pdf/split",           # Division PDF
            "/pdf/rotate",          # Rotation PDF
            "/pdf/compress",        # Compression PDF
            "/conversion",          # Accueil conversion
            "/conversion/image-vers-pdf",  # Image vers PDF
            "/conversion/image-vers-word", # Image vers Word
            "/conversion/image-vers-excel", # Image vers Excel
            "/contact",             # Contact
            "/about",               # À propos
            "/privacy",             # Confidentialité
            "/terms",               # Conditions
            "/legal"                # Mentions légales
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
            """)

        xml.append('</urlset>')

        return Response(
            "\n".join(xml),
            mimetype="application/xml",
            headers={"Cache-Control": "public, max-age=3600"}
        )

    # ========================================================
    # HEALTHCHECK (Render)
    # ========================================================

    @app.route('/health')
    def health():
        return {
            "status": "healthy",
            "app": AppConfig.NAME,
            "version": AppConfig.VERSION
        }, 200

    # ========================================================
    # ERREURS (templates recommandés)
    # ========================================================

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("🔥 ERREUR 500")
        return render_template("errors/500.html"), 500

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
