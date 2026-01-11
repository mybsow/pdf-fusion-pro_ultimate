#!/usr/bin/env python3
"""
PDF Fusion Pro Ultimate - Application principale
"""

from flask import Flask, render_template, jsonify, request, Response
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
import json
import os
from config import AppConfig
from blueprints.pdf import pdf_bp
from blueprints.api import api_bp
from blueprints.legal import legal_bp
from blueprints.stats import stats_bp
from utils.middleware import setup_middleware
from utils.stats_manager import stats_manager
from pathlib import Path

def init_app_dirs():
    """Crée les répertoires nécessaires"""
    directories = ['data/contacts', 'uploads', 'temp', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Dossier créé/vérifié: {directory}")

def create_app():
    """Factory pour créer l'application Flask"""
    # Initialiser la configuration
    AppConfig.initialize()
    
    # Créer les répertoires nécessaires
    init_app_dirs()
    
    # Créer l'application Flask
    app = Flask(__name__)
    app.secret_key = AppConfig.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
    
    # Middleware Proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Configurer le middleware avec l'instance stats_manager
    setup_middleware(app, stats_manager)

    # ============================================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================================
    
    # Blueprint principal (PDF tools)
    app.register_blueprint(pdf_bp)
    
    # Blueprint API
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Blueprint pages légales
    app.register_blueprint(legal_bp)
    
    # Blueprint statistiques
    app.register_blueprint(stats_bp)

@app.route('/admin/debug')
def admin_debug():
    """Page de debug pour vérifier la configuration"""
    import os
    import json
    
    info = {
        'service': 'PDF Fusion Pro Ultimate',
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'ADMIN_PASSWORD_set': bool(os.environ.get('ADMIN_PASSWORD')),
            'ADMIN_PASSWORD_length': len(os.environ.get('ADMIN_PASSWORD', '')) if os.environ.get('ADMIN_PASSWORD') else 0,
            'RENDER': bool(os.environ.get('RENDER')),
            'RENDER_EXTERNAL_URL': os.environ.get('RENDER_EXTERNAL_URL', 'Non défini'),
            'RENDER_SERVICE_ID': os.environ.get('RENDER_SERVICE_ID', 'Non défini'),
            'all_env_vars': dict(os.environ)  # Attention: montre toutes les variables
        },
        'routes': [
            '/admin/messages',
            '/admin/ratings',
            '/api/rating',
            '/contact',
            '/mentions-legales'
        ]
    }
    
    # Cacher les valeurs sensibles
    if info['environment']['ADMIN_PASSWORD_set']:
        info['environment']['ADMIN_PASSWORD_preview'] = os.environ.get('ADMIN_PASSWORD', '')[0] + '***' + os.environ.get('ADMIN_PASSWORD', '')[-1] if len(os.environ.get('ADMIN_PASSWORD', '')) > 2 else '***'
    
    return jsonify(info)    

    # ============================================================
    # ROUTE D'ÉVALUATION
    # ============================================================
    
    @app.route('/api/rating', methods=['POST'])
    def submit_rating():
        """API pour enregistrer les évaluations"""
        try:
            data = request.get_json()
            
            # Validation
            if not data or 'rating' not in data:
                return jsonify({"error": "Données manquantes"}), 400
            
            rating = int(data.get('rating', 0))
            if rating < 1 or rating > 5:
                return jsonify({"error": "Évaluation invalide"}), 400
            
            feedback = data.get('feedback', '')
            
            # ============================================
            # EN PRODUCTION SUR RENDER :
            # ============================================
            
            # Option 1 : Envoyer un email (recommandé pour Render)
            send_rating_email(rating, feedback, data)
            
            # Option 2 : Logger dans la console (visible dans les logs Render)
            print(f"📊 Évaluation reçue : {rating} étoiles - Feedback: {feedback[:100]}")
            
            # Option 3 : Sauvegarder temporairement (sera perdu au redéploiement)
            try:
                rating_data = {
                    'rating': rating,
                    'feedback': feedback,
                    'page': data.get('page', '/'),
                    'user_agent': data.get('user_agent', ''),
                    'timestamp': datetime.now().isoformat(),
                    'ip': request.remote_addr
                }
                
                ratings_file = 'data/ratings.json'
                os.makedirs('data', exist_ok=True)
                
                ratings = []
                if os.path.exists(ratings_file):
                    with open(ratings_file, 'r', encoding='utf-8') as f:
                        try:
                            ratings = json.load(f)
                        except:
                            ratings = []
                
                ratings.append(rating_data)
                
                with open(ratings_file, 'w', encoding='utf-8') as f:
                    json.dump(ratings, f, indent=2, ensure_ascii=False)
                    
            except Exception as file_error:
                print(f"⚠️ Impossible de sauvegarder le fichier: {file_error}")
            
            return jsonify({
                "success": True,
                "message": "Évaluation enregistrée",
                "average": 0  # Temporaire, car pas de données persistantes
            })
        
        except Exception as e:
            print(f"❌ Erreur enregistrement évaluation: {e}")
            return jsonify({"error": "Erreur interne"}), 500
    
    # ============================================================
    # ROUTES SPÉCIALES (fichiers statiques)
    # ============================================================
    
    @app.route('/admin/ratings')
    def view_ratings():
        # Ajoutez une vérification de sécurité ici
        with open('data/ratings.json', 'r') as f:
            ratings = json.load(f)
        
        # Calculez les statistiques
        return render_template('admin/ratings.html', ratings=ratings)

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
        """Génère un sitemap XML amélioré"""
        base_url = "https://pdf-fusion-pro-ultimate.onrender.com"
        
        # Pages principales AVEC PRIORITÉ ADAPTÉE
        pages = [
            # (chemin, dernière_modification, fréquence, priorité)
            ("/", datetime.now().strftime('%Y-%m-%d'), "daily", 1.0),  # Page d'accueil
            ("/fusion-pdf", datetime.now().strftime('%Y-%m-%d'), "daily", 0.9),
            ("/division-pdf", datetime.now().strftime('%Y-%m-%d'), "daily", 0.9),
            ("/rotation-pdf", datetime.now().strftime('%Y-%m-%d'), "daily", 0.9),
            ("/compression-pdf", datetime.now().strftime('%Y-%m-%d'), "daily", 0.9),
            ("/contact", datetime.now().strftime('%Y-%m-%d'), "weekly", 0.7),  # Contact important
            ("/a-propos", datetime.now().strftime('%Y-%m-%d'), "monthly", 0.6),  # À propos
            ("/mentions-legales", "2024-01-15", "monthly", 0.3),
            ("/politique-confidentialite", "2024-01-15", "monthly", 0.3),
            ("/conditions-utilisation", "2024-01-15", "monthly", 0.3),
        ]
        
        # AJOUTER LES ROUTES API (optionnel mais recommandé pour le SEO technique)
        api_pages = [
            ("/health", datetime.now().strftime('%Y-%m-%d'), "daily", 0.1),  # Endpoint santé
        ]
        
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        xml += '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        xml += '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n'
        xml += '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n'
        
        # Ajouter toutes les pages principales
        for path, lastmod, changefreq, priority in pages:
            xml += '  <url>\n'
            xml += f'    <loc>{base_url}{path}</loc>\n'
            xml += f'    <lastmod>{lastmod}</lastmod>\n'
            xml += f'    <changefreq>{changefreq}</changefreq>\n'
            xml += f'    <priority>{priority:.1f}</priority>\n'
            xml += '  </url>\n'
        
        # Ajouter les pages API (priorité plus basse)
        for path, lastmod, changefreq, priority in api_pages:
            xml += '  <url>\n'
            xml += f'    <loc>{base_url}{path}</loc>\n'
            xml += f'    <lastmod>{lastmod}</lastmod>\n'
            xml += f'    <changefreq>{changefreq}</changefreq>\n'
            xml += f'    <priority>{priority:.1f}</priority>\n'
            xml += '  </url>\n'
        
        xml += '</urlset>'
        
        return Response(xml, mimetype="application/xml", headers={
            'Cache-Control': 'public, max-age=86400'
        })
    
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
                .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; 
                       text-decoration: none; border-radius: 5px; margin-top: 20px; }
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
                .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; 
                       text-decoration: none; border-radius: 5px; margin-top: 20px; }
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
                <a href="/contact" class="btn" style="background: #2ecc71; margin-left: 10px;">Signaler ce problème</a>
            </div>
        </body>
        </html>
        """, 500
    
    return app

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
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true',
        use_reloader=True
    )

# Variable pour gunicorn (pour le déploiement)
app = create_app()