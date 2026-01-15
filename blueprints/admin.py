import os, json
from functools import wraps
from datetime import datetime
from flask import Blueprint, session, request, redirect, url_for, render_template, jsonify

from utils.stats_manager import stats_manager
from utils.rating_manager import ratings_manager
from utils.contact_manager import contact_manager

# ==========================================================
# Blueprint
# ==========================================================
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ==========================================================
# Admin password
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
# Login / Logout
# ==========================================================
@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged"] = True
            return redirect(url_for("admin.admin_dashboard"))
        return render_template("admin/login.html", error="Mot de passe incorrect")
    return render_template("admin/login.html")

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
    ratings_stats = ratings_manager.get_stats()
    messages = contact_manager.get_all()
    stats = {
        "ratings": ratings_stats.get("total", 0),
        "unseen_ratings": ratings_stats.get("unseen", 0),
        "total_messages": len(messages),
        "unseen_messages": contact_manager.get_unseen_count(),
        "pdf_merge": stats_manager.get_stat('merge', 0),
        "pdf_split": stats_manager.get_stat('pdf_split', 0),
        "pdf_rotate": stats_manager.get_stat('pdf_rotate', 0),
        "pdf_compress": stats_manager.get_stat('pdf_compress', 0),
        "total_sessions": stats_manager.get_stat('total_sessions', 0)
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
# Messages
# ==========================================================
@admin_bp.route("/messages")
@admin_required
def admin_messages():
    messages = contact_manager.get_all()
    contact_manager.mark_all_seen()
    return render_template("admin/messages.html", messages=messages)

@admin_bp.route("/messages/archive/<message_id>")
@admin_required
def archive_message(message_id):
    contact_manager.archive(message_id)
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/delete/<message_id>")
@admin_required
def delete_message(message_id):
    contact_manager.delete(message_id)
    return redirect(url_for("admin.admin_messages"))


# =====================================
# Actions sur les messages
# =====================================
@admin_bp.route("/messages/seen/<message_id>")
@admin_required
def mark_message_seen(message_id):
    contact_manager.mark_all_seen()  # ou contact_manager.mark_seen(message_id) si tu veux le faire individuellement
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/archive/<message_id>")
@admin_required
def archive_message(message_id):
    contact_manager.archive(message_id)
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/delete/<message_id>")
@admin_required
def delete_message(message_id):
    contact_manager.delete(message_id)
    return redirect(url_for("admin.admin_messages"))

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


