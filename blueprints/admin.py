# blueprints/admin.py (fusionné)
import os
from functools import wraps
from datetime import datetime
from flask import Blueprint, session, request, redirect, url_for, render_template, jsonify
from rating_manager import ratings_manager
from utils.stats_manager import stats_manager

# =====================================
# Blueprint
# =====================================
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# =====================================
# Configuration
# =====================================
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# =====================================
# Décorateur de sécurité
# =====================================
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged"):
            return redirect(url_for("admin.admin_login"))
        return view(*args, **kwargs)
    return wrapped

# =====================================
# Helper
# =====================================
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

# =====================================
# Login
# =====================================
@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged"] = True
            return redirect(url_for("admin.admin_dashboard"))
        error = "Mot de passe incorrect"
        return render_template("legal/admin/login.html", error=error)
    return render_template("legal/admin/login.html")

# =====================================
# Logout
# =====================================
@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin.admin_login"))

# =====================================
# Dashboard
# =====================================
@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    stats = {
        'pdf_merge': stats_manager.get_stat('merge', 0),
        'pdf_split': stats_manager.get_stat('pdf_split', 0),
        'pdf_rotate': stats_manager.get_stat('pdf_rotate', 0),
        'pdf_compress': stats_manager.get_stat('pdf_compress', 0),
        'ratings': stats_manager.get_stat('ratings', 0),
        'total_sessions': stats_manager.get_stat('total_sessions', 0)
    }
    return render_template("legal/admin/dashboard.html", stats=stats)

# =====================================
# Page évaluations
# =====================================
@admin_bp.route("/ratings")
@admin_required
def admin_ratings():
    # Suppression
    rating_id = request.args.get("delete")
    if rating_id:
        ratings_manager.delete_rating(rating_id)
        return redirect(url_for("admin.admin_ratings"))

    # Export JSON
    if request.args.get("export") == "json":
        ratings = ratings_manager.get_all_ratings()
        return jsonify(ratings)

    # Récupérer évaluations
    ratings = ratings_manager.get_all_ratings()
    stats = ratings_manager.get_stats()
    ratings_manager.mark_all_seen()  # Marquer comme vues

    # Trier et formater
    sorted_ratings = sorted(ratings, key=lambda x: x.get("timestamp", ""), reverse=True)
    for r in sorted_ratings:
        ts = r.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            r["display_date"] = dt.strftime("%d/%m/%Y %H:%M")
            r["time_ago"] = time_ago(dt)
        except:
            r["display_date"] = ts
            r["time_ago"] = ""

    return render_template("legal/admin/ratings.html", ratings=sorted_ratings, stats=stats)

# =====================================
# Page debug JSON
# =====================================
@admin_bp.route("/debug")
@admin_required
def admin_debug():
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
            '/admin/dashboard',
            '/admin/ratings',
            '/admin/debug',
            '/contact',
            '/mentions-legales'
        ]
    }

    # Masquer mot de passe partiellement
    if info['environment']['ADMIN_PASSWORD_set']:
        pwd = os.environ.get("ADMIN_PASSWORD", "")
        info['environment']['ADMIN_PASSWORD_preview'] = pwd[0] + "***" + pwd[-1] if len(pwd) > 2 else "***"

    return jsonify(info)
