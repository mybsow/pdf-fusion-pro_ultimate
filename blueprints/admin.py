"""
Blueprint Admin pour PDF Fusion Pro Ultimate
Dashboard moderne avec cache intelligent et gestion complète
"""

import os
import json
from functools import wraps
from datetime import datetime
from flask import Blueprint, session, request, redirect, url_for, render_template, jsonify

from utils.cache import SimpleCache
from managers.contact_manager import ContactManager
from managers.rating_manager import RatingManager
from managers.stats_manager import StatisticsManager
from flask_babel import _, lazy_gettext as _l

# Pour les textes statiques
flash(_('Votre fichier a été converti avec succès'))

# Pour les textes avec variables
flash(_('Bienvenue %(username)s', username=user.name))

# Pour les formulaires (évaluation tardive)
class ContactForm(FlaskForm):
    name = StringField(_l('Nom'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])

# Initialiser les managers
contact_manager = ContactManager()
rating_manager = RatingManager()
stats_manager = StatisticsManager()

# Cache avec TTL réduit pour des données plus fraîches
cache = SimpleCache(ttl=10)  # 10 secondes au lieu de 15

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# -----------------------
# Helper functions
# -----------------------
def time_ago(date_obj):
    """Convertit une date en format 'il y a...'"""
    if not date_obj:
        return "Date inconnue"
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except:
            return date_obj
    
    now = datetime.now()
    diff = now - date_obj
    
    if diff.days > 365:
        years = diff.days // 365
        return f"il y a {years} an{'s' if years > 1 else ''}"
    if diff.days > 30:
        months = diff.days // 30
        return f"il y a {months} mois"
    if diff.days > 0:
        return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
    if diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    if diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    return "à l'instant"

def format_timestamp(timestamp_str):
    """Formate un timestamp ISO en date lisible"""
    if not timestamp_str:
        return "-"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return timestamp_str

# -----------------------
# Authentication decorator
# -----------------------
def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged"):
            return redirect(url_for("admin.admin_login"))
        return view(*args, **kwargs)
    return wrapped

# -----------------------
# Login / Logout
# -----------------------
@admin_bp.route("/", methods=["GET", "POST"])
def admin_login():
    """Page de connexion admin"""
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if password == ADMIN_PASSWORD:
            session["admin_logged"] = True
            session["admin_login_time"] = datetime.now().isoformat()
            return redirect(url_for("admin.admin_dashboard"))
        return render_template("admin/login.html", error="Mot de passe incorrect")
    return render_template("admin/login.html")

@admin_bp.route("/logout")
def admin_logout():
    """Déconnexion admin"""
    session.clear()
    return redirect(url_for("admin.admin_login"))

