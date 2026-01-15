# blueprints/admin.py
import os
from functools import wraps
from datetime import datetime
from pathlib import Path
from flask import (
    Blueprint, session, request,
    redirect, url_for, render_template, jsonify
)

from rating_manager import ratings_manager
from utils.stats_manager import stats_manager

# Dossier contacts
CONTACTS_DIR = Path("data/contacts")
CONTACTS_DIR.mkdir(parents=True, exist_ok=True)

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
        'pdf_merge': stats_manager.get_stat('merge', 0),
        'pdf_split': stats_manager.get_stat('pdf_split', 0),
        'pdf_rotate': stats_manager.get_stat('pdf_rotate', 0),
        'pdf_compress': stats_manager.get_stat('pdf_compress', 0),
        'ratings': ratings_manager.get_stats()['total'],  # total évaluations
        'unseen_ratings': ratings_manager.get_stats().get('unseen', 0),  # nouvelles évaluations
        'total_sessions': stats_manager.get_stat('total_sessions', 0)
    }
    return render_template("admin/dashboard.html", stats=stats)


# =====================================
# Messages de contact (NOUVEAU)
# =====================================
@admin_bp.route("/messages")
@admin_required
def admin_messages():
    messages = []

    if CONTACTS_DIR.exists():
        for file in CONTACTS_DIR.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_file"] = file.name
                    data["_date"] = data.get("timestamp", "")
                    messages.append(data)
            except Exception:
                continue

    # Trier par date décroissante
    messages.sort(key=lambda x: x.get("_date", ""), reverse=True)

    return render_template(
        "admin/messages.html",
        messages=messages,
        total=len(messages)
    )


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


