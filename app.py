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
            "errors": []
        }
        
        # Si l'OCR est désactivé en config, on skip
        if not AppConfig.OCR_ENABLED:
            return status
        
        try:
            import shutil
            import subprocess
            
            # Vérifier Tesseract
            tesseract_path = shutil.which("tesseract")
            status["tesseract"] = tesseract_path
            
            # Vérifier Poppler
            status["poppler"] = shutil.which("pdftoppm") or shutil.which("pdftocairo")
            
            # Vérifier pytesseract
            try:
                import pytesseract
                pytesseract_available = True
            except ImportError:
                pytesseract_available = False
                status["errors"].append("pytesseract non installé")
            
            # Si Tesseract est disponible, vérifier les langues
            if tesseract_path:
                try:
                    result = subprocess.run(
                        ["tesseract", "--list-langs"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        available_langs = result.stdout.strip().split('\n')
                        if len(available_langs) > 1:  # Skip first line "List of available languages"
                            available_langs = available_langs[1:]
                        status["lang_fra"] = any("fra" in lang for lang in available_langs)
                    else:
                        status["errors"].append(f"tesseract --list-langs failed: {result.stderr}")
                except FileNotFoundError:
                    status["errors"].append("tesseract command not found")
                except subprocess.TimeoutExpired:
                    status["errors"].append("tesseract timeout")
                except Exception as e:
                    status["errors"].append(f"tesseract check error: {str(e)}")
            else:
                status["errors"].append("tesseract not found in PATH")
            
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
    # TEST OCR (page de statut dynamique)
    # ========================================================
    @app.route('/test-ocr')
    def test_ocr():
        """Page de test pour vérifier l'état de l'OCR (statut réel)"""
        probe = _ocr_probe()
        ok = probe["enabled"] and probe["tesseract"] and probe["poppler"]
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Test OCR</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .status {{ padding: 18px; border-radius: 8px; margin-bottom: 16px; }}
                .ok {{ background:#d1fae5; color:#065f46; border:1px solid #10b981; }}
                .warn {{ background:#fef3c7; color:#92400e; border:1px solid #f59e0b; }}
                .err {{ background:#fee2e2; color:#991b1b; border:1px solid #ef4444; }}
                code, pre {{ background:#f8fafc; padding:8px 10px; border-radius:6px; display:inline-block; }}
                a {{ color:#2563eb; text-decoration:none; }}
                a:hover {{ text-decoration:underline; }}
            </style>
        </head>
        <body>
            <h1>État du service OCR (Render)</h1>
            <div class="status {'ok' if ok else 'err'}">
                <h3>{'✅ OCR opérationnel' if ok else '⚠️ OCR non opérationnel'}</h3>
                <ul>
                    <li>OCR activé (config) : <strong>{probe['enabled']}</strong></li>
                    <li>Tesseract : <strong>{probe['tesseract'] or '—'}</strong></li>
                    <li>Poppler (pdftoppm/pdftocairo) : <strong>{probe['poppler'] or '—'}</strong></li>
                    <li>Langue FRA : <strong>{'OK' if probe['lang_fra'] else '—'}</strong></li>
                </ul>
                {('<p class="warn">Ajoute/valide <code>aptPackages: [tesseract-ocr, tesseract-ocr-fra, poppler-utils]</code> dans <code>render.yaml</code> et <code>pytesseract</code>, <code>pdf2image</code> dans <code>requirements.txt</code>.</p>' if not ok else '')}
                {('<pre>' + str(probe['errors']) + '</pre>' if probe['errors'] else '')}
            </div>
            <p><a href="/">Accueil</a> • <a href="/conversion/">Outils de conversion</a></p>
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
