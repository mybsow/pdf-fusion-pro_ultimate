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
from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email

# ============================================================
# FORMULAIRES
# ============================================================
class ContactForm(FlaskForm):
    """Formulaire de contact avec WTForms"""
    name = StringField(_l('Nom complet'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    message = TextAreaField(_l('Message'), validators=[DataRequired()])

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
        return True

# ============================================================
# ROUTE CONTACT
# ============================================================

@legal_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    success = False
    error = None

    if form.validate_on_submit():
        form_data = {
            "first_name": form.name.data.split()[0] if form.name.data else "",
            "last_name": " ".join(form.name.data.split()[1:]) if form.name.data and len(form.name.data.split()) > 1 else "",
            "email": form.email.data.lower(),
            "phone": request.form.get("phone", "").strip(),
            "subject": "contact",
            "message": form.message.data,
        }

        try:
            saved = contact_manager.save_message(**form_data)
            send_discord_notification(form_data)
            
            if saved:
                success = True
                flash(_('Votre message a été envoyé avec succès !'), 'success')
                form = ContactForm()
            else:
                error = _('Une erreur technique est survenue. Veuillez réessayer.')
        except Exception:
            error = _('Une erreur technique est survenue. Veuillez réessayer.')

    return render_template(
        "legal/contact.html",
        title=_("Contact"),
        badge=_("Formulaire de contact"),
        subtitle=_("Contactez-nous via notre formulaire"),
        form=form,
        success=success,
        error=error,
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/legal')
def legal():
    return render_template(
        "legal/legal.html",
        title=_("Mentions Légales"),
        badge=_("Information légale"),
        subtitle=_("Informations légales concernant l'utilisation du service PDF Fusion Pro"),
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/privacy')
def privacy():
    return render_template(
        "legal/privacy.html",
        title=_("Politique de Confidentialité"),
        badge=_("Protection des données"),
        subtitle=_("Comment nous protégeons et utilisons vos données"),
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/terms')
def terms():
    return render_template(
        "legal/terms.html",
        title=_("Conditions d'Utilisation"),
        badge=_("Règles d'usage"),
        subtitle=_("Règles et conditions d'utilisation du service PDF Fusion Pro"),
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


@legal_bp.route('/about')
def about():
    return render_template(
        "legal/about.html",
        title=_("À Propos"),
        badge=_("Notre histoire"),
        subtitle=_("Découvrez PDF Fusion Pro, notre mission et nos valeurs"),
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


# ============================================================
# ROUTES DE REDIRECTION
# ============================================================

@legal_bp.route('/mentions-legales')
def redirect_legal():
    return redirect(url_for('legal.legal'), code=301)

@legal_bp.route('/politique-confidentialite')
def redirect_privacy():
    return redirect(url_for('legal.privacy'), code=301)

@legal_bp.route('/conditions-utilisation')
def redirect_terms():
    return redirect(url_for('legal.terms'), code=301)

@legal_bp.route('/a-propos')
def redirect_about():
    return redirect(url_for('legal.about'), code=301)
