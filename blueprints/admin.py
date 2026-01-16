import os
from functools import wraps
from datetime import datetime
from flask import Blueprint, session, request, redirect, url_for, render_template, jsonify

from utils.cache import SimpleCache

from managers.contact_manager import contact_manager
from managers.rating_manager import rating_manager
from managers.stats_manager import stats_manager  # Importez l'instance

#from flask_caching import Cache

#cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
#cache.init_app(app)


cache = SimpleCache(ttl=15)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# -----------------------
# Auth
# -----------------------
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged"):
            return redirect(url_for("admin.admin_login"))
        return view(*args, **kwargs)
    return wrapped

# -----------------------
# Helper time ago
# -----------------------
def time_ago(date_obj):
    now = datetime.now()
    diff = now - date_obj
    if diff.days > 365: return f"il y a {diff.days//365} an{'s' if diff.days>365 else ''}"
    if diff.days > 30: return f"il y a {diff.days//30} mois"
    if diff.days > 0: return f"il y a {diff.days} jour{'s' if diff.days>1 else ''}"
    if diff.seconds > 3600: return f"il y a {diff.seconds//3600} heure{'s' if diff.seconds>1 else ''}"
    if diff.seconds > 60: return f"il y a {diff.seconds//60} minute{'s' if diff.seconds>1 else ''}"
    return "à l'instant"

# -----------------------
# Login / Logout
# -----------------------
@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    if request.method=="POST":
        if request.form.get("password")==ADMIN_PASSWORD:
            session["admin_logged"]=True
            return redirect(url_for("admin.admin_dashboard"))
        return render_template("admin/login.html", error="Mot de passe incorrect")
    return render_template("admin/login.html")

@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin.admin_login"))

# -----------------------
# Dashboard
# -----------------------
@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    # Récupération du cache
    stats = cache.get("dashboard_stats")
    if not stats:
        # =========================
        # Messages
        # =========================
        all_messages = contact_manager.get_all_sorted()
        recent_messages = all_messages[:5]  # 5 messages récents pour le dashboard

        # =========================
        # Évaluations (ratings)
        # =========================
        rating_stats = rating_manager.get_stats()
        all_ratings = rating_manager.get_all_ratings()

        # Préparer les 5 ratings récents avec attributs pour le template
        recent_ratings = []
        for r, file in zip(all_ratings[:5], rating_manager.ratings_dir.glob("rating_*.json")):
            r_copy = r.copy()
            r_copy["id"] = file.name
            ts = r.get("timestamp")
            if ts:
                try:
                    r_copy["display_date"] = datetime.fromisoformat(ts).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    r_copy["display_date"] = ts
            else:
                r_copy["display_date"] = "-"
            r_copy["page"] = r.get("page", "-")
            recent_ratings.append(r_copy)

        # =========================
        # Stats complètes
        # =========================
        stats = {
            # Messages
            "total_messages": len(all_messages),
            "unseen_messages": contact_manager.get_unseen_count(),
            "messages": recent_messages,  # pour affichage dans dashboard

            # Ratings
            "total_ratings": rating_stats.get("total", 0),
            "avg_rating": rating_stats.get("average", 0),
            "total_comments": rating_stats.get("comments", 0),
            "ratings": recent_ratings,    # pour affichage dans dashboard
        }

        # =========================
        # Mise en cache (SimpleCache ne supporte pas 'timeout')
        # =========================
        cache.set("dashboard_stats", stats)

    return render_template("admin/dashboard.html", stats=stats)

# -----------------------
# Inject unread messages badge
# -----------------------
@admin_bp.app_context_processor
def inject_unread_count():
    return {"unread_count": contact_manager.get_unseen_count()}

# -----------------------
# Messages
# -----------------------
@admin_bp.route("/messages")
@admin_required
def admin_messages():
    messages = contact_manager.get_all_sorted()
    return render_template("admin/messages.html", messages=messages)

@admin_bp.route("/messages/seen/<message_id>")
@admin_required
def mark_message_seen(message_id):
    contact_manager.mark_all_seen()
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/archive/<message_id>", methods=["POST"])
@admin_required
def archive_message(message_id):
    contact_manager.archive_message(int(message_id))
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/archived")
@admin_required
def admin_messages_archived():
    messages = contact_manager.get_all_sorted(archive=True)  # ou une méthode get_archived()
    return render_template("admin/messages_archived.html", messages=messages)

@admin_bp.route("/messages/delete/<message_id>", methods=["POST"])
@admin_required
def delete_message(message_id):
    contact_manager.delete(int(message_id))
    return redirect(url_for("admin.admin_messages"))

# -----------------------
# Ratings
# -----------------------
@admin_bp.route("/ratings")
@admin_required
def admin_ratings():
    ratings_list = rating_manager.get_all_ratings()

    # Ajout d'attributs pour le template
    ratings = []
    for r, file in zip(ratings_list, rating_manager.ratings_dir.glob("rating_*.json")):
        r_copy = r.copy()
        r_copy["id"] = file.name
        ts = r.get("timestamp")
        if ts:
            r_copy["display_date"] = datetime.fromisoformat(ts).strftime("%d/%m/%Y %H:%M")
        else:
            r_copy["display_date"] = "-"
        r_copy["page"] = r.get("page", "-")
        ratings.append(r_copy)

    stats = rating_manager.get_stats()
    return render_template("admin/ratings.html", ratings=ratings, stats=stats)

