def create_app():
    """Factory pour créer l'application Flask"""
    # Initialiser la configuration
    AppConfig.initialize()
    
    # Créer l'application Flask
    app = Flask(__name__)
    app.secret_key = AppConfig.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
    
    # Middleware Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Configurer le middleware avec l'instance stats_manager
    setup_middleware(app, stats_manager)  # Passez l'instance ici

    # Handler pour les erreurs 500 avec traceback
    @app.errorhandler(500)
    def internal_server_error(e):
        import traceback
        error_traceback = traceback.format_exc()
        
        # Affiche dans les logs
        print("\n" + "="*80)
        print("TRACEBACK DE L'ERREUR 500:")
        print("="*80)
        print(error_traceback)
        print("="*80 + "\n")
        
        # Retourne une page d'erreur
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>500 - Erreur Interne</title></head>
        <body style="font-family: monospace; padding: 20px;">
            <h1 style="color: red;">500 - Erreur Interne du Serveur</h1>
            <h2>Détails de l'erreur:</h2>
            <pre style="background: #f0f0f0; padding: 15px; border: 1px solid #ccc; overflow: auto;">
            {str(e)}
            
            {error_traceback}
            </pre>
            <p><a href="/">Retour à l'accueil</a></p>
        </body>
        </html>
        """, 500

    # ============================================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================================
    
    # Blueprint principal (PDF tools)
    app.register_blueprint(pdf_bp)
    
    # Blueprint API
    app.register_blueprint(api_bp)
    
    # Blueprint pages légales
    app.register_blueprint(legal_bp)
    
    # Blueprint statistiques
    app.register_blueprint(stats_bp)
    
    # ============================================================
    # ROUTES SPÉCIALES (fichiers statiques)
    # ============================================================
    
    @app.route('/google6f0d847067bbd18a.html')
    def google_verification():
        """Page de vérification Google Search Console"""
        verification_content = "google-site-verification: google6f0d847067bbd18a.html"
        return Response(verification_content, mimetype='text/html')
    
    @app.route('/ads.txt')
    def ads_txt():
        """Fichier ads.txt pour AdSense"""
        ads_content = "google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0"
        return Response(ads_content, mimetype='text/plain')
    
# Route racine qui redirige vers le blueprint PDF
    @app.route('/')
    def root():
        from flask import redirect
        return redirect('/pdf/')  # Redirige vers le blueprint PDF

    # OU directement affiche la même page
    @app.route('/')
    def index():
        # Importez et utilisez la même fonction que le blueprint
        from blueprints.pdf.routes import home
        return home()

    @app.route('/robots.txt')
    def robots():
        """Fichier robots.txt"""
        content = "User-agent: *\n"
        content += "Allow: /\n"
        content += f"Sitemap: https://{AppConfig.DOMAIN}/sitemap.xml\n"
        content += "\n"
        content += f"# {AppConfig.NAME} - Développé par {AppConfig.DEVELOPER_NAME}\n"
        
        return Response(content, mimetype="text/plain")
    
    @app.route('/sitemap.xml')
    def sitemap():
        """Génère un sitemap XML"""
        base_url = f"https://{AppConfig.DOMAIN}"
        pages = [
            ("/", datetime.now().strftime('%Y-%m-%d'), "daily", 1.0),
            ("/mentions-legales", "2024-01-15", "monthly", 0.8),
            ("/politique-confidentialite", "2024-01-15", "monthly", 0.8),
            ("/conditions-utilisation", "2024-01-15", "monthly", 0.8),
            ("/contact", "2024-01-15", "monthly", 0.7),
            ("/a-propos", "2024-01-15", "monthly", 0.7),
        ]
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for path, lastmod, changefreq, priority in pages:
            xml += f'  <url>\n'
            xml += f'    <loc>{base_url}{path}</loc>\n'
            xml += f'    <lastmod>{lastmod}</lastmod>\n'
            xml += f'    <changefreq>{changefreq}</changefreq>\n'
            xml += f'    <priority>{priority}</priority>\n'
            xml += f'  </url>\n'
        
        xml += '</urlset>'
        
        return Response(xml, mimetype="application/xml")
    
    # ============================================================
    # GESTION DES ERREURS
    # ============================================================
    
    @app.errorhandler(404)
    def not_found_error(error):
        return "<h1>404 - Page non trouvée</h1><p>La page que vous recherchez n'existe pas.</p>", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return "<h1>500 - Erreur interne</h1><p>Une erreur s'est produite sur le serveur.</p>", 500
    
    return app  # ⬅️ ⬅️ ⬅️ **RETOUR ICI, À LA FIN !**

    # ============================================================
# IMPORTATIONS (doivent être en haut du fichier)
# ============================================================
from flask import Flask, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from config import AppConfig
from blueprints.pdf import pdf_bp
from blueprints.api import api_bp
from blueprints.legal import legal_bp
from blueprints.stats import stats_bp
from utils.middleware import setup_middleware
from utils.stats_manager import stats_manager

# ============================================================
# DÉMARRAGE DE L'APPLICATION
# ============================================================

if __name__ == '__main__':
    print("🚀 Démarrage de PDF Fusion Pro Ultimate...")
    print(f"📊 Version: {AppConfig.VERSION}")
    print(f"🌐 Domaine: {AppConfig.DOMAIN}")
    print("=" * 50)
    
    # Créer l'application
    app = create_app()
    
    # Démarrer le serveur
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )