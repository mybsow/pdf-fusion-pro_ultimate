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
    # CORRECTION ROUTE /conversion
    # ========================================================
    # Le blueprint conversion_bp est enregistré avec le préfixe /conversion
    # Mais certaines routes peuvent avoir un double /conversion/conversion
    # Cette redirection corrige le problème
    @app.route('/conversion')
    def redirect_conversion():
        """Redirige /conversion vers /conversion/ (avec slash)"""
        return redirect('/conversion/')

    # ========================================================
    # OCR ENDPOINT (désactivé sur Render)
    # ========================================================
    @app.route('/ocr-to-excel', methods=['POST'])
    def ocr_to_excel_endpoint():
        """Endpoint pour la conversion OCR vers Excel (désactivé sur Render)"""
        return jsonify({
            "error": "OCR non disponible sur le serveur cloud",
            "solution": "Pour utiliser l'OCR, téléchargez et exécutez l'application localement",
            "instructions": "1. Clonez le dépôt GitHub\n2. Installez Tesseract OCR sur votre machine\n3. Exécutez: pip install pytesseract pillow pandas openpyxl\n4. Lancez l'application localement"
        }), 503

    # ========================================================
    # TEST OCR
    # ========================================================
    @app.route('/test-ocr')
    def test_ocr():
        """Page de test pour vérifier l'état de l'OCR"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test OCR</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status { padding: 20px; margin: 20px 0; border-radius: 5px; }
                .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            </style>
        </head>
        <body>
            <h1>État du service OCR sur Render</h1>
            <div class="status error">
                <h3>⚠️ OCR NON DISPONIBLE sur le serveur cloud</h3>
                <p>L'OCR (Tesseract) ne peut pas être installé sur Render en raison de limitations techniques.</p>
            </div>
            <div class="status info">
                <h3>✅ Solution : Utilisation locale</h3>
                <p>Pour utiliser l'OCR :</p>
                <ol>
                    <li>Téléchargez le code depuis GitHub</li>
                    <li>Installez Tesseract OCR sur votre ordinateur</li>
                    <li>Exécutez l'application localement</li>
                </ol>
                <p><strong>Commandes d'installation locale :</strong></p>
                <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
# 1. Installer Tesseract (Windows)
# Téléchargez depuis: https://github.com/UB-Mannheim/tesseract/wiki

# 2. Installer les dépendances Python
pip install pytesseract pillow pandas openpyxl flask

# 3. Lancer l'application
python app.py</pre>
            </div>
            <div class="status info">
                <h3>🔗 Liens utiles</h3>
                <ul>
                    <li><a href="/">Accueil</a></li>
                    <li><a href="/conversion/">Outils de conversion</a></li>
                    <li><a href="https://github.com/mybsow/pdf-fusion-pro_ultimate">Code source GitHub</a></li>
                </ul>
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
        return jsonify({
            "status": "healthy",
            "app": AppConfig.NAME,
            "version": AppConfig.VERSION,
            "ocr_available": False,
            "message": "Application déployée avec succès sur Render. OCR désactivé (nécessite installation locale)."
        }), 200

    # ========================================================
    # DEBUG ROUTES
    # ========================================================

    @app.route('/debug/static-files')
    def debug_static_files():
        """Vérifier les fichiers statiques"""
        import os
        from pathlib import Path
        
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
    logger.info(f"   - Health: /health")

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
