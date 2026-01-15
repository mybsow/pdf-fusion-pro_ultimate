# blueprints/admin.py
import os
from functools import wraps
from datetime import datetime
from flask import (
    Blueprint, session, request,
    redirect, url_for, render_template, jsonify
)

from rating_manager import ratings_manager
from utils.stats_manager import stats_manager

# ==========================================================
# Blueprint
# ==========================================================
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ==========================================================
# Configuration
# ==========================================================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ==========================================================
# Sécurité
# ==========================================================
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged"):
            return redirect(url_for("admin.admin_login"))
        return view(*args, **kwargs)
    return wrapped

# ==========================================================
# Helpers
# ==========================================================
def time_ago(date_obj):
    now = datetime.now()
    diff = now - date_obj

    if diff.days > 365:
        y = diff.days // 365
        return f"il y a {y} an{'s' if y > 1 else ''}"
    if diff.days > 30:
        return f"il y a {diff.days // 30} mois"
    if diff.days > 0:
        return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
    if diff.seconds > 3600:
        return f"il y a {diff.seconds // 3600} heure{'s' if diff.seconds > 1 else ''}"
    if diff.seconds > 60:
        return f"il y a {diff.seconds // 60} minute{'s' if diff.seconds > 1 else ''}"
    return "à l'instant"

# ==========================================================
# Login
# ==========================================================
@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged"] = True
            return redirect(url_for("admin.admin_dashboard"))
        return render_template("admin/login.html", error="Mot de passe incorrect")

    return render_template("admin/login.html")

# ==========================================================
# Logout
# ==========================================================
@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin.admin_login"))

# ==========================================================
# Dashboard
# ==========================================================
@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    stats = {
        "pdf_merge": stats_manager.get_stat("merge", 0),
        "pdf_split": stats_manager.get_stat("pdf_split", 0),
        "pdf_rotate": stats_manager.get_stat("pdf_rotate", 0),
        "pdf_compress": stats_manager.get_stat("pdf_compress", 0),
        "ratings": stats_manager.get_stat("ratings", 0),
        "total_sessions": stats_manager.get_stat("total_sessions", 0),
    }
    return render_template("admin/dashboard.html", stats=stats)

# ==========================================================
# Ratings
# ==========================================================
@admin_bp.route("/ratings")
@admin_required
def admin_ratings():
    rating_id = request.args.get("delete")
    if rating_id:
        ratings_manager.delete_rating(rating_id)
        return redirect(url_for("admin.admin_ratings"))

    if request.args.get("export") == "json":
        return jsonify(ratings_manager.get_all_ratings())

    ratings = ratings_manager.get_all_ratings()
    stats = ratings_manager.get_stats()
    ratings_manager.mark_all_seen()

    for r in ratings:
        ts = r.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            r["display_date"] = dt.strftime("%d/%m/%Y %H:%M")
            r["time_ago"] = time_ago(dt)
        except Exception:
            r["display_date"] = ts
            r["time_ago"] = ""

    ratings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return render_template("admin/ratings.html", ratings=ratings, stats=stats)

# ==========================================================
# Debug
# ==========================================================
@admin_bp.route("/debug")
@admin_required
def admin_debug():
    return jsonify({
        "service": "PDF Fusion Pro Ultimate",
        "timestamp": datetime.now().isoformat(),
        "env": {
            "ADMIN_PASSWORD_set": bool(os.environ.get("ADMIN_PASSWORD")),
            "RENDER": bool(os.environ.get("RENDER")),
        },
        "routes": [
            "/admin/dashboard",
            "/admin/ratings",
            "/admin/debug",
            "/contact",
            "/mentions-legales",
        ]
    })

# ============================================================
# ADMIN - INTERFACE WEB POUR VOIR LES MESSAGES
# ============================================================

