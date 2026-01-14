from flask import Blueprint, request, jsonify, redirect
from datetime import datetime
import os
from rating_manager import ratings_manager
from utils.stats_manager import stats_manager
from config import AppConfig

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ============================================================
    # ROUTES PRINCIPALES (TOUTES LES ROUTES DOIVENT ÊTRE ICI)
    # ============================================================
    
    @admin_bp.route('/debug')
    def admin_debug():
        """Page de debug pour vérifier la configuration"""
        info = {
            'service': 'PDF Fusion Pro Ultimate',
            'timestamp': datetime.now().isoformat(),
            'environment': {
                'ADMIN_PASSWORD_set': bool(os.environ.get('ADMIN_PASSWORD')),
                'ADMIN_PASSWORD_length': len(os.environ.get('ADMIN_PASSWORD', '')) if os.environ.get('ADMIN_PASSWORD') else 0,
                'RENDER': bool(os.environ.get('RENDER')),
                'RENDER_EXTERNAL_URL': os.environ.get('RENDER_EXTERNAL_URL', 'Non défini'),
                'RENDER_SERVICE_ID': os.environ.get('RENDER_SERVICE_ID', 'Non défini'),
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
            password = os.environ.get('ADMIN_PASSWORD', '')
            if len(password) > 2:
                info['environment']['ADMIN_PASSWORD_preview'] = password[0] + '***' + password[-1]
            else:
                info['environment']['ADMIN_PASSWORD_preview'] = '***'
        
        return jsonify(info)
    
    @admin_bp.route('/ratings')
    def admin_ratings():
        """Interface admin pour voir les évaluations"""
        
        # Vérification du mot de passe admin
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if request.args.get('password') != admin_password:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Accès Admin - Évaluations</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
                <style>
                    body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; 
                          display: flex; align-items: center; justify-content: center; font-family: 'Segoe UI'; }
                    .login-box { background: white; border-radius: 20px; padding: 2.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.1); max-width: 400px; }
                    .app-icon { width: 80px; height: 80px; background: linear-gradient(135deg, #4361ee, #3a0ca3);
                               border-radius: 50%; display: flex; align-items: center; justify-content: center;
                               color: white; font-size: 2rem; margin: 0 auto 1.5rem; }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <div class="app-icon"><i class="fas fa-star"></i></div>
                    <h2 class="text-center mb-4">Évaluations - Admin</h2>
                    <form method="GET" action="/admin/ratings">
                        <div class="mb-3">
                            <label for="password" class="form-label">Mot de passe admin</label>
                            <input type="password" class="form-control" id="password" name="password" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-sign-in-alt me-1"></i> Se connecter
                        </button>
                    </form>
                </div>
            </body>
            </html>
            """, 401
        
        # Récupérer les données
        ratings = ratings_manager.get_all_ratings()
        stats = ratings_manager.get_stats()
        
        # Fonction helper pour time_ago
        def time_ago(date_obj):
            """Retourne une chaîne "il y a X temps" """
            now = datetime.now()
            diff = now - date_obj
            
            if diff.days > 365:
                years = diff.days // 365
                return f"il y a {years} an{'s' if years > 1 else ''}"
            elif diff.days > 30:
                months = diff.days // 30
                return f"il y a {months} mois"
            elif diff.days > 0:
                return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"il y a {hours} heure{'s' if hours > 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
            else:
                return "à l'instant"
        
        # Générer l'interface HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Évaluations - Admin</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                :root {{
                    --primary-color: #4361ee;
                    --secondary-color: #3a0ca3;
                    --success-color: #2ecc71;
                    --warning-color: #f39c12;
                    --danger-color: #e74c3c;
                }}
                
                body {{
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    min-height: 100vh;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                
                .admin-container {{
                    max-width: 1400px;
                    margin: 2rem auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
                    overflow: hidden;
                }}
                
                .admin-header {{
                    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                    color: white;
                    padding: 2rem;
                }}
                
                .stats-card {{
                    background: white;
                    border-radius: 15px;
                    padding: 1.5rem;
                    border-left: 4px solid var(--primary-color);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
                    transition: transform 0.3s;
                    height: 100%;
                }}
                
                .stats-card:hover {{
                    transform: translateY(-5px);
                }}
                
                .rating-stars {{
                    color: #FFD700;
                    font-size: 1.2rem;
                }}
                
                .rating-card {{
                    background: white;
                    border-radius: 15px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                    border: 2px solid #e9ecef;
                    transition: all 0.3s;
                }}
                
                .rating-card:hover {{
                    border-color: var(--primary-color);
                    box-shadow: 0 5px 20px rgba(67, 97, 238, 0.1);
                }}
            </style>
        </head>
        <body>
            <div class="admin-container">
                <div class="admin-header">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <h1 class="display-6 fw-bold mb-2">
                                <i class="fas fa-star me-2"></i>Évaluations des utilisateurs
                            </h1>
                            <p class="opacity-90 mb-0">
                                <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro • {stats['total']} évaluations
                            </p>
                        </div>
                        <div class="text-end">
                            <a href="/admin/messages?password={admin_password}" class="btn btn-outline-light btn-sm me-2">
                                <i class="fas fa-envelope me-1"></i> Messages
                            </a>
                            <a href="/" class="btn btn-light btn-sm">
                                <i class="fas fa-home me-1"></i> Accueil
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="p-4">
        """
        
        # Statistiques
        html += f"""
                    <div class="row mb-4">
                        <div class="col-md-3 mb-3">
                            <div class="stats-card">
                                <div class="d-flex align-items-center">
                                    <div class="me-3">
                                        <i class="fas fa-star fa-2x text-warning"></i>
                                    </div>
                                    <div>
                                        <h3 class="fw-bold mb-0">{stats['average']}</h3>
                                        <p class="text-muted mb-0">Note moyenne</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <div class="stats-card">
                                <div class="d-flex align-items-center">
                                    <div class="me-3">
                                        <i class="fas fa-users fa-2x text-primary"></i>
                                    </div>
                                    <div>
                                        <h3 class="fw-bold mb-0">{stats['total']}</h3>
                                        <p class="text-muted mb-0">Évaluations totales</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <div class="stats-card">
                                <div class="d-flex align-items-center">
                                    <div class="me-3">
                                        <i class="fas fa-chart-line fa-2x text-success"></i>
                                    </div>
                                    <div>
                                        <h3 class="fw-bold mb-0">{stats['recent_count']}</h3>
                                        <p class="text-muted mb-0">Cette semaine</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-3 mb-3">
                            <div class="stats-card">
                                <div class="d-flex align-items-center">
                                    <div class="me-3">
                                        <i class="fas fa-percentage fa-2x text-info"></i>
                                    </div>
                                    <div>
                                        <h3 class="fw-bold mb-0">{stats['recent_percentage']}%</h3>
                                        <p class="text-muted mb-0">Derniers 7 jours</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title mb-3">
                                <i class="fas fa-chart-bar me-2"></i>Distribution des notes
                            </h5>
                            <div class="row">
        """
        
        # Distribution des notes
        for stars in range(5, 0, -1):
            count = stats['distribution'][stars]
            percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
            html += f"""
                                <div class="col-md-2 mb-2">
                                    <div class="d-flex justify-content-between align-items-center mb-1">
                                        <div class="rating-stars">
                                            {"★" * stars}{"☆" * (5-stars)}
                                        </div>
                                        <span class="badge bg-primary">{count}</span>
                                    </div>
                                    <div class="progress" style="height: 8px;">
                                        <div class="progress-bar bg-warning" style="width: {percentage}%"></div>
                                    </div>
                                    <small class="text-muted">{percentage:.1f}%</small>
                                </div>
            """
        
        html += """
                            </div>
                        </div>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h4>
                            <i class="fas fa-list me-2"></i>
                            Dernières évaluations ({len(ratings)})
                        </h4>
                        <div>
                            <a href="/admin/ratings?password=""" + admin_password + """&export=json" class="btn btn-success btn-sm">
                                <i class="fas fa-download me-1"></i> Exporter JSON
                            </a>
                        </div>
                    </div>
        """
        
        # Liste des évaluations
        if not ratings:
            html += """
                    <div class="text-center py-5">
                        <div class="mb-4">
                            <i class="fas fa-star fa-4x text-muted"></i>
                        </div>
                        <h3 class="text-muted mb-3">Aucune évaluation pour le moment</h3>
                        <p class="text-muted">Les évaluations soumises par les utilisateurs apparaîtront ici.</p>
                    </div>
            """
        else:
            # Trier par date (les plus récentes d'abord)
            sorted_ratings = sorted(ratings, 
                                  key=lambda x: x.get('timestamp', ''),
                                  reverse=True)
            
            for rating in sorted_ratings[:50]:  # Limiter à 50 pour la performance
                stars = rating.get('rating', 0)
                feedback = rating.get('feedback', '')
                timestamp = rating.get('timestamp', '')
                page = rating.get('page', '/')
                browser = rating.get('browser', 'Inconnu')
                
                # Formater la date
                try:
                    date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    display_date = date_obj.strftime('%d/%m/%Y %H:%M')
                    time_ago_str = time_ago(date_obj)
                except:
                    display_date = timestamp
                    time_ago_str = ''
                
                html += f"""
                    <div class="rating-card">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div>
                                <div class="rating-stars mb-2">
                                    {"★" * stars}{"☆" * (5-stars)}
                                    <span class="badge bg-warning ms-2">{stars}/5</span>
                                </div>
                                <div class="small text-muted">
                                    <i class="fas fa-calendar me-1"></i> {display_date}
                                    <span class="mx-2">•</span>
                                    <i class="fas fa-globe me-1"></i> {browser}
                                </div>
                            </div>
                            <div class="text-end">
                                <small class="text-muted">{time_ago_str}</small>
                            </div>
                        </div>
                        
                        {f'<p class="mb-2"><strong>Page :</strong> {page}</p>' if page and page != '/' else ''}
                        
                        {f'<div class="alert alert-light mt-2"><i class="fas fa-comment me-2"></i>{feedback}</div>' if feedback else '<p class="text-muted fst-italic">Aucun commentaire</p>'}
                        
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <div class="small text-muted">
                                <i class="fas fa-id-card me-1"></i> {rating.get('id', 'N/A')[:12]}...
                                <span class="mx-2">•</span>
                                <i class="fas fa-desktop me-1"></i> {rating.get('platform', 'Inconnu')}
                            </div>
                            <div>
                                <a href="/admin/ratings?password=""" + admin_password + f"""&delete={rating.get('id')}" 
                                   class="btn btn-outline-danger btn-sm"
                                   onclick="return confirm('Supprimer cette évaluation ?')">
                                    <i class="fas fa-trash"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                """
        
        # Footer
        html += f"""
                </div>
                
                <div class="p-4 border-top">
                    <div class="text-center">
                        <a href="/admin/messages?password={admin_password}" class="btn btn-outline-primary me-2">
                            <i class="fas fa-arrow-left me-1"></i> Retour aux messages
                        </a>
                        <a href="/" class="btn btn-primary">
                            <i class="fas fa-home me-1"></i> Retour à l'accueil
                        </a>
                    </div>
                </div>
            </div>
            
            <script>
                // Fonction pour formater la date relative
                function timeAgo(dateStr) {{
                    const date = new Date(dateStr);
                    const now = new Date();
                    const seconds = Math.floor((now - date) / 1000);
                    
                    if (seconds < 60) return 'il y a quelques secondes';
                    if (seconds < 3600) return 'il y a ' + Math.floor(seconds/60) + ' minutes';
                    if (seconds < 86400) return 'il y a ' + Math.floor(seconds/3600) + ' heures';
                    if (seconds < 2592000) return 'il y a ' + Math.floor(seconds/86400) + ' jours';
                    return 'il y a ' + Math.floor(seconds/2592000) + ' mois';
                }}
                
                // Mettre à jour les dates relatives
                document.addEventListener('DOMContentLoaded', function() {{
                    const dates = document.querySelectorAll('.time-ago');
                    dates.forEach(el => {{
                        el.textContent = timeAgo(el.dataset.timestamp);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        # Gérer l'export JSON
        if request.args.get('export') == 'json':
            return jsonify(ratings)
        
        # Gérer la suppression
        if request.args.get('delete'):
            deleted = ratings_manager.delete_rating(request.args.get('delete'))
            if deleted:
                return redirect(f'/admin/ratings?password={admin_password}&deleted=true')
        
        return html

    @admin_bp.route('/')
    def admin():
        """Route admin principale"""
        # Vérifier le mot de passe
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if request.args.get('password') != admin_password:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Admin - Connexion</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .login-box {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        width: 300px;
                    }
                    input {
                        width: 100%;
                        padding: 10px;
                        margin: 10px 0;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                    }
                    button {
                        width: 100%;
                        padding: 10px;
                        background: #4361ee;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    button:hover {
                        background: #3a56d4;
                    }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <h2 style="text-align:center;color:#333;">Connexion Admin</h2>
                    <form method="GET">
                        <input type="password" name="password" placeholder="Mot de passe admin" required>
                        <button type="submit">Se connecter</button>
                    </form>
                    <p style="font-size:12px;color:#888;text-align:center;margin-top:20px;">
                        Accès réservé aux administrateurs
                    </p>
                </div>
            </body>
            </html>
            ''', 401
        
        # Si le mot de passe est correct, afficher le panel admin
        # Récupérer les statistiques
        stats = {
            'pdf_merge': stats_manager.get_stat('merge', 0),
            'pdf_split': stats_manager.get_stat('pdf_split', 0),
            'pdf_rotate': stats_manager.get_stat('pdf_rotate', 0),
            'pdf_compress': stats_manager.get_stat('pdf_compress', 0),
            'ratings': stats_manager.get_stat('ratings', 0),
            'total_sessions': stats_manager.get_stat('total_sessions', 0)
        }
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel - PDF Fusion Pro</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #4361ee 0%, #3a56d4 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }}
                .stat-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                .stat-card small {{
                    opacity: 0.9;
                }}
                .menu {{
                    display: flex;
                    gap: 10px;
                    margin-top: 30px;
                    flex-wrap: wrap;
                }}
                .btn {{
                    padding: 10px 20px;
                    background: #4361ee;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .btn:hover {{
                    background: #3a56d4;
                }}
                .btn-danger {{
                    background: #e74c3c;
                }}
                .btn-danger:hover {{
                    background: #c0392b;
                }}
                .btn-success {{
                    background: #2ecc71;
                }}
                .btn-success:hover {{
                    background: #27ae60;
                }}
                .info-box {{
                    margin-top: 40px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #4361ee;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Panel d'Administration - PDF Fusion Pro</h1>
                <p>Bienvenue dans l'interface d'administration.</p>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Fusions PDF</h3>
                        <div class="stat-value">{stats['pdf_merge']}</div>
                        <small>Total des fusions</small>
                    </div>
                    <div class="stat-card">
                        <h3>Divisions PDF</h3>
                        <div class="stat-value">{stats['pdf_split']}</div>
                        <small>Total des divisions</small>
                    </div>
                    <div class="stat-card">
                        <h3>Rotations PDF</h3>
                        <div class="stat-value">{stats['pdf_rotate']}</div>
                        <small>Total des rotations</small>
                    </div>
                    <div class="stat-card">
                        <h3>Compressions PDF</h3>
                        <div class="stat-value">{stats['pdf_compress']}</div>
                        <small>Total des compressions</small>
                    </div>
                    <div class="stat-card">
                        <h3>Évaluations</h3>
                        <div class="stat-value">{stats['ratings']}</div>
                        <small>Total des évaluations</small>
                    </div>
                    <div class="stat-card">
                        <h3>Sessions</h3>
                        <div class="stat-value">{stats['total_sessions']}</div>
                        <small>Total des sessions</small>
                    </div>
                </div>
                
                <div class="menu">
                    <a href="/admin/messages?password={admin_password}" class="btn">
                        <span style="font-size: 1.2em;">📨</span> Messages
                    </a>
                    <a href="/admin/ratings?password={admin_password}" class="btn btn-success">
                        <span style="font-size: 1.2em;">⭐</span> Évaluations
                    </a>
                    <a href="/admin/debug" class="btn">
                        <span style="font-size: 1.2em;">🐛</span> Debug
                    </a>
                    <a href="/" class="btn">
                        <span style="font-size: 1.2em;">🏠</span> Accueil
                    </a>
                    <a href="/admin?logout=1" class="btn btn-danger">
                        <span style="font-size: 1.2em;">🚪</span> Déconnexion
                    </a>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                    <h3>Actions rapides</h3>
                    <div class="menu" style="margin-top: 15px;">
                        <a href="/admin/ratings?password={admin_password}&export=json" class="btn">
                            <span style="font-size: 1.2em;">📥</span> Exporter évaluations
                        </a>
                        <a href="/health" class="btn">
                            <span style="font-size: 1.2em;">❤️</span> Vérifier santé
                        </a>
                        <a href="/sitemap.xml" class="btn">
                            <span style="font-size: 1.2em;">🗺️</span> Sitemap
                        </a>
                        <a href="/robots.txt" class="btn">
                            <span style="font-size: 1.2em;">🤖</span> Robots.txt
                        </a>
                    </div>
                </div>
                
                <div class="info-box">
                    <h4>Information système</h4>
                    <p><strong>URL :</strong> https://pdf-fusion-pro-ultimate.onrender.com</p>
                    <p><strong>Date :</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
                    <p><strong>Version :</strong> {AppConfig.VERSION}</p>
                    <p><strong>Environnement :</strong> {os.environ.get('RENDER', 'Développement')}</p>
                </div>
            </div>
            
            <script>
                // Ajouter un effet de confirmation pour la déconnexion
                document.addEventListener('DOMContentLoaded', function() {{
                    const logoutBtn = document.querySelector('a[href*="logout"]');
                    if (logoutBtn) {{
                        logoutBtn.addEventListener('click', function(e) {{
                            if (!confirm('Voulez-vous vraiment vous déconnecter ?')) {{
                                e.preventDefault();
                            }}
                        }});
                    }}
                }});
            </script>
        </body>
        </html>
        '''
