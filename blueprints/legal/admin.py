import os
from functools import wraps
from flask import (
    session,
    request,
    redirect,
    url_for,
    render_template,
    abort
)
from . import legal_bp
from rating_manager import ratings_manager

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


# =========================
# Décorateur de sécurité
# =========================
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged"):
            return redirect(url_for("legal.admin_login"))
        return view(*args, **kwargs)
    return wrapped


# =========================
# Login admin
# =========================
@legal_bp.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged"] = True
            return redirect(url_for("legal.admin_dashboard"))
        abort(403)

    return render_template("legal/admin/login.html")


# =========================
# Dashboard admin
# =========================
@legal_bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    stats = ratings_manager.get_stats()

    return render_template(
        "legal/admin/dashboard.html",
        stats=stats
    )


# =========================
# Page évaluations
# =========================
@legal_bp.route("/admin/ratings")
@admin_required
def admin_ratings():
    ratings = ratings_manager.get_all_ratings()
    stats = ratings_manager.get_stats()

    # Marquer comme vues
    ratings_manager.mark_all_seen()

    return render_template(
        "legal/admin/ratings.html",
        ratings=ratings,
        stats=stats
    )


# =========================
# Logout
# =========================
@legal_bp.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("legal.admin_login"))
