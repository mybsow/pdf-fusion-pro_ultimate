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


@legal_bp.route('/admin/ratings')
def admin_ratings():
    """Page admin pour voir les évaluations"""
    # Protection basique par mot de passe
    if request.args.get('token') != 'votre_token_secret':
        return "Accès non autorisé", 403
    
    try:
        with open('data/ratings.json', 'r', encoding='utf-8') as f:
            ratings = json.load(f)
        
        # Calculer les stats
        total = len(ratings)
        average = calculate_average_rating(ratings)
        distribution = {1:0, 2:0, 3:0, 4:0, 5:0}
        
        for r in ratings:
            distribution[r['rating']] += 1
        
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Évaluations - Admin</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-4">
                <h1>📊 Évaluations des utilisateurs</h1>
                
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card text-white bg-primary mb-3">
                            <div class="card-body text-center">
                                <h1 class="display-1">{{ total }}</h1>
                                <p class="card-text">Évaluations totales</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-white bg-success mb-3">
                            <div class="card-body text-center">
                                <h1 class="display-1">{{ average }}</h1>
                                <p class="card-text">Note moyenne</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <h3 class="mt-4">Distribution des notes</h3>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>⭐ Note</th>
                            <th>Nombre</th>
                            <th>Pourcentage</th>
                            <th>Barre</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for rating in [5,4,3,2,1] %}
                        <tr>
                            <td>{{ rating }} étoiles</td>
                            <td>{{ distribution[rating] }}</td>
                            <td>{{ (distribution[rating]/total*100)|round(1) }}%</td>
                            <td>
                                <div class="progress">
                                    <div class="progress-bar" style="width: {{ distribution[rating]/total*100 }}%"></div>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                
                <h3 class="mt-4">Dernières évaluations</h3>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Note</th>
                                <th>Feedback</th>
                                <th>Page</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for r in ratings[-20:]|reverse %}
                            <tr>
                                <td>{{ r.timestamp[:19] }}</td>
                                <td>
                                    {% for i in range(r.rating) %}⭐{% endfor %}
                                </td>
                                <td>{{ r.feedback or '-' }}</td>
                                <td>{{ r.page }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        ''', total=total, average=average, distribution=distribution, ratings=ratings)
    
    except FileNotFoundError:
        return "Aucune évaluation pour le moment", 404
