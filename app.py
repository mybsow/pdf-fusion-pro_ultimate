#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
"""

from flask import Flask, redirect, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import os
from pathlib import Path

from config import AppConfig
from blueprints.pdf import pdf_bp
from blueprints.api import api_bp
from blueprints.legal import legal_bp
from blueprints.stats import stats_bp
from blueprints.admin import admin_bp
from utils.middleware import setup_middleware


# ============================================================
# Initialisation des dossiers nécessaires
# ============================================================

def init_app_dirs():
    """Crée les répertoires nécessaires au fonctionnement de l'application."""
    for d in ['data/contacts', 'uploads', 'temp', 'logs']:
        Path(d).mkdir(parents=True, exist_ok=True)


# ============================================================
# Factory Flask (UNIQUE)
# ============================================================

def create_app():
    """Factory d'application Flask."""
    AppConfig.initialize()
    init_app_dirs()

    app = Flask(__name__)

    # ----------------------------
    # Configuration Flask
    # ----------------------------
    app.secret_key = os.environ.get(
        "FLASK_SECRET_KEY",
        AppConfig.SECRET_KEY
    )

    app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE

    # Proxy (Render / reverse proxy)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    # ----------------------------
    # Initialisation des managers
    # ----------------------------
    from managers.contact_manager import contact_manager
    from managers.rating_manager import rating_manager
    from managers.stats_manager import stats_manager

    # Middleware statistiques
    setup_middleware(app, stats_manager)

    # Warm-up cache léger (safe)
    with app.app_context():
        contact_manager.get_unseen_count()

    # ----------------------------
    # Enregistrement des blueprints
    # ----------------------------
    app.register_blueprint(pdf_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(legal_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(admin_bp)   # /admin/*

    # ----------------------------
    # Routes système
    # ----------------------------
    @app.route('/')
    def index():
        return redirect('/pdf')

    @app.route('/google6f0d847067bbd18a.html')
    def google_verification():
        return Response(
            "google-site-verification: google6f0d847067bbd18a.html",
            mimetype="text/html"
        )

    @app.route('/ads.txt')
    def ads_txt():
        return Response(
            "google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0",
            mimetype="text/plain"
        )

    @app.route('/robots.txt')
    def robots():
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: https://{AppConfig.DOMAIN}/sitemap.xml\n"
        )
        return Response(content, mimetype="text/plain")

    @app.route('/sitemap.xml')
    def sitemap():
        base_url = f"https://{AppConfig.DOMAIN}"
        today = datetime.now().strftime('%Y-%m-%d')

        pages = [
            ("/", today, "daily", 1.0),
            ("/fusion-pdf", today, "daily", 0.9),
            ("/division-pdf", today, "daily", 0.9),
            ("/rotation-pdf", today, "daily", 0.9),
            ("/compression-pdf", today, "daily", 0.9),
            ("/contact", today, "weekly", 0.7),
            ("/a-propos", today, "monthly", 0.6),
            ("/mentions-legales", "2024-01-15", "monthly", 0.3),
            ("/politique-confidentialite", "2024-01-15", "monthly", 0.3),
            ("/conditions-utilisation", "2024-01-15", "monthly", 0.3),
        ]

        # AJOUTER LES ROUTES API (optionnel mais recommandé pour le SEO technique)
        api_pages = [
            ("/health", datetime.now().strftime('%Y-%m-%d'), "daily", 0.1),
        ]        
            
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        xml += '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        xml += '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n'
        xml += '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n'

        for path, lastmod, freq, prio in pages:
            xml += (
                "  <url>\n"
                f"    <loc>{base_url}{path}</loc>\n"
                f"    <lastmod>{lastmod}</lastmod>\n"
                f"    <changefreq>{freq}</changefreq>\n"
                f"    <priority>{prio}</priority>\n"
                "  </url>\n"
            )

        xml += '</urlset>'
        return Response(xml, mimetype="application/xml")

    # ============================================================
    # GESTION DES ERREURS
    # ============================================================
    @app.errorhandler(404)
    def not_found_error(error):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Page non trouvée</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #e74c3c; }
                .container { max-width: 600px; margin: 0 auto; }
                .btn { display: inline-block; padding: 10px 20px; background: #3498db; 
                       color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>404 - Page non trouvée</h1>
                <p>La page que vous recherchez n'existe pas.</p>
                <a href="/" class="btn">Retour à l'accueil</a>
            </div>
        </body>
        </html>
        """, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        
        # Log l'erreur
        error_traceback = traceback.format_exc()
        print("\n" + "="*80)
        print("TRACEBACK DE L'ERREUR 500:")
        print("="*80)
        print(error_traceback)
        print("="*80 + "\n")
        
        # Page d'erreur pour l'utilisateur
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>500 - Erreur Interne</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #e74c3c; }
                .container { max-width: 600px; margin: 0 auto; }
                .btn { display: inline-block; padding: 10px 20px; background: #3498db; 
                       color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
                .error-details { background: #f8f9fa; padding: 15px; border-radius: 5px; 
                                margin-top: 20px; text-align: left; font-family: monospace; 
                                font-size: 12px; overflow: auto; max-height: 200px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>500 - Erreur Interne du Serveur</h1>
                <p>Une erreur s'est produite sur le serveur. L'équipe technique a été notifiée.</p>
                
                <div class="error-details">
                    <strong>Détails :</strong><br>
                    <pre style="margin: 0;">""" + str(error)[:500] + """</pre>
                </div>
                
                <a href="/" class="btn">Retour à l'accueil</a>
                <a href="/contact" class="btn" style="background: #2ecc71; margin-left: 10px;">
                    Signaler ce problème
                </a>
            </div>
        </body>
        </html>
        """, 500

    return app


# ============================================================
# Point d'entrée Gunicorn / Render
# ============================================================

app = create_app()


# ============================================================
# Lancement local uniquement
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    )
