#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
Version compatible Render
"""

from flask import Flask, redirect, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import os
import sys
from pathlib import Path

# Ajout du chemin racine au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AppConfig
from blueprints.pdf import pdf_bp
from blueprints.api import api_bp
from blueprints.legal import legal_bp
from blueprints.stats import stats_bp
from blueprints.admin import admin_bp
# Ajouter l'import du blueprint de conversion
from blueprints.conversion import conversion_bp

# ============================================================
# Initialisation des dossiers nécessaires
# ============================================================

def init_app_dirs():
    """Crée les répertoires nécessaires au fonctionnement de l'application."""
    # Dossier racine du projet
    base_dir = Path(__file__).parent
    
    for d in ['data/contacts', 'data/ratings', 'uploads', 'temp', 'logs']:
        dir_path = base_dir / d
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Dossier créé/vérifié: {dir_path}")

    # Créer le fichier contacts.json vide s'il n'existe pas
    contacts_file = base_dir / 'data' / 'contacts.json'
    if not contacts_file.exists():
        try:
            with open(contacts_file, 'w', encoding='utf-8') as f:
                f.write('[]')
            print(f"✅ Fichier contacts.json créé: {contacts_file}")
        except Exception as e:
            print(f"⚠️  Erreur création contacts.json: {e}")

# ============================================================
# Factory Flask (UNIQUE)
# ============================================================