# -----------------------
# Dashboard principal
# -----------------------
@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    """Dashboard principal avec statistiques en temps réel"""
    # Force le rafraîchissement si demandé
    force_refresh = request.args.get('refresh') == 'true'
    
    # Récupération depuis le cache (sauf si force_refresh)
    cached_stats = cache.get("dashboard_stats")
    
    if not cached_stats or force_refresh:
        print("🔄 Régénération des stats du dashboard...")
        
        try:
            # =========================
            # Messages de contact
            # =========================
            all_messages = contact_manager.get_all_sorted()
            recent_messages = []
            
            for msg in all_messages[:10]:  # 10 messages max pour l'affichage
                msg_copy = msg.copy()
                # Formater la date
                msg_copy["formatted_date"] = format_timestamp(msg.get("timestamp"))
                msg_copy["time_ago"] = time_ago(msg.get("timestamp"))
                recent_messages.append(msg_copy)
            
            # =========================
            # Évaluations (ratings)
            # =========================
            # Force le rafraîchissement si demandé
            # Par (pour plus de debug) :
            all_ratings = rating_manager.get_all_ratings(force_refresh=True)
            print(f"📊 Ratings chargés: {len(all_ratings)}")
            if all_ratings:
                print(f"📊 Exemple rating: {all_ratings[0]}")
            
            # Formater les ratings pour l'affichage
            formatted_ratings = []
            for rating in all_ratings[:15]:  # 15 ratings max pour l'affichage
                r_copy = rating.copy()
                # Date formatée
                r_copy["formatted_date"] = format_timestamp(rating.get("timestamp"))
                r_copy["time_ago"] = time_ago(rating.get("timestamp"))
                # Compatibilité avec le template
                r_copy["display_date"] = r_copy["formatted_date"]  # ← AJOUT IMPORTANT
                # Page simplifiée
                page = rating.get("page", "/")
                if page == "/":
                    r_copy["page_name"] = "Accueil"
                elif "fusion" in page:
                    r_copy["page_name"] = "Fusion PDF"
                elif "division" in page:
                    r_copy["page_name"] = "Division PDF"
                elif "rotation" in page:
                    r_copy["page_name"] = "Rotation PDF"
                elif "compress" in page:
                    r_copy["page_name"] = "Compression PDF"
                else:
                    r_copy["page_name"] = page
                
                formatted_ratings.append(r_copy)
            
            # Stats de ratings
            rating_stats = rating_manager.get_stats()
            # Dans admin_dashboard(), après avoir chargé les ratings :
            print(f"📊 DEBUG - Nombre de ratings: {len(all_ratings)}")
            print(f"📊 DEBUG - Répertoire ratings: {rating_manager.ratings_dir}")
            print(f"📊 DEBUG - Fichiers dans ratings: {list(rating_manager.ratings_dir.glob('*.json'))}")
            
            # =========================
            # Statistiques d'utilisation
            # =========================
            # Sessions aujourd'hui (approximation)
            today = datetime.now().strftime("%Y-%m-%d")
            daily_stats = stats_manager.stats.get("daily_stats", {})
            sessions_today = sum(daily_stats.get(today, {}).values()) if today in daily_stats else 0
            
            # =========================
            # Compilation des stats
            # =========================
            stats = {
                # Informations générales
                "generated_at": datetime.now().isoformat(),
                "cache_refresh": force_refresh,
                
                # Messages
                "total_messages": len(all_messages),
                "unseen_messages": contact_manager.get_unseen_count(),
                "recent_messages": recent_messages[:5],  # 5 pour le dashboard
                "all_messages_count": len(all_messages),
                
                # Évaluations
                "total_ratings": rating_stats.get("total", 0),
                "avg_rating": rating_stats.get("average", 0),
                "total_comments": rating_stats.get("comments", 0),
                "recent_ratings": formatted_ratings[:5],  # 5 pour le dashboard
                "all_ratings": formatted_ratings,
                "ratings_distribution": rating_stats.get("distribution", {1:0, 2:0, 3:0, 4:0, 5:0}),
                "unseen_ratings": rating_stats.get("unseen", 0),
                
                # Sessions et utilisation
                "sessions_today": sessions_today,
                "total_operations": stats_manager.get_stat("total_operations", 0),
                "merges_today": daily_stats.get(today, {}).get("merges", 0),
                "splits_today": daily_stats.get(today, {}).get("splits", 0),
                "rotations_today": daily_stats.get(today, {}).get("rotations", 0),
                "compressions_today": daily_stats.get(today, {}).get("compressions", 0),
                
                # Stats globales
                "total_merges": stats_manager.get_stat("merges", 0),
                "total_splits": stats_manager.get_stat("splits", 0),
                "total_rotations": stats_manager.get_stat("rotations", 0),
                "total_compressions": stats_manager.get_stat("compressions", 0),
            }
            
            # Mise en cache
            cache.set("dashboard_stats", stats)
            cached_stats = stats
            
            print(f"✅ Stats régénérées: {len(all_messages)} messages, {len(all_ratings)} ratings")
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des stats: {e}")
            # Fallback avec des données minimales
            cached_stats = {
                "total_messages": 0,
                "unseen_messages": 0,
                "total_ratings": 0,
                "avg_rating": 0,
                "total_comments": 0,
                "recent_messages": [],
                "recent_ratings": [],
                "ratings_distribution": {1:0, 2:0, 3:0, 4:0, 5:0},
                "error": str(e)
            }
    
    # Ajouter l'année courante pour le footer
    return render_template("admin/dashboard.html", 
                         stats=cached_stats, 
                         current_year=datetime.now().year)

@admin_bp.route("/dashboard/refresh")
@admin_required
def refresh_dashboard():
    """Force le rafraîchissement du cache du dashboard"""
    cache.set("dashboard_stats", None)
    # Invalider aussi le cache des managers
    rating_manager._cache = None
    return redirect(url_for("admin.admin_dashboard", refresh='true'))

