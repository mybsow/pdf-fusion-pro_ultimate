"""
Routes pour les pages légales
Version production sécurisée - CORRIGÉE
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
import logging
from pathlib import Path

from . import legal_bp

# Imports absolus plutôt que relatifs
from config import AppConfig

# Imports avec gestion d'erreur
try:
    from managers.contact_manager import contact_manager
    CONTACT_MANAGER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Contact manager non disponible: {e}")
    CONTACT_MANAGER_AVAILABLE = False
    # Manager factice
    class DummyContactManager:
        def save_message(self, **kwargs):
            return True
    contact_manager = DummyContactManager()

# Flask-Babel
try:
    from flask_babel import _, lazy_gettext as _l
    BABEL_AVAILABLE = True
except ImportError:
    BABEL_AVAILABLE = False
    # Fonctions factices
    def _(s):
        return s
    def _l(s):
        return s

# Flask-WTF
try:
    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, SelectField
    from wtforms.validators import DataRequired, Optional, Email, Length
    FORMS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ Flask-WTF non disponible: {e}")
    FORMS_AVAILABLE = False
    # Classes factices
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


# ============================================================
# FORMULAIRE CONTACT
# ============================================================

if FORMS_AVAILABLE:
    class ContactForm(FlaskForm):
        """Formulaire de contact"""
        
        full_name = StringField(
            _l('Nom complet') if BABEL_AVAILABLE else 'Nom complet',
            validators=[DataRequired(), Length(min=2, max=100)]
        )
        
        email = StringField(
            _l('Email') if BABEL_AVAILABLE else 'Email',
            validators=[Optional(), Email()]
        )
        
        phone = StringField(
            _l('Téléphone (optionnel)') if BABEL_AVAILABLE else 'Téléphone (optionnel)',
            validators=[Optional()]
        )
        
        subject = SelectField(
            _l('Sujet') if BABEL_AVAILABLE else 'Sujet',
            choices=[
                ('bug', '🚨 ' + (_l('Signaler un bug') if BABEL_AVAILABLE else 'Signaler un bug')),
                ('improvement', '💡 ' + (_l('Proposer une amélioration') if BABEL_AVAILABLE else 'Amélioration')),
                ('partnership', '🤝 ' + (_l('Partenariat') if BABEL_AVAILABLE else 'Partenariat')),
                ('other', '❓ ' + (_l('Autre') if BABEL_AVAILABLE else 'Autre')),
            ],
            validators=[DataRequired()]
        )
        
        message = TextAreaField(
            _l('Message') if BABEL_AVAILABLE else 'Message',
            validators=[DataRequired(), Length(max=2000)]
        )
else:
    # Fallback si Flask-WTF n'est pas disponible
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
                {"name": "Téléphone", "value": form_data.get("phone", "Non renseigné"), "inline": True},
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
        current_app.logger.info("✅ Notification Discord envoyée")
        
    except Exception as e:
        current_app.logger.warning(f"⚠️ Webhook Discord échoué: {e}")


# ============================================================
# ROUTE CONTACT
# ============================================================

@legal_bp.route("/contact", methods=["GET", "POST"])
def contact():
    # Initialiser le formulaire
    form = ContactForm() if FORMS_AVAILABLE else ContactForm()
    success = False
    error = None
    form_data = {}
    
    if request.method == "POST":
        if FORMS_AVAILABLE and hasattr(form, 'validate_on_submit') and form.validate_on_submit():
            # Traitement normal avec formulaire WTForms
            email_value = (form.email.data or "").strip().lower() if form.email else ""
            
            form_data = {
                "full_name": form.full_name.data.strip() if form.full_name else "",
                "email": email_value,
                "phone": (form.phone.data or "").strip() if form.phone else "",
                "subject": form.subject.data if form.subject else "",
                "message": form.message.data.strip() if form.message else "",
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
                    flash(_('Votre message a été envoyé avec succès !') if BABEL_AVAILABLE else 'Message envoyé !', 'success')
                    # Réinitialiser le formulaire
                    form = ContactForm()
                    form_data = {}
                else:
                    error = _('Une erreur technique est survenue. Veuillez réessayer.') if BABEL_AVAILABLE else 'Erreur technique'
                    
            except Exception as e:
                current_app.logger.exception(f"❌ Erreur sauvegarde: {e}")
                error = _('Une erreur technique est survenue. Veuillez réessayer.') if BABEL_AVAILABLE else 'Erreur technique'
        
        else:
            # Fallback: traitement manuel des données POST
            form_data = {
                "full_name": request.form.get("full_name", "").strip(),
                "email": request.form.get("email", "").strip().lower(),
                "phone": request.form.get("phone", "").strip(),
                "subject": request.form.get("subject", ""),
                "message": request.form.get("message", "").strip(),
            }
            
            # Validation simple
            if form_data["full_name"] and form_data["message"]:
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
                        flash('Message envoyé avec succès !', 'success')
                        form_data = {}
                    else:
                        error = 'Erreur technique'
                        
                except Exception as e:
                    current_app.logger.exception(f"❌ Erreur fallback: {e}")
                    error = 'Erreur technique'
            else:
                error = 'Veuillez remplir tous les champs obligatoires.'
    
    return render_template(
        "legal/contact.html",
        title=_("Contact") if BABEL_AVAILABLE else "Contact",
        badge=_("Formulaire de contact") if BABEL_AVAILABLE else "Formulaire de contact",
        subtitle=_("Contactez-nous via notre formulaire") if BABEL_AVAILABLE else "Contactez-nous",
        form=form,
        form_data=form_data,
        success=success,
        error=error,
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime,
        current_lang=session.get('language', 'fr')  # Ajoutez ceci
    )


# ============================================================
# AUTRES PAGES LÉGALES
# ============================================================

@legal_bp.route("/legal")
def legal():
    return render_template(
        "legal/legal.html",
        title=_("Mentions Légales") if BABEL_AVAILABLE else "Mentions Légales",
        badge=_("Information légale") if BABEL_AVAILABLE else "Information légale",
        subtitle=_("Informations légales") if BABEL_AVAILABLE else "Informations légales",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime,
        current_lang=session.get('language', 'fr')  # Ajoutez ceci
    )


@legal_bp.route("/privacy")
def privacy():
    return render_template(
        "legal/privacy.html",
        title=_("Politique de Confidentialité") if BABEL_AVAILABLE else "Politique de Confidentialité",
        badge=_("Protection des données") if BABEL_AVAILABLE else "Protection des données",
        subtitle=_("Comment nous protégeons vos données") if BABEL_AVAILABLE else "Protection des données",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime,
        current_lang=session.get('language', 'fr')  # Ajoutez ceci
    )


@legal_bp.route("/terms")
def terms():
    return render_template(
        "legal/terms.html",
        title=_("Conditions d'Utilisation") if BABEL_AVAILABLE else "Conditions d'Utilisation",
        badge=_("Règles d'usage") if BABEL_AVAILABLE else "Règles d'usage",
        subtitle=_("Conditions d'utilisation du service") if BABEL_AVAILABLE else "Conditions d'utilisation",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime,
        current_lang=session.get('language', 'fr')  # Ajoutez ceci
    )


@legal_bp.route("/about")
def about():
    return render_template(
        "legal/about.html",
        title=_("À Propos") if BABEL_AVAILABLE else "À Propos",
        badge=_("Notre histoire") if BABEL_AVAILABLE else "Notre histoire",
        subtitle=_("Découvrez PDF Fusion Pro") if BABEL_AVAILABLE else "À propos de nous",
        current_year=datetime.now().year,
        config=AppConfig,
        datetime=datetime,
        current_lang=session.get('language', 'fr')  # Ajoutez ceci
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
