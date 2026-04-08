"""
Routes pour les pages légales
Version production sécurisée et optimisée
"""

from flask import (
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    current_app
)
from markupsafe import escape
from datetime import datetime
from pathlib import Path
import os
import requests
import logging

from . import legal_bp
from config import AppConfig

# ===============================
# CONTACT MANAGER
# ===============================
try:
    from managers.contact_manager import contact_manager
except ImportError as e:
    logging.warning(f"⚠️ Contact manager non disponible: {e}")
    class DummyContactManager:
        def save_message(self, **kwargs):
            return True
    contact_manager = DummyContactManager()

# ===============================
# FLASK-BABEL
# ===============================
try:
    from flask_babel import _, lazy_gettext as _l
    BABEL_AVAILABLE = True
except ImportError:
    BABEL_AVAILABLE = False
    def _(s): return s
    def _l(s): return s

# ===============================
# FLASK-WTF & WTForms
# ===============================
try:
    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, SelectField
    from wtforms.validators import DataRequired, Optional, Email, Length
    FORMS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Flask-WTF non disponible: {e}")
    FORMS_AVAILABLE = False
    class FlaskForm:
        def __init__(self, *args, **kwargs):
            self.data = {}
        def validate_on_submit(self):
            return False
    class StringField: pass
    class TextAreaField: pass
    class SelectField: pass
    class DataRequired: pass
    class Optional: pass
    class Email: pass
    class Length: pass

# ===============================
# FORMULAIRE CONTACT
# ===============================
if FORMS_AVAILABLE:
    class ContactForm(FlaskForm):
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
                ('bug',         '🚨 ' + str(_l('Signaler un bug'))),
                ('improvement', '💡 ' + str(_l('Proposer une amélioration'))),
                ('partnership', '🤝 ' + str(_l('Partenariat'))),
                ('other',       '❓ ' + str(_l('Autre'))),
            ],
            validators=[DataRequired()]
        )
        message = TextAreaField(
            _l('Message'),
            validators=[DataRequired(), Length(max=2000)]
        )
else:
    class ContactForm:
        def __init__(self, *args, **kwargs):
            self.full_name = None
            self.email = None
            self.phone = None
            self.subject = None
            self.message = None
            self.data = {}
        def validate_on_submit(self):
            return False

# ===============================
# UTILITAIRES
# ===============================
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
                {"name": "Nom",       "value": escape(f"{first_name} {last_name}"),                                               "inline": True},
                {"name": "Email",     "value": escape(form_data.get("email",   "Non renseigné")),                                 "inline": True},
                {"name": "Téléphone", "value": escape(form_data.get("phone",   "Non renseigné")),                                 "inline": True},
                {"name": "Sujet",     "value": escape(subject_map.get(form_data.get("subject"), form_data.get("subject", ""))),   "inline": False},
                {"name": "Message",   "value": escape(form_data.get("message", "")[:1000]),                                       "inline": False},
            ],
            "footer": {"text": f"{AppConfig.NAME} • {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
        }
        r = requests.post(webhook_url, json={"embeds": [embed]}, timeout=3)
        if not r.ok:
            current_app.logger.warning(f"⚠️ Discord webhook status: {r.status_code}")
        else:
            current_app.logger.info("✅ Notification Discord envoyée")
    except requests.RequestException as e:
        current_app.logger.warning(f"⚠️ Discord webhook échoué: {e}")


def process_contact(form_data: dict) -> bool:
    """Valide et sauvegarde un message de contact, envoie Discord"""
    try:
        name_parts = form_data.get("full_name", "").split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        saved = contact_manager.save_message(
            first_name=first_name,
            last_name=last_name,
            email=form_data.get("email", ""),
            phone=form_data.get("phone", ""),
            subject=form_data.get("subject", ""),
            message=form_data.get("message", ""),
        )
        send_discord_notification(form_data)
        return saved
    except Exception as e:
        current_app.logger.exception(f"❌ Erreur process_contact: {e}")
        return False

# ===============================
# ROUTE CONTACT
# ===============================
@legal_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm() if FORMS_AVAILABLE else None
    success = False
    error = None
    form_data = {}
    current_time = datetime.now().strftime('%H:%M')

    if request.method == "POST":
        if FORMS_AVAILABLE and form and hasattr(form, "validate_on_submit") and form.validate_on_submit():
            form_data = {
                "full_name": (form.full_name.data or "").strip(),
                "email":     (form.email.data   or "").strip().lower(),
                "phone":     (form.phone.data   or "").strip(),
                "subject":   form.subject.data if form.subject else "",
                "message":   (form.message.data or "").strip(),
            }
        else:
            form_data = {
                "full_name": request.form.get("full_name", "").strip(),
                "email":     request.form.get("email",     "").strip().lower(),
                "phone":     request.form.get("phone",     "").strip(),
                "subject":   request.form.get("subject",   ""),
                "message":   request.form.get("message",   "").strip(),
            }

        if not form_data["full_name"] or not form_data["message"]:
            error = _('Veuillez remplir tous les champs obligatoires.')
        elif form_data["email"] and "@" not in form_data["email"]:
            error = _('Veuillez entrer une adresse email valide.')
        else:
            success = process_contact(form_data)
            if success:
                flash(_('Votre message a été envoyé avec succès !'), 'success')
                form_data = {}
                if FORMS_AVAILABLE:
                    form = ContactForm()
            else:
                error = _('Une erreur technique est survenue. Veuillez réessayer.')

    return render_template(
        "legal/contact.html",
        title=_("Contact"),
        badge=_("Formulaire de contact"),
        subtitle=_("Contactez-nous via notre formulaire"),
        form=form,
        form_data=form_data,
        success=success,
        error=error,
        current_time=current_time,
        app_name=AppConfig.NAME,  # AJOUTÉ
    )

# ===============================
# PAGES LÉGALES
# ===============================
@legal_bp.route("/legal")
def legal():
    return render_template(
        "legal/legal.html",
        title=_("Mentions Légales"),
        badge=_("Information légale"),
        subtitle=_("Informations légales"),
        app_name=AppConfig.NAME,  # AJOUTÉ
    )


@legal_bp.route("/privacy")
def privacy():
    return render_template(
        "legal/privacy.html",
        title=_("Politique de Confidentialité"),
        badge=_("Protection des données"),
        subtitle=_("Comment nous protégeons vos données"),
        app_name=AppConfig.NAME,  # AJOUTÉ
    )


@legal_bp.route("/terms")
def terms():
    return render_template(
        "legal/terms.html",
        title=_("Conditions d'Utilisation"),
        badge=_("Règles d'usage"),
        subtitle=_("Conditions d'utilisation du service"),
        app_name=AppConfig.NAME,  # AJOUTÉ - C'est la correction principale !
    )


@legal_bp.route("/about")
def about():
    return render_template(
        "legal/about.html",
        title=_("À Propos"),
        badge=_("Notre histoire"),
        subtitle=_("Découvrez PDF Fusion Pro"),
        app_name=AppConfig.NAME,  # AJOUTÉ
    )

# ===============================
# REDIRECTIONS SEO
# ===============================
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