@admin_bp.route("/dashboard/api")
@admin_required
def dashboard_api():
    """API JSON pour le dashboard (utilisé par AJAX)"""
    force_refresh = request.args.get('refresh') == 'true'
    
    # Similaire à admin_dashboard mais retourne du JSON
    all_messages = contact_manager.get_all_sorted()
    all_ratings = rating_manager.get_all_ratings(force_refresh=force_refresh)
    rating_stats = rating_manager.get_stats()
    
    today = datetime.now().strftime("%Y-%m-%d")
    daily_stats = stats_manager.stats.get("daily_stats", {})
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "messages": {
            "total": len(all_messages),
            "unseen": contact_manager.get_unseen_count(),
            "recent": [
                {
                    "id": msg.get("id"),
                    "name": f"{msg.get('first_name', '')} {msg.get('last_name', '')}",
                    "subject": msg.get("subject", ""),
                    "preview": (msg.get("message", "")[:50] + "...") if len(msg.get("message", "")) > 50 else msg.get("message", ""),
                    "time_ago": time_ago(msg.get("timestamp")),
                    "seen": msg.get("seen", False)
                }
                for msg in all_messages[:5]
            ]
        },
        "ratings": {
            "total": rating_stats.get("total", 0),
            "average": rating_stats.get("average", 0),
            "distribution": rating_stats.get("distribution", {}),
            "unseen": rating_stats.get("unseen", 0),
            "recent": [
                {
                    "rating": r.get("rating", 0),
                    "feedback": r.get("feedback", ""),
                    "time_ago": time_ago(r.get("timestamp")),
                    "page": r.get("page", "/"),
                    "seen": r.get("seen", False)
                }
                for r in all_ratings[:5]
            ]
        },
        "operations": {
            "today": {
                "total": sum(daily_stats.get(today, {}).values()),
                "merges": daily_stats.get(today, {}).get("merges", 0),
                "splits": daily_stats.get(today, {}).get("splits", 0),
                "rotations": daily_stats.get(today, {}).get("rotations", 0),
                "compressions": daily_stats.get(today, {}).get("compressions", 0)
            },
            "all_time": {
                "total": stats_manager.get_stat("total_operations", 0),
                "merges": stats_manager.get_stat("merges", 0),
                "splits": stats_manager.get_stat("splits", 0),
                "rotations": stats_manager.get_stat("rotations", 0),
                "compressions": stats_manager.get_stat("compressions", 0)
            }
        }
    }
    
    return jsonify(data)

# -----------------------
# Injection du badge de messages non lus
# -----------------------
@admin_bp.app_context_processor
def inject_unread_count():
    """Injecte le nombre de messages non lus dans tous les templates admin"""
    try:
        count = contact_manager.get_unseen_count()
        # Ajouter aussi les ratings non vus
        rating_stats = rating_manager.get_stats()
        rating_unseen = rating_stats.get("unseen", 0)
        
        return {
            "unread_count": count,
            "unread_ratings": rating_unseen,
            "total_unread": count + rating_unseen
        }
    except:
        return {"unread_count": 0, "unread_ratings": 0, "total_unread": 0}

# -----------------------
# Gestion des Messages
# -----------------------
@admin_bp.route("/messages")
@admin_required
def admin_messages():
    """Page de gestion des messages"""
    show_archived = request.args.get('archived') == 'true'
    
    if show_archived:
        # Pour les messages archivés, on pourrait avoir une méthode spécifique
        # Pour l'instant, on filtre depuis tous les messages
        all_messages = contact_manager.get_all_sorted()
        messages = [m for m in all_messages if m.get("archived", False)]
        page_title = "Messages Archivés"
    else:
        messages = contact_manager.get_all_sorted()
        page_title = "Messages de Contact"
    
    # Formater les dates
    for msg in messages:
        msg["formatted_date"] = format_timestamp(msg.get("timestamp"))
        msg["time_ago"] = time_ago(msg.get("timestamp"))
    
    return render_template("admin/messages.html", 
                         messages=messages, 
                         page_title=page_title,
                         show_archived=show_archived)

@admin_bp.route("/messages/seen/all")
@admin_required
def mark_all_messages_seen():
    """Marquer tous les messages comme lus"""
    contact_manager.mark_all_seen()
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/seen/<int:message_id>")
@admin_required
def mark_message_seen(message_id):
    """Marquer un message spécifique comme lu"""
    contact_manager.mark_seen(message_id)
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/archive/<int:message_id>", methods=["POST"])
@admin_required
def archive_message(message_id):
    """Archiver un message"""
    contact_manager.archive_message(message_id)
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/unarchive/<int:message_id>", methods=["POST"])
@admin_required
def unarchive_message(message_id):
    """Désarchiver un message"""
    # Note: Vous devrez ajouter cette méthode à contact_manager
    # Pour l'instant, redirection simple
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/delete/<int:message_id>", methods=["POST"])
@admin_required
def delete_message(message_id):
    """Supprimer un message"""
    contact_manager.delete(message_id)
    return redirect(url_for("admin.admin_messages"))