@admin_bp.route('/messages', methods=['GET'])
def admin_messages():
    """Interface web pour voir les messages de contact"""
    
    from flask import session
    
    # Gestion compatible local/Render
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    
    # Si pas de mot de passe dans les variables d'environnement
    # et qu'on est en local avec un fichier .env
    if not admin_password and os.path.exists('.env'):
        try:
            # Chargement manuel simple pour le développement local
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and 'ADMIN_PASSWORD=' in line:
                        admin_password = line.split('=', 1)[1].strip()
                        break
        except Exception as e:
            print(f"⚠️ Erreur lecture .env: {e}")
            pass
    
    # Vérification spéciale pour Render
    if not admin_password and os.environ.get('RENDER'):
        # Sur Render sans mot de passe configuré
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Configuration requise - PDF Fusion Pro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                body {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 1rem;
                }
                .config-box {
                    background: white;
                    border-radius: 20px;
                    padding: 2.5rem;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 600px;
                }
                .config-icon {
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #e74c3c, #c0392b);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 2rem;
                    margin: 0 auto 1.5rem;
                }
                .steps {
                    counter-reset: step-counter;
                    margin: 2rem 0;
                }
                .step {
                    display: flex;
                    align-items: flex-start;
                    margin-bottom: 1.5rem;
                    padding-left: 3rem;
                    position: relative;
                }
                .step::before {
                    counter-increment: step-counter;
                    content: counter(step-counter);
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: 2rem;
                    height: 2rem;
                    background: #4361ee;
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                }
                .step-content {
                    flex: 1;
                }
                .step-title {
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                    color: #2c3e50;
                }
                .code-block {
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 1rem;
                    font-family: 'Courier New', monospace;
                    margin: 0.5rem 0;
                    border-left: 4px solid #4361ee;
                }
            </style>
        </head>
        <body>
            <div class="config-box">
                <div class="config-icon">
                    <i class="fas fa-cog"></i>
                </div>
                
                <h2 class="text-center mb-3">Configuration requise</h2>
                <p class="text-center text-muted mb-4">
                    <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro - Panneau d'administration
                </p>
                
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    <strong>Variable d'environnement manquante :</strong> 
                    <code>ADMIN_PASSWORD</code> n'est pas configuré sur Render.
                </div>
                
                <h5 class="mt-4 mb-3"><i class="fas fa-list-ol me-2"></i> Étapes de configuration :</h5>
                
                <div class="steps">
                    <div class="step">
                        <div class="step-content">
                            <div class="step-title">1. Connectez-vous à Render</div>
                            <p>Allez sur <a href="https://dashboard.render.com" target="_blank">dashboard.render.com</a></p>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-content">
                            <div class="step-title">2. Sélectionnez votre service</div>
                            <p>Cherchez "pdf-fusion-pro-ultimate" dans vos services</p>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-content">
                            <div class="step-title">3. Accédez aux variables d'environnement</div>
                            <p>Cliquez sur "Environment" dans le menu de gauche</p>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-content">
                            <div class="step-title">4. Ajoutez la variable</div>
                            <p>Cliquez sur "Add Environment Variable" :</p>
                            <div class="code-block">
                                Key: <strong>ADMIN_PASSWORD</strong><br>
                                Value: <strong>VotreMotDePasseSecurise</strong>
                            </div>
                            <small class="text-muted">Exemple : Kindia@2805* (changer pour votre propre mot de passe)</small>
                        </div>
                    </div>
                    
                    <div class="step">
                        <div class="step-content">
                            <div class="step-title">5. Redéployez</div>
                            <p>Cliquez sur "Manual Deploy" → "Deploy latest commit"</p>
                        </div>
                    </div>
                </div>
                
                <div class="alert alert-info mt-4">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Note :</strong> Après configuration, accédez à 
                    <code>/admin/messages?password=VotreMotDePasseSecurise</code>
                </div>
                
                <div class="text-center mt-4">
                    <a href="https://dashboard.render.com" target="_blank" class="btn btn-primary me-2">
                        <i class="fas fa-external-link-alt me-1"></i> Aller sur Render
                    </a>
                    <a href="/" class="btn btn-outline-secondary">
                        <i class="fas fa-home me-1"></i> Retour à l'accueil
                    </a>
                </div>
            </div>
        </body>
        </html>
        """, 500
    
    # Si toujours pas de mot de passe, utiliser un défaut (développement local)
    if not admin_password:
        admin_password = 'admin123'  # ⚠️ CHANGEZ CE MOT DE PASSE EN PRODUCTION !
    
    # Limiter les tentatives de connexion (protection basique)
    try:
        session_key = f'admin_login_attempts_{request.remote_addr}'
        attempts = session.get(session_key, 0)
        
        # Bloquer après 5 tentatives échouées
        if attempts >= 5:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Trop de tentatives - PDF Fusion Pro</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body {
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    }
                    .alert-box {
                        background: white;
                        border-radius: 20px;
                        padding: 2.5rem;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                        max-width: 500px;
                        text-align: center;
                    }
                    .alert-icon {
                        font-size: 4rem;
                        color: #e74c3c;
                        margin-bottom: 1rem;
                    }
                </style>
            </head>
            <body>
                <div class="alert-box">
                    <div class="alert-icon">
                        <i class="fas fa-ban"></i>
                    </div>
                    <h2 class="text-danger">Accès temporairement bloqué</h2>
                    <p class="mt-3">
                        Trop de tentatives de connexion infructueuses.
                    </p>
                    <p class="text-muted">
                        Veuillez réessayer dans <strong>15 minutes</strong>.
                    </p>
                    <div class="mt-4">
                        <a href="/" class="btn btn-outline-primary">
                            <i class="fas fa-home me-1"></i> Retour à l'accueil
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """, 429
    except:
        # Si session n'est pas disponible, continuer sans limitation
        pass
    
    # Vérifier l'authentification
    if request.args.get('password') != admin_password:
        # Incrémenter le compteur de tentatives
        try:
            session[session_key] = attempts + 1
        except:
            pass
            
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Accès Admin - PDF Fusion Pro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                body {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    min-height: 100vh;
                    display: flex;
                        align-items: center;
                    justify-content: center;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                .login-box {
                    background: white;
                    border-radius: 20px;
                    padding: 2.5rem;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 400px;
                }
                .app-icon {
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #4361ee, #3a0ca3);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 2rem;
                    margin: 0 auto 1.5rem;
                }
                .alert-warning {
                    background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                    border-color: #ffc107;
                }
                .attempts-warning {
                    font-size: 0.85rem;
                    color: #e74c3c;
                    margin-top: 0.5rem;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <div class="app-icon">
                    <i class="fas fa-lock"></i>
                </div>
                
                <h2 class="text-center mb-4">Accès Administrateur</h2>
                <p class="text-center text-muted mb-4">
                    <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro
                </p>
                
                <form method="GET" action="/admin/messages">
                    <div class="mb-3">
                        <label for="password" class="form-label">Mot de passe admin</label>
                        <div class="input-group">
                            <span class="input-group-text">
                                <i class="fas fa-key"></i>
                            </span>
                            <input type="password" class="form-control" id="password" name="password" 
                                   placeholder="Entrez le mot de passe" required autofocus>
                        </div>
                        <div class="form-text">
                            <i class="fas fa-info-circle me-1"></i>
                            Accès réservé à l'administrateur
                        </div>
                        """ + (f"""
                        <div class="attempts-warning">
                            <i class="fas fa-exclamation-triangle me-1"></i>
                            Tentative {attempts + 1}/5
                        </div>
                        """ if attempts > 0 else "") + """
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-sign-in-alt me-1"></i> Se connecter
                    </button>
                </form>
                
                <div class="alert alert-warning mt-4">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Sécurité :</strong> Configurez la variable d'environnement 
                    <code>ADMIN_PASSWORD</code> sur Render pour un mot de passe sécurisé.
                </div>
                
                <!-- Indicateur d'environnement -->
                <div class="text-center mt-3 small text-muted">
                    <i class="fas fa-server me-1"></i>
                    """ + ("🟢 Connecté à Render" if os.environ.get('RENDER') else "🟡 Développement local") + """
                </div>
            </div>
        </body>
        </html>
        """, 401

    # ============================================
    # DÉBUT DE L'INTERFACE ADMIN
    # ============================================
    
    contacts_dir = Path("data/contacts")
    contacts = []
    
    if contacts_dir.exists():
        # Lire tous les fichiers JSON
        for filepath in sorted(contacts_dir.glob("*.json"), 
                              key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    contact_data = json.load(f)
                    contact_data['filename'] = filepath.name
                    contact_data['file_size'] = f"{filepath.stat().st_size:,} octets"
                    contact_data['modified'] = datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).strftime('%d/%m/%Y %H:%M')
                    contacts.append(contact_data)
            except Exception as e:
                contacts.append({
                    'filename': filepath.name,
                    'error': str(e),
                    'modified': datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).strftime('%d/%m/%Y %H:%M')
                })
    
    # Gérer les actions (suppression, marquer comme traité)
    action = request.args.get('action')
    filename = request.args.get('file')
    
    if action and filename:
        filepath = contacts_dir / filename
        if filepath.exists():
            if action == 'delete':
                try:
                    filepath.unlink()
                    return redirect(f'/admin/messages?password={admin_password}&deleted={filename}')
                except:
                    pass
            elif action == 'toggle_processed':
                try:
                    with open(filepath, 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        data['processed'] = not data.get('processed', False)
                        data['processed_at'] = datetime.now().isoformat() if data['processed'] else None
                        f.seek(0)
                        json.dump(data, f, indent=2, ensure_ascii=False)
                        f.truncate()
                    return redirect(f'/admin/messages?password={admin_password}')
                except:
                    pass
    
    # Calculer les statistiques
    stats = {
        'total': len(contacts),
        'processed': sum(1 for c in contacts if c.get('processed')),
        'bug': sum(1 for c in contacts if c.get('subject') == 'bug'),
        'improvement': sum(1 for c in contacts if c.get('subject') == 'improvement'),
        'partnership': sum(1 for c in contacts if c.get('subject') == 'partnership'),
        'other': sum(1 for c in contacts if c.get('subject') == 'other'),
        'today': sum(1 for c in contacts if c.get('received_at', '').startswith(
            datetime.now().strftime('%Y-%m-%d')
        ))
    }
    
    # Sujets traduits
    subject_translation = {
        'bug': '🚨 Bug/Problème',
        'improvement': '💡 Suggestion',
        'partnership': '🤝 Partenariat',
        'other': '❓ Autre'
    }
    
    # Générer l'HTML de l'interface admin
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Messages de Contact - Admin</title>
        
        <!-- Bootstrap 5.3 -->
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
            
            .admin-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.2);
                padding: 0.5rem 1.5rem;
                border-radius: 50px;
                font-weight: 600;
                margin-bottom: 1rem;
            }}
            
            .admin-content {{
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
            
            .stats-icon {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                margin-bottom: 1rem;
            }}
            
            .message-card {{
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border: 2px solid #e9ecef;
                transition: all 0.3s;
            }}
            
            .message-card:hover {{
                border-color: var(--primary-color);
                box-shadow: 0 5px 20px rgba(67, 97, 238, 0.1);
            }}
            
            .message-card.processed {{
                border-color: var(--success-color);
                background: linear-gradient(135deg, #f8fff9, #e8f7ec);
            }}
            
            .message-header {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            }}
            
            .message-content {{
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 10px;
                max-height: 200px;
                overflow-y: auto;
                font-family: monospace;
                white-space: pre-wrap;
            }}
            
            .badge-subject {{
                font-size: 0.8em;
                padding: 0.4em 0.8em;
            }}
            
            .btn-action {{
                padding: 0.3rem 0.8rem;
                font-size: 0.85rem;
                margin: 0 0.2rem;
            }}
            
            @media (max-width: 768px) {{
                .admin-container {{
                    margin: 1rem;
                    border-radius: 15px;
                }}
                
                .admin-header, .admin-content {{
                    padding: 1.5rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="admin-container">
            <div class="admin-header">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <div class="admin-badge">
                            <i class="fas fa-user-shield me-2"></i> Administration
                        </div>
                        <h1 class="display-6 fw-bold mb-2">Messages de Contact</h1>
                        <p class="opacity-90 mb-0">
                            <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro
                            <span class="mx-2">•</span>
                            <i class="fas fa-folder me-1"></i> data/contacts/
                        </p>
                    </div>
                    <div class="text-end">
                        <a href="/" class="btn btn-outline-light btn-sm me-2">
                            <i class="fas fa-home me-1"></i> Accueil
                        </a>
                        <a href="/contact" class="btn btn-light btn-sm">
                            <i class="fas fa-envelope me-1"></i> Formulaire
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="admin-content">
    """
    
    # Messages d'alerte
    if request.args.get('deleted'):
        html += f"""
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Message supprimé :</strong> {request.args.get('deleted')}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
        """
    
    if not contacts:
        html += """
                <div class="text-center py-5">
                    <div class="mb-4">
                        <i class="fas fa-inbox fa-4x text-muted"></i>
                    </div>
                    <h3 class="text-muted mb-3">Aucun message pour le moment</h3>
                    <p class="text-muted">Les messages soumis via le formulaire de contact apparaîtront ici.</p>
                    <a href="/contact" class="btn btn-primary">
                        <i class="fas fa-eye me-1"></i> Voir le formulaire
                    </a>
                </div>
        """
    else:
        # Statistiques
        html += f"""
                <div class="row mb-4">
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white;">
                                <i class="fas fa-envelope"></i>
                            </div>
                            <h3 class="fw-bold">{stats['total']}</h3>
                            <p class="text-muted mb-0">Messages totaux</p>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #2ecc71, #27ae60); color: white;">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <h3 class="fw-bold">{stats['processed']}</h3>
                            <p class="text-muted mb-0">Messages traités</p>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #f39c12, #e67e22); color: white;">
                                <i class="fas fa-bug"></i>
                            </div>
                            <h3 class="fw-bold">{stats['bug']}</h3>
                            <p class="text-muted mb-0">Rapports de bugs</p>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white;">
                                <i class="fas fa-lightbulb"></i>
                            </div>
                            <h3 class="fw-bold">{stats['improvement']}</h3>
                            <p class="text-muted mb-0">Suggestions</p>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3>
                        <i class="fas fa-list me-2"></i>
                        Messages reçus ({stats['total']})
                    </h3>
                    <div>
                        <a href="/admin/messages?password={admin_password}&export=json" class="btn btn-success btn-sm">
                            <i class="fas fa-download me-1"></i> Exporter JSON
                        </a>
                        <button class="btn btn-warning btn-sm ms-2" onclick="toggleAllMessages()">
                            <i class="fas fa-eye me-1"></i> Tout afficher/masquer
                        </button>
                    </div>
                </div>
        """
        
        # Liste des messages
        for i, contact in enumerate(contacts, 1):
            # Gestion des erreurs de lecture
            if 'error' in contact:
                html += f"""
                <div class="message-card">
                    <div class="message-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge bg-danger badge-subject">
                                    <i class="fas fa-exclamation-triangle me-1"></i> ERREUR
                                </span>
                            </div>
                            <small class="text-muted">{contact.get('modified', 'Date inconnue')}</small>
                        </div>
                    </div>
                    <p class="text-danger">
                        <i class="fas fa-times-circle me-1"></i>
                        Erreur de lecture : {contact.get('error', 'Inconnue')}
                    </p>
                    <p class="mb-2"><strong>Fichier :</strong> {contact.get('filename')}</p>
                    <div class="text-end">
                        <a href="/admin/messages?password={admin_password}&action=delete&file={contact.get('filename')}" 
                           class="btn btn-danger btn-sm btn-action"
                           onclick="return confirm('Supprimer ce fichier corrompu ?')">
                            <i class="fas fa-trash"></i> Supprimer
                        </a>
                    </div>
                </div>
                """
                continue
            
            # Message normal
            subject_display = subject_translation.get(
                contact.get('subject', 'other'),
                contact.get('subject', 'Autre')
            )
            
            # Couleur du badge selon le sujet
            badge_color = {
                'bug': 'danger',
                'improvement': 'warning',
                'partnership': 'info',
                'other': 'secondary'
            }.get(contact.get('subject', 'other'), 'secondary')
            
            processed = contact.get('processed', False)
            processed_class = 'processed' if processed else ''
            
            # Date formatée
            received_at = contact.get('received_at', '')
            if 'T' in received_at:
                date_part, time_part = received_at.split('T')
                time_part = time_part.split('.')[0]
                display_date = f"{date_part} {time_part}"
            else:
                display_date = received_at
            
            html += f"""
            <div class="message-card {processed_class}" id="message-{i}">
                <div class="message-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-{badge_color} badge-subject">
                                {subject_display}
                            </span>
                            <span class="badge {'bg-success' if processed else 'bg-secondary'} badge-subject ms-2">
                                <i class="fas fa-{'check' if processed else 'clock'} me-1"></i>
                                {'Traité' if processed else 'En attente'}
                            </span>
                        </div>
                        <div>
                            <small class="text-muted me-3">
                                <i class="fas fa-calendar me-1"></i> {display_date}
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-hashtag me-1"></i> #{i}
                            </small>
                        </div>
                    </div>
                    
                    <div class="row mt-2">
                        <div class="col-md-4">
                            <p class="mb-1"><strong><i class="fas fa-user me-1"></i> Nom :</strong></p>
                            <p class="mb-0">{contact.get('first_name', 'N/A')} {contact.get('last_name', 'N/A')}</p>
                        </div>
                        <div class="col-md-4">
                            <p class="mb-1"><strong><i class="fas fa-envelope me-1"></i> Email :</strong></p>
                            <p class="mb-0">
                                <a href="mailto:{contact.get('email', '')}" class="text-decoration-none">
                                    {contact.get('email', 'N/A')}
                                </a>
                            </p>
                        </div>
                        <div class="col-md-4">
                            <p class="mb-1"><strong><i class="fas fa-phone me-1"></i> Téléphone :</strong></p>
                            <p class="mb-0">{contact.get('phone', 'Non renseigné')}</p>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <p class="mb-1"><strong><i class="fas fa-comment me-1"></i> Message :</strong></p>
                    <div class="message-content" id="content-{i}">
                        {contact.get('message', 'Aucun message')}
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center">
                    <div class="text-muted small">
                        <i class="fas fa-file me-1"></i> {contact.get('filename')}
                        <span class="mx-2">•</span>
                        <i class="fas fa-hdd me-1"></i> {contact.get('file_size', 'N/A')}
                        <span class="mx-2">•</span>
                        <i class="fas fa-globe me-1"></i> {contact.get('ip_address', 'N/A')}
                    </div>
                    
                    <div>
                        <button class="btn btn-outline-primary btn-sm btn-action" 
                                onclick="copyToClipboard('{contact.get('email', '')}')"
                                title="Copier l'email">
                            <i class="fas fa-copy"></i>
                        </button>
                        
                        <a href="mailto:{contact.get('email', '')}" 
                           class="btn btn-outline-success btn-sm btn-action"
                           title="Répondre">
                            <i class="fas fa-reply"></i>
                        </a>
                        
                        <a href="/admin/messages?password={admin_password}&action=toggle_processed&file={contact.get('filename')}" 
                           class="btn {'btn-success' if not processed else 'btn-secondary'} btn-sm btn-action"
                           title="{'Marquer comme traité' if not processed else 'Marquer non traité'}">
                            <i class="fas fa-{'check' if not processed else 'undo'}"></i>
                        </a>
                        
                        <a href="/admin/messages?password={admin_password}&action=delete&file={contact.get('filename')}" 
                           class="btn btn-outline-danger btn-sm btn-action"
                           onclick="return confirm('Supprimer définitivement ce message ?')"
                           title="Supprimer">
                            <i class="fas fa-trash"></i>
                        </a>
                    </div>
                </div>
            </div>
            """
    
    # Footer et scripts
    html += f"""
            </div>
            
            <div class="admin-content border-top">
                <div class="row">
                    <div class="col-md-6">
                        <div class="alert alert-info">
                            <h5><i class="fas fa-info-circle me-2"></i> Informations</h5>
                            <ul class="mb-0">
                                <li>Messages sauvegardés dans <code>data/contacts/</code></li>
                                <li>Chaque message est un fichier JSON indépendant</li>
                                <li>Statistiques mises à jour en temps réel</li>
                                <li>Session admin protégée par mot de passe</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="alert alert-warning">
                            <h5><i class="fas fa-exclamation-triangle me-2"></i> Sécurité</h5>
                            <p class="mb-2">Pour plus de sécurité :</p>
                            <ol class="mb-0">
                                <li>Configurez <code>ADMIN_PASSWORD</code> sur Render</li>
                                <li>Changez régulièrement le mot de passe</li>
                                <li>Limitez l'accès à cette page</li>
                            </ol>
                        </div>
                    </div>
                </div>
                
                <div class="text-center mt-4">
                    <div class="btn-group" role="group">
                        <a href="/admin/messages?password={admin_password}&export=json" class="btn btn-success">
                            <i class="fas fa-download me-1"></i> Exporter JSON
                        </a>
                        <a href="/admin/messages?password={admin_password}&cleanup=true" class="btn btn-warning"
                           onclick="return confirm('Supprimer les messages de plus de 30 jours ?')">
                            <i class="fas fa-broom me-1"></i> Nettoyer
                        </a>
                    </div>
                    
                    <div class="btn-group ms-2" role="group">
                        <a href="/admin/messages?password={admin_password}" class="btn btn-primary">
                            <i class="fas fa-envelope me-1"></i> Messages
                        </a>
                        <a href="/admin/ratings?password={admin_password}" class="btn btn-warning">
                            <i class="fas fa-star me-1"></i> Évaluations
                        </a>
                    </div>
                    
                    <a href="/" class="btn btn-outline-secondary ms-2">
                        <i class="fas fa-home me-1"></i> Accueil
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JS -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        
        <script>
            // Copier l'email dans le presse-papier
            function copyToClipboard(email) {{
                navigator.clipboard.writeText(email).then(function() {{
                    alert('Email copié : ' + email);
                }}, function(err) {{
                    alert('Erreur de copie : ' + err);
                }});
            }}
            
            // Afficher/masquer tous les messages
            function toggleAllMessages() {{
                const messageContents = document.querySelectorAll('[id^="content-"]');
                const allHidden = Array.from(messageContents).every(content => 
                    content.style.display === 'none' || content.style.maxHeight === '0px'
                );
                
                messageContents.forEach(content => {{
                    if (allHidden) {{
                        content.style.display = 'block';
                        content.style.maxHeight = 'none';
                    }} else {{
                        content.style.display = 'none';
                        content.style.maxHeight = '0px';
                    }}
                }});
                
                const btn = document.querySelector('button[onclick="toggleAllMessages()"]');
                btn.innerHTML = allHidden ? 
                    '<i class="fas fa-eye-slash me-1"></i> Tout masquer' : 
                    '<i class="fas fa-eye me-1"></i> Tout afficher';
            }}
            
            // Initialiser : masquer les longs messages
            document.addEventListener('DOMContentLoaded', function() {{
                const messageContents = document.querySelectorAll('[id^="content-"]');
                messageContents.forEach(content => {{
                    if (content.scrollHeight > 200) {{
                        content.style.maxHeight = '200px';
                        content.style.overflowY = 'auto';
                    }}
                }});
                
                // Message de confirmation pour suppression
                const deleteLinks = document.querySelectorAll('a[href*="action=delete"]');
                deleteLinks.forEach(link => {{
                    link.addEventListener('click', function(e) {{
                        if (!confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {{
                            e.preventDefault();
                        }}
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    # Gérer l'export JSON
    if request.args.get('export') == 'json':
        clean_contacts = []
        for contact in contacts:
            if 'error' not in contact:
                clean_contacts.append({
                    k: v for k, v in contact.items() 
                    if k not in ['filename', 'file_size', 'modified']
                })
        return jsonify(clean_contacts)
    
    # Gérer le nettoyage
    if request.args.get('cleanup') == 'true':
        cutoff_time = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        deleted = 0
        for filepath in contacts_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted += 1
                except:
                    pass
        return redirect(f'/admin/messages?password={admin_password}&cleaned={deleted}')
    
    return html
