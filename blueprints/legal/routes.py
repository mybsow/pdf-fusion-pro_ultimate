from flask import render_template, request  # Changé : render_template au lieu de render_template_string
from datetime import datetime
from pathlib import Path
import os
import requests

from . import legal_bp
from config import AppConfig
from managers.contact_manager import contact_manager

# ============================================================
# NOTIFICATIONS (gardez cette fonction)
# ============================================================
def send_discord_notification(form_data):
    # [Gardez votre code existant]
    pass

# ============================================================
# ROUTE CONTACT (modifiée pour utiliser un template)
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

        # Validation (gardez votre code existant)
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
                saved = contact_manager.save_message(**form_data)
                send_discord_notification(form_data)
                
                if saved:
                    success = True
                else:
                    error = "Une erreur technique est survenue. Veuillez réessayer."
            except Exception:
                error = "Une erreur technique est survenue. Veuillez réessayer."
    
    return render_template(
        "legal/contact.html",  # Chemin vers le template
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

# ============================================================
# AUTRES ROUTES (simplifiées)
# ============================================================

@legal_bp.route('/mentions-legales')
def legal_notices():
    return render_template(
        "legal/legal.html",  # Chemin vers le template
        title="Mentions Légales",
        badge="Information légale",
        subtitle="Informations légales concernant l'utilisation du service PDF Fusion Pro",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )

@legal_bp.route('/politique-confidentialite')
def privacy_policy():
    return render_template(
        "legal/privacy.html",
        title="Politique de Confidentialité",
        badge="Protection des données",
        subtitle="Comment nous protégeons et utilisons vos données",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )

@legal_bp.route('/conditions-utilisation')
def terms_of_service():
    return render_template(
        "legal/terms.html",
        title="Conditions d'Utilisation",
        badge="Règles d'usage",
        subtitle="Règles et conditions d'utilisation du service PDF Fusion Pro",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )

@legal_bp.route('/a-propos')
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