@admin_bp.route("/messages/<int:message_id>")
@admin_required
def view_message(message_id):
    """Voir un message spécifique"""
    all_messages = contact_manager.get_all_sorted()
    message = next((m for m in all_messages if m.get("id") == message_id), None)
    
    if not message:
        return "Message non trouvé", 404
    
    # Marquer comme lu quand on le consulte
    contact_manager.mark_seen(message_id)
    
    message["formatted_date"] = format_timestamp(message.get("timestamp"))
    message["time_ago"] = time_ago(message.get("timestamp"))
    
    return render_template("admin/message_detail.html", message=message)

# -----------------------
# Gestion des Évaluations (Ratings)
# -----------------------
@admin_bp.route("/ratings")
@admin_required
def admin_ratings():
    """Page de gestion des évaluations"""
    force_refresh = request.args.get('refresh') == 'true'
    show_unseen = request.args.get('unseen') == 'true'
    
    # Récupérer toutes les évaluations
    all_ratings = rating_manager.get_all_ratings(force_refresh=force_refresh)
    
    # Filtrer si nécessaire
    if show_unseen:
        ratings = [r for r in all_ratings if not r.get("seen", False)]
        page_title = "Évaluations Non Vues"
    else:
        ratings = all_ratings
        page_title = "Toutes les Évaluations"
    
    # Formater les données pour l'affichage
    formatted_ratings = []
    for rating in ratings:
        r_copy = rating.copy()
        # Date formatée
        r_copy["formatted_date"] = format_timestamp(rating.get("timestamp"))
        r_copy["time_ago"] = time_ago(rating.get("timestamp"))
        
        # Page simplifiée
        page = rating.get("page", "/")
        if page == "/":
            r_copy["page_name"] = "Accueil"
        elif "fusion" in page:
            r_copy["page_name"] = "Fusion PDF"
        elif "division" in page:
            r_copy["page_name"] = "Division PDF"
        elif "rotation" in page:
            r_copy["page_name"] = "Rotation PDF"
        elif "compress" in page:
            r_copy["page_name"] = "Compression PDF"
        else:
            r_copy["page_name"] = page
        
        # ID pour les actions
        r_copy["file_id"] = rating.get("file_id", "")
        
        formatted_ratings.append(r_copy)
    
    # Statistiques
    stats = rating_manager.get_stats()
    
    return render_template("admin/ratings.html", 
                         ratings=formatted_ratings, 
                         stats=stats,
                         page_title=page_title,
                         show_unseen=show_unseen)

@admin_bp.route("/ratings/seen/all")
@admin_required
def mark_all_ratings_seen():
    """Marquer toutes les évaluations comme vues"""
    rating_manager.mark_all_seen()
    return redirect(url_for("admin.admin_ratings"))

@admin_bp.route("/ratings/seen/<rating_id>")
@admin_required
def mark_rating_seen(rating_id):
    """Marquer une évaluation spécifique comme vue"""
    # Note: Vous devrez implémenter cette méthode dans rating_manager
    # Pour l'instant, redirection
    return redirect(url_for("admin.admin_ratings"))

@admin_bp.route("/ratings/delete/<rating_id>", methods=["POST"])
@admin_required
def delete_rating(rating_id):
    """Supprimer une évaluation"""
    rating_manager.delete_rating(rating_id)
    return redirect(url_for("admin.admin_ratings"))

@admin_bp.route("/ratings/export")
@admin_required
def export_ratings():
    """Exporter les évaluations en JSON"""
    ratings = rating_manager.get_all_ratings(force_refresh=True)
    
    export_data = {
        "export_date": datetime.now().isoformat(),
        "total_ratings": len(ratings),
        "ratings": ratings
    }
    
    response = jsonify(export_data)
    response.headers.add('Content-Disposition', 'attachment; filename=ratings_export.json')
    return response

