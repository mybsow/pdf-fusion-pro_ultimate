"""
Routes pour les pages légales
"""

from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import requests

from . import legal_bp
from config import AppConfig
from managers.contact_manager import contact_manager

# ============================================================
# NOTIFICATIONS
# ============================================================
def send_discord_notification(form_data):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return True

    try:
        subject_map = {
            "bug": "🚨 Bug",
            "improvement": "💡 Amélioration",
            "partnership": "🤝 Partenariat",
            "other": "❓ Autre"
        }

        embed = {
            "title": "📨 Nouveau message de contact",
            "color": 0x4361EE,
            "fields": [
                {"name": "Nom", "value": f"{form_data['first_name']} {form_data['last_name']}", "inline": True},
                {"name": "Email", "value": form_data["email"], "inline": True},
                {"name": "Sujet", "value": subject_map.get(form_data["subject"], form_data["subject"]), "inline": False},
                {"name": "Message", "value": form_data["message"][:1000], "inline": False},
            ],
            "footer": {
                "text": f"{AppConfig.NAME} • {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            }
        }

        requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=3
        )
        return True

    except Exception:
        # Discord ne doit JAMAIS bloquer le formulaire
        return True


# ============================================================
# ROUTE CONTACT
# ============================================================

@legal_bp.route("/contact", methods=["GET", "POST"])
def contact():
    success = False
    error = None

    if request.method == "POST":
        form_data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "phone": request.form.get("phone", "").strip(),
            "subject": request.form.get("subject", "").strip(),
            "message": request.form.get("message", "").strip(),
        }

        # =====================
        # VALIDATION
        # =====================
        if not all([
            form_data["first_name"],
            form_data["last_name"],
            form_data["email"],
            form_data["subject"],
            form_data["message"],
        ]):
            error = "Veuillez remplir tous les champs obligatoires."
        elif len(form_data["message"]) > 2000:
            error = "Le message ne doit pas dépasser 2000 caractères."
        elif "@" not in form_data["email"]:
            error = "Adresse email invalide."
        else:
            try:
                # =====================
                # TRAITEMENT FIABLE
                # =====================
                saved = contact_manager.save_message(**form_data)
                send_discord_notification(form_data)
                
                if saved:
                    success = True
                else:
                    error = "Une erreur technique est survenue. Veuillez réessayer."
            except Exception:
                error = "Une erreur technique est survenue. Veuillez réessayer."

    return render_template(
        "legal/contact.html",
        title="Contact",
        badge="Formulaire de contact",
        subtitle="Contactez-nous via notre formulaire",
        success=success,
        error=error,
        form_data=request.form if request.method == "POST" else {},
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/legal')
def legal():
    return render_template(
        "legal/legal.html",
        title="Mentions Légales",
        badge="Information légale",
        subtitle="Informations légales concernant l'utilisation du service PDF Fusion Pro",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/privacy')
def privacy():
    return render_template(
        "legal/privacy.html",
        title="Politique de Confidentialité",
        badge="Protection des données",
        subtitle="Comment nous protégeons et utilisons vos données",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/terms')
def terms():
    return render_template(
        "legal/terms.html",
        title="Conditions d'Utilisation",
        badge="Règles d'usage",
        subtitle="Règles et conditions d'utilisation du service PDF Fusion Pro",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/about')
def about():
    return render_template(
        "legal/about.html",
        title="À Propos",
        badge="Notre histoire",
        subtitle="Découvrez PDF Fusion Pro, notre mission et nos valeurs",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


# ============================================================
# ROUTES DE REDIRECTION (pour garder la compatibilité)
# ============================================================

@legal_bp.route('/mentions-legales')
def redirect_legal():
    """Redirige l'ancienne URL vers la nouvelle."""
    return redirect(url_for('legal.legal'), code=301)

@legal_bp.route('/politique-confidentialite')
def redirect_privacy():
    """Redirige l'ancienne URL vers la nouvelle."""
    return redirect(url_for('legal.privacy'), code=301)

@legal_bp.route('/conditions-utilisation')
def redirect_terms():
    """Redirige l'ancienne URL vers la nouvelle."""
    return redirect(url_for('legal.terms'), code=301)

@legal_bp.route('/a-propos')
def redirect_about():
    """Redirige l'ancienne URL vers la nouvelle."""
    return redirect(url_for('legal.about'), code=301)
