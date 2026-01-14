from flask import session, request, redirect, url_for, abort, render_template_string
import os

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

@legal_bp.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged"] = True
            return redirect("/admin/dashboard")
        return "Accès refusé", 401

    return '''
    <form method="POST">
        <input type="password" name="password" placeholder="Mot de passe admin">
        <button>Connexion</button>
    </form>
    '''
from rating_manager import ratings_manager

@legal_bp.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged"):
        return redirect("/admin")

    stats = ratings_manager.get_stats()

    badge = (
        f"<span style='color:red;font-weight:bold;'>({stats['recent_count']} nouveau)</span>"
        if stats["recent_count"] > 0 else ""
    )

    return render_template_string(f"""
    <h1>Admin – Dashboard</h1>

    <ul>
        <li>⭐ Évaluations totales : {stats['total']}</li>
        <li>📊 Note moyenne : {stats['average']}</li>
        <li>🔔 Nouvelles (24h) : {stats['recent_count']}</li>
    </ul>

    <a href="/admin/ratings">Voir évaluations {badge}</a><br><br>
    <a href="/admin/logout">Déconnexion</a>
    """)
@legal_bp.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/")


from flask import render_template, session, redirect, url_for
from blueprints.legal import legal_bp
from utils.ratings_manager import ratings_manager

@legal_bp.route("/admin/ratings")
def admin_ratings():
    if not session.get("admin_logged_in"):
        return redirect(url_for("legal.admin_login"))

    ratings = ratings_manager.get_all_ratings()
    stats = ratings_manager.get_stats()

    return render_template(
        "admin/ratings.html",
        ratings=ratings,
        stats=stats,
        has_new=ratings_manager.has_new_ratings(24)
    )
    
    except FileNotFoundError:
        return "Aucune évaluation pour le moment", 404