# -----------------------
# Statistiques détaillées
# -----------------------
@admin_bp.route("/stats")
@admin_required
def admin_stats():
    """Page de statistiques détaillées"""
    # Données de base
    today = datetime.now().strftime("%Y-%m-%d")
    daily_stats = stats_manager.stats.get("daily_stats", {})
    
    # Préparer les données pour les graphiques
    last_7_days = []
    for i in range(6, -1, -1):
        date = (datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        day_stats = daily_stats.get(date, {})
        last_7_days.append({
            "date": date,
            "total": sum(day_stats.values()),
            "merges": day_stats.get("merges", 0),
            "splits": day_stats.get("splits", 0),
            "rotations": day_stats.get("rotations", 0),
            "compressions": day_stats.get("compressions", 0)
        })
    
    stats_data = {
        "today": today,
        "today_stats": daily_stats.get(today, {}),
        "last_7_days": last_7_days,
        "all_time": {
            "total_operations": stats_manager.get_stat("total_operations", 0),
            "merges": stats_manager.get_stat("merges", 0),
            "splits": stats_manager.get_stat("splits", 0),
            "rotations": stats_manager.get_stat("rotations", 0),
            "compressions": stats_manager.get_stat("compressions", 0),
            "user_sessions": stats_manager.get_stat("user_sessions", 0),
            "zip_downloads": stats_manager.get_stat("zip_downloads", 0),
            "previews": stats_manager.get_stat("previews", 0)
        }
    }
    
    return render_template("admin/stats.html", stats=stats_data)

# -----------------------
# Debug et maintenance
# -----------------------
@admin_bp.route("/debug")
@admin_required
def admin_debug():
    """Page de débogage pour vérifier les données"""
    import os
    from pathlib import Path
    
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "files": {
            "contacts_json": {
                "path": "data/contacts.json",
                "exists": os.path.exists("data/contacts.json"),
                "size": os.path.getsize("data/contacts.json") if os.path.exists("data/contacts.json") else 0,
                "content_sample": None
            },
            "ratings_dir": {
                "path": "data/ratings",
                "exists": os.path.exists("data/ratings"),
                "file_count": len(list(Path("data/ratings").glob("*.json"))) if os.path.exists("data/ratings") else 0,
                "files": [f.name for f in Path("data/ratings").glob("*.json")][:10] if os.path.exists("data/ratings") else []
            }
        },
        "managers": {
            "contact_manager": {
                "total_messages": len(contact_manager.get_all_sorted()),
                "unseen_count": contact_manager.get_unseen_count()
            },
            "rating_manager": {
                "total_ratings": len(rating_manager.get_all_ratings()),
                "stats": rating_manager.get_stats()
            },
            "stats_manager": {
                "total_operations": stats_manager.get_stat("total_operations", 0)
            }
        },
        "cache": {
            "dashboard_stats_cached": cache.get("dashboard_stats") is not None,
            "cache_ttl": cache.ttl
        }
    }
    
    # Lire un échantillon des contacts
    try:
        if os.path.exists("data/contacts.json"):
            with open("data/contacts.json", "r") as f:
                contacts = json.load(f)
                debug_info["files"]["contacts_json"]["content_sample"] = contacts[:3] if contacts else []
    except Exception as e:
        debug_info["files"]["contacts_json"]["error"] = str(e)
    
    return render_template("admin/debug.html", debug_info=debug_info)

@admin_bp.route("/repair/contacts")
@admin_required
def repair_contacts():
    """Réparer le fichier contacts.json"""
    import json
    from pathlib import Path
    
    contacts_file = Path("data/contacts.json")
    
    if contacts_file.exists():
        try:
            # Essayer de lire le fichier
            with open(contacts_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            if content.strip():
                # Essayer de parser le JSON
                json.loads(content)
                return "✅ Fichier contacts.json est valide", 200
            else:
                # Fichier vide, le réinitialiser
                with open(contacts_file, "w", encoding="utf-8") as f:
                    f.write("[]")
                return "✅ Fichier contacts.json réinitialisé (était vide)", 200
                
        except json.JSONDecodeError:
            # Fichier invalide, créer une sauvegarde et réinitialiser
            backup = contacts_file.with_suffix('.json.backup')
            contacts_file.rename(backup)
            
            with open(contacts_file, "w", encoding="utf-8") as f:
                f.write("[]")
            
            return f"✅ Fichier contacts.json réparé. Backup créé: {backup.name}", 200
            
    else:
        # Créer le fichier s'il n'existe pas
        contacts_file.parent.mkdir(exist_ok=True)
        with open(contacts_file, "w", encoding="utf-8") as f:
            f.write("[]")
        return "✅ Fichier contacts.json créé", 200

@admin_bp.route("/debug/clear-cache")
@admin_required
def clear_cache():
    """Vider tous les caches"""
    cache.set("dashboard_stats", None)
    rating_manager._cache = None
    return redirect(url_for("admin.admin_debug"))