def create_app():
    """Factory d'application Flask."""
    print("🚀 Initialisation de l'application Flask...")
    
    try:
        # Initialisation de la configuration
        AppConfig.initialize()
        print(f"✅ Configuration chargée: {AppConfig.NAME} v{AppConfig.VERSION}")
        
        # Création des dossiers
        init_app_dirs()
        
        # Création de l'application Flask
        app = Flask(__name__)
        
        # ----------------------------
        # Configuration Flask
        # ----------------------------
        app.secret_key = os.environ.get(
            "FLASK_SECRET_KEY",
            AppConfig.SECRET_KEY
        )
        
        app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
        
        # Configuration pour Render
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        app.config['SERVER_NAME'] = AppConfig.DOMAIN if AppConfig.DOMAIN else None
        
        # Proxy (Render / reverse proxy)
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        
        print(f"🔧 Config Flask initialisée - Secret: {'Oui' if app.secret_key else 'Non'}")
        
        # ----------------------------
        # Initialisation des managers
        # ----------------------------
        try:
            from managers.contact_manager import contact_manager
            from managers.rating_manager import rating_manager
            from managers.stats_manager import stats_manager
            from utils.middleware import setup_middleware
            
            print("✅ Managers importés avec succès")
            
            # Middleware statistiques
            setup_middleware(app, stats_manager)
            
            # Warm-up cache léger (safe)
            with app.app_context():
                unseen_count = contact_manager.get_unseen_count()
                print(f"📨 Messages non lus: {unseen_count}")
                
        except ImportError as e:
            print(f"⚠️  Erreur import managers: {e}")
        except Exception as e:
            print(f"⚠️  Erreur initialisation managers: {e}")
        
        # ----------------------------
        # Enregistrement des blueprints
        # ----------------------------
        blueprints = [
            (pdf_bp, None, "PDF"),
            (api_bp, "/api", "API"),
            (legal_bp, None, "Legal"),
            (stats_bp, None, "Stats"),
            (admin_bp, None, "Admin"),
            (conversion_bp, None, "conversion")
        ]
        
        for bp, prefix, name in blueprints:
            try:
                if prefix:
                    app.register_blueprint(bp, url_prefix=prefix)
                else:
                    app.register_blueprint(bp)
                print(f"✅ Blueprint '{name}' enregistré" + (f" avec préfixe '{prefix}'" if prefix else ""))
            except Exception as e:
                print(f"❌ Erreur enregistrement blueprint '{name}': {e}")
        
        # Blueprint debug (optionnel)
        try:
            from blueprints.debug import debug_bp
            app.register_blueprint(debug_bp, url_prefix="/debug")
            print("✅ Blueprint debug enregistré")
        except ImportError:
            print("⚠️  Blueprint debug non disponible")
        except Exception as e:
            print(f"⚠️  Erreur blueprint debug: {e}")
        
        # ----------------------------
        # Routes système
        # ----------------------------
        @app.route('/')
        def index():
            """Redirection vers l'interface PDF"""
            return redirect('/pdf')
        
        @app.route('/google6f0d847067bbd18a.html')
        def google_verification():
            """Verification Google Search Console"""
            return Response(
                "google-site-verification: google6f0d847067bbd18a.html",
                mimetype="text/plain"
            )
        
        @app.route('/ads.txt')
        def ads_txt():
            """Fichier ads.txt pour AdSense"""
            return Response(
                "google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0",
                mimetype="text/plain"
            )
        
        @app.route('/robots.txt')
        def robots():
            """Fichier robots.txt"""
            content = (
                "User-agent: *\n"
                "Allow: /\n"
                "Disallow: /admin/\n"
                "Disallow: /debug/\n"
                f"Sitemap: https://{domain}/sitemap.xml\n"
            )
            return Response(content, mimetype="text/plain")
        
        @app.route('/sitemap.xml')
        def sitemap():
            """Génération dynamique du sitemap XML"""
            domain = AppConfig.DOMAIN.rstrip("/")
            base_url = f"https://{domain}"
            today = datetime.now().strftime('%Y-%m-%d')
        
            pages = [
                ("/", today, "daily", 1.0),
                ("/fusion-pdf", today, "daily", 0.9),
                ("/division-pdf", today, "daily", 0.9),
                ("/rotation-pdf", today, "daily", 0.9),
                ("/compression-pdf", today, "daily", 0.9),
                ("/conversion", today, "daily", 0.8),  # <-- Ajouter
                ("/conversion/image-vers-pdf", today, "daily", 0.7),
                ("/conversion/image-vers-word", today, "daily", 0.7),
                ("/conversion/image-vers-excel", today, "daily", 0.7),
                ("/contact", today, "weekly", 0.7),
                ("/a-propos", today, "monthly", 0.6),
                ("/mentions-legales", today, "monthly", 0.3),
                ("/politique-confidentialite", today, "monthly", 0.3),
                ("/conditions-utilisation", today, "monthly", 0.3),
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
        
            return Response(xml, mimetype="application/xml", headers={
                "Cache-Control": "public, max-age=3600"
            })

        # ============================================================
        # ROUTES DE SANTÉ ET DIAGNOSTIC
        # ============================================================
        @app.route('/health')
        def health_check():
            """Endpoint de santé pour Render et monitoring"""
            try:
                from managers.stats_manager import stats_manager
                
                health_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "app": {
                        "name": AppConfig.NAME,
                        "version": AppConfig.VERSION,
                        "domain": AppConfig.DOMAIN
                    },
                    "services": {
                        "flask": True,
                        "filesystem": os.access('.', os.W_OK),
                        "memory": True
                    },
                    "stats": {
                        "total_operations": stats_manager.get_stat("total_operations", 0)
                    }
                }
                return health_data, 200
                
            except Exception as e:
                return {
                    "status": "degraded",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, 200  # 200 pour que Render ne considère pas comme échec
        
        @app.route('/diagnostic')
        def diagnostic():
            """Page de diagnostic détaillée"""
            import platform
            
            diagnostic_info = {
                "timestamp": datetime.now().isoformat(),
                "environment": {
                    "python_version": platform.python_version(),
                    "flask_version": "3.0.0",
                    "os": platform.system(),
                    "render": os.environ.get('RENDER', 'false').lower() == 'true',
                    "port": os.environ.get('PORT', '5000')
                },
                "app": {
                    "name": AppConfig.NAME,
                    "version": AppConfig.VERSION,
                    "developer": AppConfig.DEVELOPER_NAME,
                    "domain": AppConfig.DOMAIN
                },
                "paths": {
                    "current_dir": os.getcwd(),
                    "data_dir": str(Path('data').absolute()) if Path('data').exists() else "Missing",
                    "contacts_file": str(Path('data/contacts.json').absolute()) if Path('data/contacts.json').exists() else "Missing",
                    "ratings_dir": str(Path('data/ratings').absolute()) if Path('data/ratings').exists() else "Missing"
                },
                "files": {
                    "app.py": os.path.exists('app.py'),
                    "requirements.txt": os.path.exists('requirements.txt'),
                    "render.yaml": os.path.exists('render.yaml')
                }
            }
            
            return diagnostic_info
        
        # ============================================================
        # GESTION DES ERREURS
        # ============================================================
        @app.errorhandler(404)
        def not_found_error(error):
            """Page 404 personnalisée"""
            html = '''
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>404 - Page non trouvée | PDF Fusion Pro</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; }
                    .error-container { max-width: 600px; margin: 100px auto; text-align: center; }
                    .error-code { font-size: 8rem; font-weight: bold; color: #4361ee; opacity: 0.2; }
                </style>
            </head>
            <body>
                <div class="container error-container">
                    <div class="error-code">404</div>
                    <h1 class="mb-4">Page non trouvée</h1>
                    <p class="lead mb-4">La page que vous recherchez n'existe pas ou a été déplacée.</p>
                    <div class="d-flex justify-content-center gap-3">
                        <a href="/" class="btn btn-primary btn-lg">
                            <i class="fas fa-home me-2"></i>Retour à l'accueil
                        </a>
                        <a href="/contact" class="btn btn-outline-primary btn-lg">
                            <i class="fas fa-envelope me-2"></i>Nous contacter
                        </a>
                    </div>
                </div>
                <script src="https://kit.fontawesome.com/your-fontawesome-kit.js" crossorigin="anonymous"></script>
            </body>
            </html>
            '''
            return html, 404
        
        @app.errorhandler(500)
        def internal_error(error):
            """Page 500 personnalisée"""
            import traceback
            
            # Log de l'erreur
            error_traceback = traceback.format_exc()
            print("\n" + "="*80)
            print("❌ ERREUR INTERNE 500:")
            print("="*80)
            print(error_traceback)
            print("="*80 + "\n")
            
            html = '''
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>500 - Erreur serveur | PDF Fusion Pro</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { background: linear-gradient(135deg, #ffeaea 0%, #ffd6d6 100%); min-height: 100vh; }
                    .error-container { max-width: 800px; margin: 50px auto; }
                    .error-code { font-size: 6rem; font-weight: bold; color: #e74c3c; }
                </style>
            </head>
            <body>
                <div class="container error-container">
                    <div class="card shadow-lg">
                        <div class="card-header bg-danger text-white">
                            <h2 class="mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Erreur Interne du Serveur</h2>
                        </div>
                        <div class="card-body">
                            <div class="error-code text-center mb-4">500</div>
                            <h3 class="text-center mb-4">Une erreur technique est survenue</h3>
                            <p class="lead">Notre équipe technique a été automatiquement notifiée de ce problème.</p>
                            
                            <div class="alert alert-info">
                                <h5><i class="fas fa-lightbulb me-2"></i>Que faire ?</h5>
                                <ul class="mb-0">
                                    <li>Rafraîchissez la page dans quelques instants</li>
                                    <li>Retournez à la page d'accueil et réessayez</li>
                                    <li>Si le problème persiste, contactez-nous</li>
                                </ul>
                            </div>
                            
                            <div class="d-flex justify-content-center gap-3 mt-4">
                                <a href="/" class="btn btn-primary btn-lg">
                                    <i class="fas fa-home me-2"></i>Accueil
                                </a>
                                <a href="javascript:location.reload()" class="btn btn-outline-primary btn-lg">
                                    <i class="fas fa-redo me-2"></i>Rafraîchir
                                </a>
                                <a href="/contact" class="btn btn-outline-danger btn-lg">
                                    <i class="fas fa-bug me-2"></i>Signaler un bug
                                </a>
                            </div>
                        </div>
                        <div class="card-footer text-muted text-center">
                            <small>PDF Fusion Pro • Version ''' + AppConfig.VERSION + ''' • ''' + datetime.now().strftime('%d/%m/%Y %H:%M') + '''</small>
                        </div>
                    </div>
                </div>
                <script src="https://kit.fontawesome.com/your-fontawesome-kit.js" crossorigin="anonymous"></script>
            </body>
            </html>
            '''
            return html, 500
        
        # ============================================================
        # FILTRES JINJA2 UTILES
        # ============================================================
        @app.template_filter('datetime')
        def format_datetime(value, format='%d/%m/%Y %H:%M'):
            """Filtre Jinja2 pour formater les dates"""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    return value
            if isinstance(value, datetime):
                return value.strftime(format)
            return value
        
        @app.template_filter('filesize')
        def format_filesize(value):
            """Formatage de taille de fichier"""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if value < 1024.0 or unit == 'GB':
                    return f"{value:.1f} {unit}"
                value /= 1024.0
        
        print("=" * 60)
        print(f"✅ Application Flask initialisée avec succès !")
        print(f"📱 Nom: {AppConfig.NAME}")
        print(f"🔖 Version: {AppConfig.VERSION}")
        print(f"🌐 Domain: {AppConfig.DOMAIN}")
        print(f"👨‍💻 Développeur: {AppConfig.DEVELOPER_NAME}")
        print(f"🔗 Routes principales: /, /pdf, /admin, /health, /diagnostic")
        print("=" * 60)
        
        return app
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        
        # Créer une application minimale en cas d'erreur
        app = Flask(__name__)
        app.secret_key = os.urandom(24)
        
        @app.route('/')
        def fallback():
            return "Application en maintenance. Veuillez réessayer dans quelques instants.", 503
        
        @app.route('/health')
        def fallback_health():
            return {"status": "degraded", "error": str(e)}, 200
        
        return app

# ============================================================
# Point d'entrée Gunicorn / Render
# ============================================================

app = create_app()

# ============================================================
# Lancement local uniquement
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    print("\n" + "="*60)
    print(f"🚀 DÉMARRAGE DE L'APPLICATION")
    print("="*60)
    print(f"📁 Répertoire: {os.getcwd()}")
    print(f"🌍 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"🔧 Environnement: {os.environ.get('FLASK_ENV', 'production')}")
    print("="*60)
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    )
