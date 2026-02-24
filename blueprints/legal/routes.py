"""
Routes pour les pages légales
Version production sécurisée
"""

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)
from datetime import datetime
import os
import requests

from . import legal_bp
from config import AppConfig
from managers.contact_manager import contact_manager
from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional, Email, Length


# ============================================================
# FORMULAIRE CONTACT
# ============================================================

class ContactForm(FlaskForm):
    """Formulaire de contact"""

    full_name = StringField(
        _l('Nom complet'),
        validators=[DataRequired(), Length(min=2, max=100)]
    )

    email = StringField(
        _l('Email'),
        validators=[Optional(), Email()]
    )

    phone = StringField(
        _l('Téléphone (optionnel)'),
        validators=[Optional()]
    )

    subject = SelectField(
        _l('Sujet'),
        choices=[
            ('bug', '🚨 ' + _l('Signaler un bug ou un problème technique')),
            ('improvement', '💡 ' + _l('Proposer une amélioration fonctionnelle')),
            ('partnership', '🤝 ' + _l('Demande de partenariat')),
            ('other', '❓ ' + _l('Autre demande')),
        ],
        validators=[DataRequired()]
    )

    message = TextAreaField(
        _l('Message'),
        validators=[DataRequired(), Length(max=2000)]
    )


# ============================================================
# DISCORD WEBHOOK
# ============================================================

def send_discord_notification(form_data: dict) -> None:
    """Envoie notification Discord (non bloquant)"""

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return

    try:
        subject_map = {
            "bug": "🚨 Bug",
            "improvement": "💡 Amélioration",
            "partnership": "🤝 Partenariat",
            "other": "❓ Autre"
        }

        full_name = form_data.get("full_name", "").strip()
        parts = full_name.split()
        first_name = parts[0] if parts else "N/A"
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        embed = {
            "title": "📨 Nouveau message de contact",
            "color": 0x4361EE,
            "fields": [
                {"name": "Nom", "value": f"{first_name} {last_name}", "inline": True},
                {"name": "Email", "value": form_data.get("email", "Non renseigné"), "inline": True},
                {"name": "Sujet", "value": subject_map.get(form_data.get("subject"), form_data.get("subject")), "inline": False},
                {"name": "Message", "value": form_data.get("message", "")[:1000], "inline": False},
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

    except Exception:
        # On ignore volontairement les erreurs Discord
        current_app.logger.warning("Webhook Discord échoué")


# ============================================================
# ROUTE CONTACT
# ============================================================

@legal_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    success = False
    error = None
    form_data = {}

    if form.validate_on_submit():

        email_value = (form.email.data or "").strip().lower()

        form_data = {
            "full_name": form.full_name.data.strip(),
            "email": email_value,
            "phone": (form.phone.data or "").strip(),
            "subject": form.subject.data,
            "message": form.message.data.strip(),
        }

        try:
            name_parts = form_data["full_name"].split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

            saved = contact_manager.save_message(
                first_name=first_name,
                last_name=last_name,
                email=form_data["email"],
                phone=form_data["phone"],
                subject=form_data["subject"],
                message=form_data["message"],
            )

            send_discord_notification(form_data)

            if saved:
                success = True
                flash(_('Votre message a été envoyé avec succès !'), 'success')
                form = ContactForm()
                form_data = {}
            else:
                error = _('Une erreur technique est survenue. Veuillez réessayer.')

        except Exception:
            current_app.logger.exception("Erreur sauvegarde formulaire contact")
            error = _('Une erreur technique est survenue. Veuillez réessayer.')

    elif request.method == "POST":
        # Conserver les valeurs si validation échoue
        form_data = {
            "full_name": request.form.get("full_name", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "subject": request.form.get("subject", ""),
            "message": request.form.get("message", ""),
        }

    return render_template(
        "legal/contact.html",
        title=_("Contact"),
        badge=_("Formulaire de contact"),
        subtitle=_("Contactez-nous via notre formulaire"),
        form=form,
        form_data=form_data,
        success=success,
        error=error,
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime
    )


# ============================================================
# AUTRES PAGES LÉGALES
# ============================================================

@legal_bp.route("/legal")
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


@legal_bp.route("/privacy")
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


@legal_bp.route("/terms")
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


@legal_bp.route("/about")
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
# REDIRECTIONS SEO
# ============================================================

@legal_bp.route("/mentions-legales")
def redirect_legal():
    return redirect(url_for("legal.legal"), code=301)


@legal_bp.route("/politique-confidentialite")
def redirect_privacy():
    return redirect(url_for("legal.privacy"), code=301)


@legal_bp.route("/conditions-utilisation")
def redirect_terms():
    return redirect(url_for("legal.terms"), code=301)


@legal_bp.route("/a-propos")
def redirect_about():
    return redirect(url_for("legal.about"), code=301)
