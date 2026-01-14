from flask import Blueprint, request, jsonify, redirect, render_template, session, url_for
from datetime import datetime
import os
from rating_manager import ratings_manager
from utils.stats_manager import stats_manager
from config import AppConfig

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ===============================
# Helper
# ===============================
def is_admin_authenticated():
    return session.get('admin_authenticated', False)

def check_admin_password(password):
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    return password == admin_password

def time_ago(date_obj):
    """Retourne une chaîne 'il y a X temps' """
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

# ===============================
# Routes
# ===============================

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Page de login admin"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_admin_password(password):
            session['admin_authenticated'] = True
            return redirect(url_for('admin.admin_dashboard'))
        else:
            error = "Mot de passe incorrect"
            return render_template("admin/login.html", error=error)
    return render_template("admin/login.html")


@admin_bp.route('/logout')
def admin_logout():
    """Déconnexion admin"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/')
def admin_dashboard():
    """Dashboard admin principal"""
    if not is_admin_authenticated():
        return redirect(url_for('admin.admin_login'))

    stats = {
        'pdf_merge': stats_manager.get_stat('merge', 0),
        'pdf_split': stats_manager.get_stat('pdf_split', 0),
        'pdf_rotate': stats_manager.get_stat('pdf_rotate', 0),
        'pdf_compress': stats_manager.get_stat('pdf_compress', 0),
        'ratings': stats_manager.get_stat('ratings', 0),
        'total_sessions': stats_manager.get_stat('total_sessions', 0)
    }

    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route('/debug')
def admin_debug():
    """Page debug admin"""
    if not is_admin_authenticated():
        return redirect(url_for('admin.admin_login'))

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

    # Cacher valeur sensible
    if info['environment']['ADMIN_PASSWORD_set']:
        password = os.environ.get('ADMIN_PASSWORD', '')
        if len(password) > 2:
            info['environment']['ADMIN_PASSWORD_preview'] = password[0] + '***' + password[-1]
        else:
            info['environment']['ADMIN_PASSWORD_preview'] = '***'

    return jsonify(info)


@admin_bp.route('/ratings', methods=['GET', 'POST'])
def admin_ratings():
    """Page gestion des évaluations"""
    if not is_admin_authenticated():
        return redirect(url_for('admin.admin_login'))

    # Gestion suppression
    rating_id_to_delete = request.args.get('delete')
    if rating_id_to_delete:
        deleted = ratings_manager.delete_rating(rating_id_to_delete)
        return redirect(url_for('admin.admin_ratings'))

    # Gestion export JSON
    if request.args.get('export') == 'json':
        ratings = ratings_manager.get_all_ratings()
        return jsonify(ratings)

    # Récupérer les évaluations
    ratings = ratings_manager.get_all_ratings()
    stats = ratings_manager.get_stats()

    # Trier les plus récentes
    sorted_ratings = sorted(ratings, key=lambda x: x.get('timestamp', ''), reverse=True)

    # Formater les dates
    for r in sorted_ratings:
        timestamp = r.get('timestamp')
        try:
            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            r['display_date'] = date_obj.strftime('%d/%m/%Y %H:%M')
            r['time_ago'] = time_ago(date_obj)
        except:
            r['display_date'] = timestamp
            r['time_ago'] = ''

    return render_template("admin/ratings.html", ratings=sorted_ratings, stats=stats)


# ===============================
# Fin du blueprint
# ===============================
