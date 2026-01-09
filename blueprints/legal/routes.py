"""
Routes pour les pages légales
"""

from flask import render_template_string, request, jsonify, flash, redirect, url_for
from datetime import datetime
from . import legal_bp
from config import AppConfig
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import requests
from pathlib import Path

# ============================================================
# TEMPLATE HTML POUR LES PAGES LÉGALES
# ============================================================

LEGAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | {{ config.NAME }}</title>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #4361ee;
            --secondary-color: #3a0ca3;
            --accent-color: #4cc9f0;
            --light-color: #f8f9fa;
            --dark-color: #212529;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
        }
        
        [data-bs-theme="dark"] {
            --light-color: #1a1d20;
            --dark-color: #f8f9fa;
            --gray-color: #adb5bd;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            color: var(--dark-color);
        }
        
        [data-bs-theme="dark"] body {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        }
        
        .legal-container {
            max-width: 1000px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            margin: 2rem auto;
        }
        
        [data-bs-theme="dark"] .legal-container {
            background: var(--light-color);
        }
        
        .legal-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2.5rem;
        }
        
        .legal-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1.5rem;
            border-radius: 50px;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        .legal-content {
            padding: 2.5rem;
            line-height: 1.8;
        }
        
        .legal-content h2 {
            color: var(--secondary-color);
            font-weight: 700;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--light-color);
            font-size: 1.8rem;
        }
        
        .legal-content h3 {
            color: var(--primary-color);
            font-weight: 600;
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-size: 1.4rem;
        }
        
        .legal-footer {
            background: var(--light-color);
            padding: 1.5rem 2.5rem;
            border-top: 1px solid rgba(0, 0, 0, 0.05);
            font-size: 0.9rem;
        }
        
        [data-bs-theme="dark"] .legal-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .nav-links a {
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            margin: 0 0.75rem;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: white;
        }
        
        .info-box {
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
            border-left: 4px solid var(--primary-color);
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
        }
        
        [data-bs-theme="dark"] .info-box {
            background: linear-gradient(135deg, #2d3748, #4a5568);
        }
        
        .contact-info {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin: 1.5rem 0;
        }
        
        .contact-icon {
            width: 50px;
            height: 50px;
            background: var(--primary-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.25rem;
        }
        
        /* Styles spécifiques au formulaire de contact */
        .contact-form-container {
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            margin: 2rem 0;
        }
        
        [data-bs-theme="dark"] .contact-form-container {
            background: #2d2d44;
        }
        
        .form-label {
            font-weight: 600;
            color: var(--dark-color);
            margin-bottom: 0.5rem;
            font-size: 0.95rem;
        }
        
        [data-bs-theme="dark"] .form-label {
            color: var(--light-color);
        }
        
        .form-control, .form-select {
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        [data-bs-theme="dark"] .form-control,
        [data-bs-theme="dark"] .form-select {
            background: #3a3a52;
            border-color: #4a4a6a;
            color: var(--light-color);
        }
        
        .form-control:focus, .form-select:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.25);
        }
        
        .form-text {
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 0.25rem;
        }
        
        .btn-send {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 10px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-send:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
        }
        
        .alert-success {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            border-color: var(--success-color);
            color: #155724;
        }
        
        .alert-danger {
            background: linear-gradient(135deg, #f8d7da, #f5c6cb);
            border-color: var(--danger-color);
            color: #721c24;
        }
        
        .character-count {
            font-size: 0.8rem;
            color: #6c757d;
            text-align: right;
            margin-top: 0.25rem;
        }
        
        .character-count.warning {
            color: var(--warning-color);
        }
        
        .character-count.danger {
            color: var(--danger-color);
        }
        
        .contact-types-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .contact-type-card {
            background: var(--light-color);
            border-radius: 10px;
            padding: 1.5rem;
            border-left: 4px solid var(--primary-color);
            transition: transform 0.3s ease;
        }
        
        .contact-type-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .contact-type-icon {
            font-size: 1.5rem;
            color: var(--primary-color);
            margin-bottom: 1rem;
        }
        
        @media (max-width: 768px) {
            .legal-container {
                margin: 1rem;
                border-radius: 15px;
            }
            
            .legal-header, .legal-content {
                padding: 1.5rem;
            }
            
            .contact-types-grid {
                grid-template-columns: 1fr;
            }
            
            .contact-form-container {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="legal-container">
        <div class="legal-header">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <a href="/" class="text-white text-decoration-none">
                    <i class="fas fa-file-pdf fa-lg me-2"></i>
                    <span class="fw-bold">{{ config.NAME }}</span>
                </a>
                <div class="nav-links d-none d-md-block">
                    <a href="/"><i class="fas fa-home me-1"></i> Accueil</a>
                    <a href="/mentions-legales">Mentions</a>
                    <a href="/politique-confidentialite">Confidentialité</a>
                    <a href="/conditions-utilisation">Conditions</a>
                    <a href="/contact">Contact</a>
                </div>
            </div>
            <div class="legal-badge">{{ badge }}</div>
            <h1 class="display-6 fw-bold">{{ title }}</h1>
            <p class="opacity-90">{{ subtitle }}</p>
        </div>
        
        <div class="legal-content">
            {{ content|safe }}
        </div>
 
        <div class="legal-footer">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <p class="mb-0">
                        <i class="fas fa-copyright me-1"></i> {{ current_year }} {{ config.NAME }} 
                        • Développé par <strong>{{ config.DEVELOPER_NAME }}</strong> 
                        • Version {{ config.VERSION }}
                    </p>
                    <p class="mb-0 text-muted small mt-1">
                        <i class="fas fa-envelope me-1"></i> 
                        <a href="/contact" class="text-muted text-decoration-none">
                            Contactez-nous via notre formulaire
                        </a>
                        • Hébergé sur <strong>{{ config.HOSTING }}</strong> • {{ config.DOMAIN }}
                    </p>
                </div>
                <div class="col-md-4 text-md-end mt-2 mt-md-0">
                    <a href="/" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-arrow-left me-1"></i> Retour à l'accueil
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Thème sombre/clair automatique
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        }
        
        // Gestion du compteur de caractères
        document.addEventListener('DOMContentLoaded', function() {
            const messageTextarea = document.getElementById('message');
            const charCount = document.getElementById('charCount');
            
            if (messageTextarea && charCount) {
                function updateCharCount() {
                    const length = messageTextarea.value.length;
                    charCount.textContent = `${length} / 2000 caractères`;
                    
                    charCount.classList.remove('warning', 'danger');
                    if (length > 1500) {
                        charCount.classList.add('warning');
                    }
                    if (length > 1900) {
                        charCount.classList.add('danger');
                    }
                }
                
                messageTextarea.addEventListener('input', updateCharCount);
                updateCharCount(); // Initial call
            }
        });
    </script>
</body>
</html>
"""

# ============================================================
# FONCTIONS D'ENVOI FIABLES
# ============================================================

def save_contact_to_json(form_data, flask_request):
    """
    Sauvegarde le contact dans un fichier JSON (solution fiable)
    Retourne toujours True sauf en cas d'erreur critique
    """
    try:
        # Créer le dossier data/contacts si nécessaire
        contacts_dir = Path("data/contacts")
        contacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer un nom de fichier unique et sécurisé
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Nettoyer l'email pour le nom de fichier
        safe_email = form_data['email'].split('@')[0][:20].replace('.', '_').replace('+', '_')
        filename = f"contact_{timestamp}_{safe_email}.json"
        filepath = contacts_dir / filename
        
        # Préparer les données avec métadonnées
        contact_data = {
            **form_data,
            "received_at": datetime.now().isoformat(),
            "timestamp": timestamp,
            "ip_address": flask_request.remote_addr if hasattr(flask_request, 'remote_addr') else None,
            "user_agent": flask_request.user_agent.string if hasattr(flask_request, 'user_agent') else None,
            "status": "pending",
            "app_name": AppConfig.NAME,
            "domain": AppConfig.DOMAIN
        }
        
        # Sauvegarder en JSON avec encoding UTF-8
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(contact_data, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Contact sauvegardé dans: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur critique sauvegarde JSON: {e}")
        return False


def send_discord_notification(form_data):
    """
    Envoie une notification Discord (optionnel)
    Ne bloque jamais le processus principal
    """
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        # Pas de webhook configuré = on ignore silencieusement
        return True
    
    try:
        # Mapper les sujets pour l'affichage
        subject_display_map = {
            'bug': '🚨 Bug/Problème technique',
            'improvement': '💡 Amélioration/Suggestion',
            'partnership': '🤝 Partenariat',
            'other': '❓ Autre demande'
        }
        
        subject_display = subject_display_map.get(
            form_data['subject'], 
            form_data['subject'].capitalize()
        )
        
        # Tronquer le message si trop long pour Discord
        message_preview = form_data['message']
        if len(message_preview) > 1000:
            message_preview = message_preview[:997] + "..."
        
        # Créer l'embed Discord
        embed = {
            "title": "📧 Nouveau message de contact",
            "color": 0x4361ee,  # Couleur bleue
            "fields": [
                {
                    "name": "👤 Nom complet",
                    "value": f"{form_data['first_name']} {form_data['last_name']}",
                    "inline": True
                },
                {
                    "name": "📧 Email",
                    "value": form_data['email'],
                    "inline": True
                },
                {
                    "name": "📱 Téléphone",
                    "value": form_data.get('phone', 'Non renseigné'),
                    "inline": True
                },
                {
                    "name": "🎯 Type de demande",
                    "value": subject_display,
                    "inline": False
                },
                {
                    "name": "💬 Message",
                    "value": message_preview,
                    "inline": False
                }
            ],
            "footer": {
                "text": f"{AppConfig.NAME} • {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            }
        }
        
        # Envoyer avec un timeout très court
        response = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=3  # Timeout court pour ne pas bloquer
        )
        
        if response.status_code in [200, 204]:
            print("🔔 Notification Discord envoyée")
            return True
        else:
            print(f"⚠️ Discord a répondu avec code: {response.status_code}")
            return True  # On continue même si Discord échoue
            
    except requests.exceptions.Timeout:
        print("⚠️ Timeout Discord (ignoré)")
        return True
    except Exception as e:
        print(f"⚠️ Erreur Discord (ignorée): {str(e)[:100]}")
        return True  # Ne JAMAIS bloquer le formulaire


def send_email_fallback(form_data):
    """
    Envoie un email - DÉSACTIVÉ TEMPORAIREMENT pour éviter les timeouts
    Les messages sont sauvegardés en JSON, l'email sera implémenté plus tard
    """
    print("📨 Email désactivé temporairement (éviter timeout Render)")
    print("   Les messages sont sauvegardés dans data/contacts/")
    print(f"   Message de: {form_data.get('email', 'N/A')}")
    
    # DEBUG: Afficher la configuration (sans essayer d'envoyer)
    smtp_configured = all([
        os.environ.get('SMTP_USERNAME'),
        os.environ.get('SMTP_PASSWORD'),
        os.environ.get('DEVELOPER_EMAIL')
    ])
    
    if smtp_configured:
        print("   ⚠️ SMTP est configuré mais désactivé pour stabilité")
        print(f"   📧 Destinataire: {os.environ.get('DEVELOPER_EMAIL')}")
        print(f"   🔑 Utilisateur SMTP: {os.environ.get('SMTP_USERNAME')[:10]}...")
    else:
        print("   ⚠️ SMTP non configuré dans les variables d'environnement")
        print("   ℹ️ Pour configurer SMTP, ajoutez dans Render:")
        print("      SMTP_USERNAME, SMTP_PASSWORD, DEVELOPER_EMAIL")
    
    # Toujours retourner True pour ne pas bloquer le formulaire
    return True


# ============================================================
# ROUTES
# ============================================================

@legal_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Page de contact avec formulaire fiable"""
    
    success = False
    error = None
    
    if request.method == 'POST':
        # Récupération et nettoyage des données
        form_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'phone': request.form.get('phone', '').strip(),
            'subject': request.form.get('subject', '').strip(),
            'message': request.form.get('message', '').strip()
        }
        
        # Validation robuste
        if not all([form_data['first_name'], form_data['last_name'], form_data['email'], form_data['subject'], form_data['message']]):
            error = "Veuillez remplir tous les champs obligatoires (*)."
        elif len(form_data['message']) > 2000:
            error = "Le message ne doit pas dépasser 2000 caractères."
        elif '@' not in form_data['email'] or '.' not in form_data['email'][form_data['email'].find('@'):]:
            error = "Veuillez saisir une adresse email valide."
        elif len(form_data['first_name']) < 2 or len(form_data['last_name']) < 2:
            error = "Le nom et prénom doivent contenir au moins 2 caractères."
        else:
            # ============================================
            # NOUVELLE LOGIQUE D'ENVOI FIABLE
            # ============================================
            
            # 1. Sauvegarde en JSON (GARANTIE de fonctionnement)
            json_saved = save_contact_to_json(form_data, request)
            
            # 2. Notification Discord (optionnel, non-bloquant)
            discord_sent = send_discord_notification(form_data)
            
            # 3. Email SMTP (DÉSACTIVÉ temporairement)
            print("📧 Tentative d'envoi d'email...")
            email_sent = send_email_fallback(form_data)  # Retourne toujours True maintenant
            
            # 4. Déterminer le succès
            if json_saved:
                success = True
                current_time = datetime.now().strftime('%H:%M')
                email_status = "📨 (sauvegardé uniquement - email désactivé)"
                print(f"✅ Formulaire traité avec succès à {current_time} pour: {form_data['email']} {email_status}")
                
                # Si SMTP est configuré, on pourrait l'activer plus tard
                smtp_configured = all([
                    os.environ.get('SMTP_USERNAME'),
                    os.environ.get('SMTP_PASSWORD'),
                    os.environ.get('DEVELOPER_EMAIL')
                ])
                if smtp_configured:
                    print(f"   ℹ️ SMTP configuré pour: {os.environ.get('DEVELOPER_EMAIL')}")
            else:
                error = "Une erreur technique est survenue lors de la sauvegarde. Veuillez réessayer."
    
    # Contenu HTML du formulaire
    contact_form = """
    <div class="info-box">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Formulaire de contact :</strong> Utilisez ce formulaire pour nous contacter directement.
        Nous vous répondrons dans les meilleurs délais.
    </div>
    
    <h2>Formulaire de Contact</h2>
    <p>Remplissez ce formulaire pour nous contacter. Tous les champs marqués d'un astérisque (*) sont obligatoires.</p>
    
    """
    
    # Message de succès ou d'erreur
    if success:
        current_time = datetime.now().strftime('%H:%M')
        contact_form += f"""
        <div class="alert alert-success" role="alert">
            <i class="fas fa-check-circle me-2"></i>
            <strong>Message enregistré avec succès !</strong><br>
            <small>Référence: {current_time} • Merci pour votre message.</small><br>
            Nous avons bien reçu votre demande et nous vous répondrons dans les plus brefs délais.
        </div>
        
        <div class="text-center mt-4">
            <a href="/" class="btn btn-primary me-2">
                <i class="fas fa-home me-1"></i> Retour à l'accueil
            </a>
            <a href="/contact" class="btn btn-outline-primary">
                <i class="fas fa-envelope me-1"></i> Envoyer un autre message
            </a>
        </div>
        """
        
        # Ne pas afficher le formulaire après succès
        contact_form += """
        </div></div>"""
        
        return render_template_string(
            LEGAL_TEMPLATE,
            title="Contact - Message envoyé",
            badge="Succès",
            subtitle="Votre message a été enregistré avec succès",
            content=contact_form,
            current_year=datetime.now().year,
            config=AppConfig
        )
    
    elif error:
        contact_form += f"""
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-circle me-2"></i>
            <strong>Attention :</strong> {error}
        </div>
        """
    
    # Le formulaire lui-même (uniquement si pas de succès)
    contact_form += f"""
    <div class="contact-form-container">
        <form method="POST" action="/contact">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="first_name" class="form-label">Prénom *</label>
                    <input type="text" class="form-control" id="first_name" name="first_name" 
                           placeholder="Votre prénom" required
                           value="{request.form.get('first_name', '')}"
                           minlength="2" maxlength="50">
                </div>
                
                <div class="col-md-6 mb-3">
                    <label for="last_name" class="form-label">Nom *</label>
                    <input type="text" class="form-control" id="last_name" name="last_name" 
                           placeholder="Votre nom" required
                           value="{request.form.get('last_name', '')}"
                           minlength="2" maxlength="50">
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label for="email" class="form-label">Adresse email *</label>
                    <input type="email" class="form-control" id="email" name="email" 
                           placeholder="votre@email.com" required
                           value="{request.form.get('email', '')}">
                    <div class="form-text">Nous ne partagerons jamais votre email avec des tiers.</div>
                </div>
                
                <div class="col-md-6 mb-3">
                    <label for="phone" class="form-label">Numéro de téléphone (optionnel)</label>
                    <input type="tel" class="form-control" id="phone" name="phone" 
                           placeholder="06 12 34 56 78"
                           value="{request.form.get('phone', '')}">
                    <div class="form-text">Pour un contact plus rapide si nécessaire.</div>
                </div>
            </div>
            
            <div class="mb-3">
                <label for="subject" class="form-label">Sujet de votre message *</label>
                <select class="form-select" id="subject" name="subject" required>
                    <option value="" disabled selected>Sélectionnez un sujet</option>
                    <option value="bug" {"selected" if request.form.get('subject') == 'bug' else ""}>🚨 Signaler un bug ou un problème technique</option>
                    <option value="improvement" {"selected" if request.form.get('subject') == 'improvement' else ""}>💡 Proposer une amélioration fonctionnelle</option>
                    <option value="partnership" {"selected" if request.form.get('subject') == 'partnership' else ""}>🤝 Demande de partenariat</option>
                    <option value="other" {"selected" if request.form.get('subject') == 'other' else ""}>❓ Autre demande</option>
                </select>
            </div>
            
            <div class="mb-3">
                <label for="message" class="form-label">Votre message *</label>
                <textarea class="form-control" id="message" name="message" rows="6" 
                          placeholder="Décrivez votre demande en détail..." required
                          maxlength="2000">{request.form.get('message', '')}</textarea>
                <div class="character-count" id="charCount">0 / 2000 caractères</div>
                <div class="form-text">Maximum 2000 caractères. Soyez aussi précis que possible.</div>
            </div>
            
            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <button type="submit" class="btn btn-send">
                    <i class="fas fa-paper-plane me-1"></i> Envoyer le message
                </button>
            </div>
        </form>
    </div>
    
    <h3 class="mt-5">Types de demandes</h3>
    <p>Voici les différents types de demandes que vous pouvez nous soumettre :</p>
    
    <div class="contact-types-grid">
        <div class="contact-type-card">
            <div class="contact-type-icon">
                <i class="fas fa-bug"></i>
            </div>
            <h4>Support technique</h4>
            <p>Pour signaler un bug, un problème technique ou une difficulté d'utilisation du service.</p>
        </div>
        
        <div class="contact-type-card">
            <div class="contact-type-icon">
                <i class="fas fa-lightbulb"></i>
            </div>
            <h4>Améliorations</h4>
            <p>Pour proposer une nouvelle fonctionnalité ou suggérer une amélioration du service.</p>
        </div>
        
        <div class="contact-type-card">
            <div class="contact-type-icon">
                <i class="fas fa-handshake"></i>
            </div>
            <h4>Partenariats</h4>
            <p>Pour discuter d'opportunités de collaboration, d'intégration ou de partenariat.</p>
        </div>
        
        <div class="contact-type-card">
            <div class="contact-type-icon">
                <i class="fas fa-question-circle"></i>
            </div>
            <h4>Autres demandes</h4>
            <p>Pour toute autre question concernant le service, la confidentialité ou les conditions d'utilisation.</p>
        </div>
    </div>
    
    <div class="info-box mt-4">
        <i class="fas fa-clock me-2"></i>
        <strong>Temps de réponse :</strong> Nous nous efforçons de répondre à tous les messages dans un délai de 48 heures.
        Pour les urgences techniques, précisez-le dans votre message.
    </div>
    
    <div class="alert alert-warning mt-4">
        <i class="fas fa-exclamation-circle me-2"></i>
        <strong>Note importante :</strong> Pour des raisons de sécurité et de confidentialité, 
        nous ne traitons pas les demandes concernant des fichiers PDF spécifiques via ce formulaire.
        Tous les traitements de fichiers doivent être effectués directement via l'interface web.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Contact",
        badge="Formulaire de contact",
        subtitle="Contactez-nous via notre formulaire",
        content=contact_form,
        current_year=datetime.now().year,
        config=AppConfig
    )


# ============================================================
# ADMIN - INTERFACE WEB POUR VOIR LES MESSAGES
# ============================================================

@legal_bp.route('/admin/messages', methods=['GET'])
def admin_messages():
    """Interface web pour voir les messages de contact"""
    import json
    from pathlib import Path
    
    # Protection basique par mot de passe
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    
    # Si pas de mot de passe configuré, on utilise un mot de passe par défaut (à changer)
    if not admin_password:
        admin_password = 'admin123'  # ⚠️ CHANGEZ CE MOT DE PASSE !
    
    # Vérifier l'authentification
    if request.args.get('password') != admin_password:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Accès Admin - PDF Fusion Pro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                body {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                .login-box {
                    background: white;
                    border-radius: 20px;
                    padding: 2.5rem;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 400px;
                }
                .app-icon {
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #4361ee, #3a0ca3);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 2rem;
                    margin: 0 auto 1.5rem;
                }
                .alert-warning {
                    background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                    border-color: #ffc107;
                }
            </style>
        </head>
        <body>
            <div class="login-box">
                <div class="app-icon">
                    <i class="fas fa-lock"></i>
                </div>
                
                <h2 class="text-center mb-4">Accès Administrateur</h2>
                <p class="text-center text-muted mb-4">
                    <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro
                </p>
                
                <form method="GET" action="/admin/messages">
                    <div class="mb-3">
                        <label for="password" class="form-label">Mot de passe admin</label>
                        <div class="input-group">
                            <span class="input-group-text">
                                <i class="fas fa-key"></i>
                            </span>
                            <input type="password" class="form-control" id="password" name="password" 
                                   placeholder="Entrez le mot de passe" required autofocus>
                        </div>
                        <div class="form-text">
                            <i class="fas fa-info-circle me-1"></i>
                            Accès réservé à l'administrateur
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-sign-in-alt me-1"></i> Se connecter
                    </button>
                </form>
                
                <div class="alert alert-warning mt-4">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    <strong>Accès restreint :</strong> Cette page est réservée à l'administrateur de l'application.
                </div>
            </div>
        </body>
        </html>
        """
    
    # Lire tous les messages
    contacts_dir = Path("data/contacts")
    messages = []
    
    if contacts_dir.exists():
        for file_path in contacts_dir.glob("contact_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    message_data = json.load(f)
                message_data["filename"] = file_path.name
                messages.append(message_data)
            except Exception as e:
                print(f"Erreur lecture {file_path}: {e}")
    
    # Trier par date (plus récent d'abord)
    messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Générer l'HTML
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Messages - PDF Fusion Pro</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                background: #f8f9fa;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .header {
                background: linear-gradient(135deg, #4361ee, #3a0ca3);
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            .message-card {
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
                border-left: 4px solid #4361ee;
            }
            .badge-new {
                background: linear-gradient(135deg, #2ecc71, #27ae60);
                color: white;
            }
            .badge-read {
                background: #6c757d;
                color: white;
            }
            .message-subject {
                font-weight: 600;
                color: #4361ee;
            }
            .message-meta {
                font-size: 0.85rem;
                color: #6c757d;
            }
            .no-messages {
                text-align: center;
                padding: 3rem;
                color: #6c757d;
                background: white;
                border-radius: 10px;
            }
            .status-badge {
                font-size: 0.8rem;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h1><i class="fas fa-envelope-open-text me-2"></i> Messages de contact</h1>
                        <p class="mb-0 opacity-75">
                            <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro • Interface d'administration
                        </p>
                    </div>
                    <div>
                        <a href="/contact" class="btn btn-light me-2">
                            <i class="fas fa-envelope me-1"></i> Formulaire
                        </a>
                        <a href="/" class="btn btn-outline-light">
                            <i class="fas fa-home me-1"></i> Accueil
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <span class="badge bg-primary">Total: {total_messages}</span>
                    <span class="badge bg-success ms-2">Non lus: {unread_count}</span>
                </div>
                <div>
                    <span class="text-muted">
                        <i class="fas fa-sync-alt me-1"></i> Dernière mise à jour: {current_time}
                    </span>
                </div>
            </div>
    """
    
    if not messages:
        html += """
        <div class="no-messages">
            <i class="fas fa-inbox fa-3x mb-3" style="color: #dee2e6;"></i>
            <h3>Aucun message pour le moment</h3>
            <p class="text-muted">Les messages de contact apparaîtront ici lorsqu'ils seront envoyés via le formulaire.</p>
        </div>
        """
    else:
        for msg in messages:
            # Déterminer le statut et les couleurs
            status = msg.get("status", "pending")
            status_badge_class = "badge-new" if status == "pending" else "badge-read"
            status_text = "Nouveau" if status == "pending" else "Lu"
            
            # Formater la date
            received_at = msg.get("received_at", "")
            if received_at:
                try:
                    dt = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
                    date_str = dt.strftime('%d/%m/%Y à %H:%M')
                except:
                    date_str = received_at
            else:
                date_str = "Date inconnue"
            
            # Tronquer le message pour l'aperçu
            message_preview = msg.get("message", "")[:150]
            if len(msg.get("message", "")) > 150:
                message_preview += "..."
            
            html += f"""
            <div class="message-card">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h5 class="message-subject mb-1">
                            <i class="fas fa-user-circle me-1"></i>
                            {msg.get('first_name', 'N/A')} {msg.get('last_name', 'N/A')}
                        </h5>
                        <p class="message-meta mb-0">
                            <i class="fas fa-envelope me-1"></i> {msg.get('email', 'N/A')}
                            <span class="ms-3"><i class="fas fa-phone me-1"></i> {msg.get('phone', 'Non renseigné')}</span>
                        </p>
                    </div>
                    <div class="text-end">
                        <span class="badge {status_badge_class} status-badge">{status_text}</span>
                        <div class="message-meta mt-1">{date_str}</div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <span class="badge bg-info">{msg.get('subject', 'Non spécifié')}</span>
                </div>
                
                <div class="mb-3">
                    <p class="mb-1"><strong>Message :</strong></p>
                    <div style="
                        background: #f8f9fa; 
                        padding: 1rem; 
                        border-radius: 5px; 
                        border-left: 3px solid #4361ee;
                        max-height: 200px;
                        overflow-y: auto;
                    ">
                        {msg.get('message', 'Aucun message')}
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mt-3">
                    <div class="message-meta">
                        <small>
                            <i class="fas fa-file me-1"></i> {msg.get('filename', 'N/A')}
                            <span class="ms-3"><i class="fas fa-globe me-1"></i> {msg.get('ip_address', 'N/A')}</span>
                        </small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-outline-primary" onclick="markAsRead('{msg.get('filename')}')">
                            <i class="fas fa-check me-1"></i> Marquer comme lu
                        </button>
                    </div>
                </div>
            </div>
            """
    
    html += """
        </div>
        
        <script>
            function markAsRead(filename) {
                if (confirm('Marquer ce message comme lu ?')) {
                    // Ici vous pourriez ajouter une requête AJAX pour mettre à jour le statut
                    alert('Fonctionnalité à implémenter : Marquer comme lu pour ' + filename);
                    // Pour l'instant, recharger la page
                    location.reload();
                }
            }
            
            // Rafraîchir automatiquement toutes les 30 secondes
            setTimeout(function() {
                location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    """
    
    current_time = datetime.now().strftime('%H:%M:%S')
    unread_count = sum(1 for msg in messages if msg.get("status") == "pending")
    
    return html.format(
        total_messages=len(messages),
        unread_count=unread_count,
        current_time=current_time
    )


# ============================================================
# PAGES LÉGALES FIXES
# ============================================================

@legal_bp.route('/mentions-legales')
def legal_notice():
    """Page des mentions légales"""
    
    content = """
    <h2>Mentions Légales</h2>
    
    <div class="info-box">
        <i class="fas fa-balance-scale me-2"></i>
        <strong>Conformité RGPD et CNIL :</strong> Cette application respecte scrupuleusement 
        le Règlement Général sur la Protection des Données (RGPD) et les directives 
        de la Commission Nationale de l'Informatique et des Libertés (CNIL).
    </div>
    
    <h3>Éditeur de l'application</h3>
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-building"></i>
        </div>
        <div>
            <p><strong>{{ config.NAME }}</strong><br>
            Application web hébergée sur {{ config.HOSTING }}<br>
            <i class="fas fa-globe me-1"></i> {{ config.DOMAIN }}</p>
        </div>
    </div>
    
    <h3>Directeur de la publication</h3>
    <p><strong>{{ config.DEVELOPER_NAME }}</strong><br>
    Développeur et responsable technique de l'application</p>
    
    <h3>Hébergement</h3>
    <p><strong>{{ config.HOSTING }}</strong><br>
    Hébergement infogéré avec haute disponibilité</p>
    
    <h3>Propriété intellectuelle</h3>
    <p>L'ensemble des éléments constituant le site (textes, graphismes, logiciels, etc.) 
    est la propriété exclusive de {{ config.NAME }} ou de ses partenaires. 
    Toute reproduction, représentation, modification, publication, transmission, 
    dénaturation, totale ou partielle du site ou de son contenu, par quelque procédé que ce soit, 
    et sur quelque support que ce soit, est interdite sans autorisation préalable.</p>
    
    <h3>Protection des données personnelles</h3>
    <p>Conformément à la loi "Informatique et Libertés" du 6 janvier 1978 modifiée 
    et au Règlement Général sur la Protection des Données (RGPD), vous disposez 
    d'un droit d'accès, de rectification, de suppression et d'opposition aux données vous concernant.</p>
    
    <p>Pour exercer ces droits ou pour toute question sur le traitement de vos données, 
    vous pouvez nous contacter via notre formulaire de contact.</p>
    
    <h3>Responsabilité</h3>
    <p>{{ config.NAME }} s'efforce d'assurer au mieux de ses possibilités l'exactitude 
    et la mise à jour des informations diffusées sur son application. Cependant, 
    nous ne pouvons garantir l'exactitude, la précision ou l'exhaustivité 
    des informations mises à disposition sur cette application.</p>
    
    <h3>Cookies</h3>
    <p>Notre application utilise des cookies strictement nécessaires au fonctionnement 
    de l'application (session utilisateur, préférences). Aucun cookie de tracking 
    ou publicitaire n'est utilisé.</p>
    
    <div class="alert alert-warning mt-4">
        <i class="fas fa-exclamation-circle me-2"></i>
        <strong>Important :</strong> Ces mentions légales peuvent être modifiées à tout moment 
        sans préavis. Nous vous invitons à les consulter régulièrement.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Mentions Légales",
        badge="Informations légales",
        subtitle="Conformité RGPD et mentions légales",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )


@legal_bp.route('/politique-confidentialite')
def privacy_policy():
    """Politique de confidentialité"""
    
    content = """
    <h2>Politique de Confidentialité</h2>
    
    <div class="info-box">
        <i class="fas fa-shield-alt me-2"></i>
        <strong>Engagement de confidentialité :</strong> Nous nous engageons à protéger 
        vos données personnelles et votre vie privée. Cette politique explique comment 
        nous collectons, utilisons et protégeons vos informations.
    </div>
    
    <h3>Collecte des données</h3>
    <p>Nous collectons uniquement les données strictement nécessaires au bon fonctionnement 
    de l'application :</p>
    <ul>
        <li><strong>Données de session :</strong> Informations techniques nécessaires 
        au traitement des fichiers PDF (identifiants de session temporaires)</li>
        <li><strong>Données de contact :</strong> Lorsque vous utilisez notre formulaire 
        de contact (nom, email, message)</li>
        <li><strong>Fichiers PDF :</strong> Les fichiers que vous uploadez sont traités 
        uniquement en mémoire et ne sont jamais stockés sur nos serveurs</li>
    </ul>
    
    <h3>Utilisation des données</h3>
    <p>Vos données sont utilisées exclusivement pour :</p>
    <ul>
        <li>Fournir le service de fusion de PDFs</li>
        <li>Répondre à vos demandes via le formulaire de contact</li>
        <li>Améliorer le service et résoudre les problèmes techniques</li>
    </ul>
    
    <h3>Protection des données</h3>
    <p>Nous mettons en œuvre des mesures techniques et organisationnelles appropriées 
    pour protéger vos données contre tout accès non autorisé, modification, 
    divulgation ou destruction :</p>
    <ul>
        <li>Chiffrement HTTPS pour toutes les communications</li>
        <li>Traitement des fichiers uniquement en mémoire (pas de stockage persistant)</li>
        <li>Suppression automatique des fichiers après traitement</li>
        <li>Sécurité des serveurs et surveillance continue</li>
    </ul>
    
    <h3>Durée de conservation</h3>
    <p><strong>Fichiers PDF :</strong> Supprimés immédiatement après le traitement<br>
    <strong>Données de session :</strong> Supprimées à la fermeture du navigateur<br>
    <strong>Messages de contact :</strong> Conservés 12 mois maximum</p>
    
    <h3>Partage des données</h3>
    <p>Nous ne vendons, n'échangeons ni ne transférons vos données personnelles 
    à des tiers. Les seules exceptions sont :</p>
    <ul>
        <li>Si la loi l'exige (obligation légale)</li>
        <li>Pour protéger nos droits ou la sécurité de l'application</li>
    </ul>
    
    <h3>Vos droits</h3>
    <p>Conformément au RGPD, vous disposez des droits suivants :</p>
    <ul>
        <li><strong>Droit d'accès :</strong> Demander quelles données nous détenons</li>
        <li><strong>Droit de rectification :</strong> Corriger des données inexactes</li>
        <li><strong>Droit à l'effacement :</strong> Demander la suppression de vos données</li>
        <li><strong>Droit d'opposition :</strong> Vous opposer au traitement</li>
        <li><strong>Droit à la portabilité :</strong> Recevoir vos données dans un format structuré</li>
    </ul>
    
    <h3>Contact DPO</h3>
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-user-shield"></i>
        </div>
        <div>
            <p>Pour toute question concernant la protection de vos données, 
            vous pouvez contacter notre responsable de la protection des données :<br>
            <a href="/contact">Via notre formulaire de contact</a></p>
        </div>
    </div>
    
    <div class="alert alert-info mt-4">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Transparence :</strong> Cette politique de confidentialité est révisée 
        régulièrement pour s'assurer de sa conformité avec les réglementations en vigueur.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Politique de Confidentialité",
        badge="Protection des données",
        subtitle="Comment nous protégeons vos données personnelles",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )


@legal_bp.route('/conditions-utilisation')
def terms_of_service():
    """Conditions d'utilisation"""
    
    content = """
    <h2>Conditions d'Utilisation</h2>
    
    <div class="info-box">
        <i class="fas fa-file-contract me-2"></i>
        <strong>Acceptation des conditions :</strong> En utilisant {{ config.NAME }}, 
        vous acceptez les présentes conditions d'utilisation. Si vous n'acceptez pas 
        ces conditions, veuillez ne pas utiliser notre service.
    </div>
    
    <h3>Description du service</h3>
    <p>{{ config.NAME }} est une application web gratuite permettant la fusion de 
    fichiers PDF. Le service est fourni "tel quel" et est accessible gratuitement 
    à toute personne disposant d'une connexion Internet.</p>
    
    <h3>Utilisation autorisée</h3>
    <p>Vous vous engagez à utiliser le service :</p>
    <ul>
        <li>De manière légale et conforme à ces conditions</li>
        <li>Sans tenter de contourner les mesures de sécurité</li>
        <li>Sans uploader de contenu illégal ou protégé par des droits d'auteur sans autorisation</li>
        <li>Sans perturber le fonctionnement normal du service</li>
    </ul>
    
    <h3>Fichiers PDF</h3>
    <p><strong>Important :</strong></p>
    <ul>
        <li>Vous ne devez uploader que des fichiers PDF dont vous êtes propriétaire 
        ou pour lesquels vous avez obtenu l'autorisation</li>
        <li>Les fichiers sont traités uniquement en mémoire et ne sont jamais stockés 
        sur nos serveurs</li>
        <li>Nous ne sommes pas responsables du contenu des fichiers traités</li>
        <li>Le service est limité à {{ config.MAX_FILES }} fichiers et {{ config.MAX_FILE_SIZE_MB }} Mo par fichier</li>
    </ul>
    
    <h3>Limitation de responsabilité</h3>
    <p>{{ config.NAME }} ne peut être tenu responsable :</p>
    <ul>
        <li>Des dommages directs ou indirects résultant de l'utilisation du service</li>
        <li>De la perte ou de l'altération de vos fichiers PDF</li>
        <li>De l'indisponibilité temporaire ou définitive du service</li>
        <li>De l'utilisation frauduleuse de vos fichiers par des tiers</li>
    </ul>
    
    <h3>Disponibilité du service</h3>
    <p>Nous nous efforçons d'assurer un service disponible 24h/24 et 7j/7, 
    mais nous ne pouvons garantir une disponibilité ininterrompue. Des périodes 
    de maintenance ou des problèmes techniques peuvent rendre le service temporairement 
    inaccessible.</p>
    
    <h3>Modification des conditions</h3>
    <p>Nous nous réservons le droit de modifier ces conditions d'utilisation à tout moment. 
    Les modifications prendront effet dès leur publication sur cette page. 
    Il est de votre responsabilité de consulter régulièrement ces conditions.</p>
    
    <h3>Propriété intellectuelle</h3>
    <p>L'application, son code source, son interface utilisateur, son design 
    et tous les éléments associés sont la propriété de {{ config.DEVELOPER_NAME }} 
    ou de ses concédants et sont protégés par les lois sur la propriété intellectuelle.</p>
    
    <h3>Loi applicable</h3>
    <p>Les présentes conditions sont régies et interprétées conformément au droit français. 
    Tout litige relatif à l'exécution ou à l'interprétation des présentes sera 
    de la compétence exclusive des tribunaux français.</p>
    
    <div class="alert alert-warning mt-4">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Utilisation responsable :</strong> Nous nous réservons le droit de suspendre 
        ou de résilier votre accès au service en cas de violation de ces conditions 
        d'utilisation.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Conditions d'Utilisation",
        badge="Conditions générales",
        subtitle="Règles d'utilisation du service",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )


@legal_bp.route('/a-propos')
def about():
    content = f"""
    <h2>À propos de PDF Fusion Pro</h2>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-rocket"></i>
        </div>
        <div>
            <h3 class="h5 mb-1">Notre mission</h3>
            <p>Offrir un outil PDF en ligne performant, intuitif et respectueux de votre vie privée.</p>
        </div>
    </div>
    
    <h2 class="mt-4">Caractéristiques principales</h2>
    
    <div class="row mt-3">
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-object-group text-primary me-2"></i>
                        Fusion PDF
                    </h4>
                    <p class="card-text">Combine plusieurs fichiers PDF en un seul document organisé.</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-cut text-success me-2"></i>
                        Division PDF
                    </h4>
                    <p class="card-text">Divisez vos PDF par page, par plage ou selon des pages spécifiques.</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-sync-alt text-warning me-2"></i>
                        Rotation PDF
                    </h4>
                    <p class="card-text">Faites pivoter des pages spécifiques ou l'ensemble du document.</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-compress-alt text-danger me-2"></i>
                        Compression PDF
                    </h4>
                    <p class="card-text">Réduisez la taille de vos fichiers PDF sans perte de qualité notable.</p>
                </div>
            </div>
        </div>
    </div>
    
    <h2 class="mt-4">Nos engagements</h2>
    
    <h3><i class="fas fa-lock text-success me-2"></i> Sécurité</h3>
    <p>Tous les traitements sont effectués en mémoire. Aucun fichier n'est stocké sur nos serveurs.</p>
    
    <h3><i class="fas fa-tachometer-alt text-primary me-2"></i> Performance</h3>
    <p>Interface optimisée pour une expérience utilisateur fluide et rapide.</p>
    
    <h3><i class="fas fa-eye-slash text-info me-2"></i> Confidentialité</h3>
    <p>Nous ne collectons pas de données personnelles liées au contenu de vos fichiers.</p>
    
    <h3><i class="fas fa-dollar-sign text-warning me-2"></i> Gratuité</h3>
    <p>Service entièrement gratuit, financé par des publicités discrètes et non intrusives.</p>
    
    <h2>Développeur</h2>
    <p><strong>{AppConfig.NAME}</strong> est développé et maintenu par <strong>{AppConfig.DEVELOPER_NAME}</strong>, un développeur passionné par la création d'outils web utiles et accessibles.</p>
    
    <div class="info-box mt-4">
        <i class="fas fa-code me-2"></i>
        <strong>Technologies utilisées :</strong> Python, Flask, PyPDF2, Bootstrap 5, JavaScript moderne.
    </div>
    
    <div class="card border-primary mt-4">
        <div class="card-body">
            <h4 class="card-title">
                <i class="fas fa-comments text-primary me-2"></i>
                Une question ou suggestion ?
            </h4>
            <p class="card-text">Nous sommes à votre écoute pour améliorer le service.</p>
            <a href="/contact" class="btn btn-primary">
                <i class="fas fa-paper-plane me-1"></i> Utiliser le formulaire de contact
            </a>
        </div>
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="À Propos",
        badge="Notre histoire",
        subtitle="Découvrez PDF Fusion Pro, notre mission et nos valeurs",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )