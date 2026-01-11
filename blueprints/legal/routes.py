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
    
    <!-- 3. Balises meta robots -->
    <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="googlebot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    <meta name="bingbot" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
    
    <!-- 5. URL canonique dynamique -->
    <link rel="canonical" href="https://pdf-fusion-pro-ultimate.onrender.com{{ request.path }}" />
    
    <!-- 4. Données structurées pour pages légales -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "{{ title }} | {{ config.NAME }}",
        "description": "{{ subtitle }}",
        "url": "https://pdf-fusion-pro-ultimate.onrender.com{{ request.path }}",
        "datePublished": "2024-01-15",
        "dateModified": "{% now 'local', '%Y-%m-%d' %}",
        "inLanguage": "fr",
        "isPartOf": {
            "@type": "WebSite",
            "name": "PDF Fusion Pro",
            "url": "https://pdf-fusion-pro-ultimate.onrender.com"
        },
        "publisher": {
            "@type": "Person",
            "name": "{{ config.DEVELOPER_NAME }}",
            "email": "{{ config.DEVELOPER_EMAIL }}"
        }
    }
    </script>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
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
    else:
        print("   ⚠️ SMTP non configuré dans les variables d'environnement")
    
    # Toujours retourner True pour ne pas bloquer le formulaire
    return True
    
    # ============================================
    # ANCIEN CODE SMTP (COMMENTÉ TEMPORAIREMENT)
    # ============================================
    '''
    # NE PAS EXÉCUTER CE CODE POUR LE MOMENT
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    developer_email = os.environ.get('DEVELOPER_EMAIL', AppConfig.DEVELOPER_EMAIL)
    
    # ... reste de l'ancien code SMTP ...
    '''


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
            
            # 4. Message informatif dans les logs
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
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Sécurité :</strong> Configurez la variable d'environnement 
                    <code>ADMIN_PASSWORD</code> sur Render pour un mot de passe sécurisé.
                </div>
            </div>
        </body>
        </html>
        """, 401
    
    # ============================================
    # DÉBUT DE L'INTERFACE ADMIN
    # ============================================
    
    contacts_dir = Path("data/contacts")
    contacts = []
    
    if contacts_dir.exists():
        # Lire tous les fichiers JSON
        for filepath in sorted(contacts_dir.glob("*.json"), 
                              key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    contact_data = json.load(f)
                    contact_data['filename'] = filepath.name
                    contact_data['file_size'] = f"{filepath.stat().st_size:,} octets"
                    contact_data['modified'] = datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).strftime('%d/%m/%Y %H:%M')
                    contacts.append(contact_data)
            except Exception as e:
                contacts.append({
                    'filename': filepath.name,
                    'error': str(e),
                    'modified': datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).strftime('%d/%m/%Y %H:%M')
                })
    
    # Gérer les actions (suppression, marquer comme traité)
    action = request.args.get('action')
    filename = request.args.get('file')
    
    if action and filename:
        filepath = contacts_dir / filename
        if filepath.exists():
            if action == 'delete':
                try:
                    filepath.unlink()
                    return redirect(f'/admin/messages?password={admin_password}&deleted={filename}')
                except:
                    pass
            elif action == 'toggle_processed':
                try:
                    with open(filepath, 'r+', encoding='utf-8') as f:
                        data = json.load(f)
                        data['processed'] = not data.get('processed', False)
                        data['processed_at'] = datetime.now().isoformat() if data['processed'] else None
                        f.seek(0)
                        json.dump(data, f, indent=2, ensure_ascii=False)
                        f.truncate()
                    return redirect(f'/admin/messages?password={admin_password}')
                except:
                    pass
    
    # Calculer les statistiques
    stats = {
        'total': len(contacts),
        'processed': sum(1 for c in contacts if c.get('processed')),
        'bug': sum(1 for c in contacts if c.get('subject') == 'bug'),
        'improvement': sum(1 for c in contacts if c.get('subject') == 'improvement'),
        'partnership': sum(1 for c in contacts if c.get('subject') == 'partnership'),
        'other': sum(1 for c in contacts if c.get('subject') == 'other'),
        'today': sum(1 for c in contacts if c.get('received_at', '').startswith(
            datetime.now().strftime('%Y-%m-%d')
        ))
    }
    
    # Sujets traduits
    subject_translation = {
        'bug': '🚨 Bug/Problème',
        'improvement': '💡 Suggestion',
        'partnership': '🤝 Partenariat',
        'other': '❓ Autre'
    }
    
    # Générer l'HTML de l'interface admin
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Messages de Contact - Admin</title>
        
        <!-- Bootstrap 5.3 -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        
        <style>
            :root {{
                --primary-color: #4361ee;
                --secondary-color: #3a0ca3;
                --success-color: #2ecc71;
                --warning-color: #f39c12;
                --danger-color: #e74c3c;
            }}
            
            body {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            
            .admin-container {{
                max-width: 1400px;
                margin: 2rem auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
                overflow: hidden;
            }}
            
            .admin-header {{
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 2rem;
            }}
            
            .admin-badge {{
                display: inline-block;
                background: rgba(255, 255, 255, 0.2);
                padding: 0.5rem 1.5rem;
                border-radius: 50px;
                font-weight: 600;
                margin-bottom: 1rem;
            }}
            
            .admin-content {{
                padding: 2rem;
            }}
            
            .stats-card {{
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                border-left: 4px solid var(--primary-color);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
                transition: transform 0.3s;
                height: 100%;
            }}
            
            .stats-card:hover {{
                transform: translateY(-5px);
            }}
            
            .stats-icon {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                margin-bottom: 1rem;
            }}
            
            .message-card {{
                background: white;
                border-radius: 15px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border: 2px solid #e9ecef;
                transition: all 0.3s;
            }}
            
            .message-card:hover {{
                border-color: var(--primary-color);
                box-shadow: 0 5px 20px rgba(67, 97, 238, 0.1);
            }}
            
            .message-card.processed {{
                border-color: var(--success-color);
                background: linear-gradient(135deg, #f8fff9, #e8f7ec);
            }}
            
            .message-header {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 1rem;
            }}
            
            .message-content {{
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 10px;
                max-height: 200px;
                overflow-y: auto;
                font-family: monospace;
                white-space: pre-wrap;
            }}
            
            .badge-subject {{
                font-size: 0.8em;
                padding: 0.4em 0.8em;
            }}
            
            .btn-action {{
                padding: 0.3rem 0.8rem;
                font-size: 0.85rem;
                margin: 0 0.2rem;
            }}
            
            @media (max-width: 768px) {{
                .admin-container {{
                    margin: 1rem;
                    border-radius: 15px;
                }}
                
                .admin-header, .admin-content {{
                    padding: 1.5rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="admin-container">
            <div class="admin-header">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <div class="admin-badge">
                            <i class="fas fa-user-shield me-2"></i> Administration
                        </div>
                        <h1 class="display-6 fw-bold mb-2">Messages de Contact</h1>
                        <p class="opacity-90 mb-0">
                            <i class="fas fa-file-pdf me-1"></i> PDF Fusion Pro
                            <span class="mx-2">•</span>
                            <i class="fas fa-folder me-1"></i> data/contacts/
                        </p>
                    </div>
                    <div class="text-end">
                        <a href="/" class="btn btn-outline-light btn-sm me-2">
                            <i class="fas fa-home me-1"></i> Accueil
                        </a>
                        <a href="/contact" class="btn btn-light btn-sm">
                            <i class="fas fa-envelope me-1"></i> Formulaire
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="admin-content">
    """
    
    # Messages d'alerte
    if request.args.get('deleted'):
        html += f"""
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Message supprimé :</strong> {request.args.get('deleted')}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
        """
    
    if not contacts:
        html += """
                <div class="text-center py-5">
                    <div class="mb-4">
                        <i class="fas fa-inbox fa-4x text-muted"></i>
                    </div>
                    <h3 class="text-muted mb-3">Aucun message pour le moment</h3>
                    <p class="text-muted">Les messages soumis via le formulaire de contact apparaîtront ici.</p>
                    <a href="/contact" class="btn btn-primary">
                        <i class="fas fa-eye me-1"></i> Voir le formulaire
                    </a>
                </div>
        """
    else:
        # Statistiques
        html += f"""
                <div class="row mb-4">
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #4361ee, #3a0ca3); color: white;">
                                <i class="fas fa-envelope"></i>
                            </div>
                            <h3 class="fw-bold">{stats['total']}</h3>
                            <p class="text-muted mb-0">Messages totaux</p>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #2ecc71, #27ae60); color: white;">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <h3 class="fw-bold">{stats['processed']}</h3>
                            <p class="text-muted mb-0">Messages traités</p>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #f39c12, #e67e22); color: white;">
                                <i class="fas fa-bug"></i>
                            </div>
                            <h3 class="fw-bold">{stats['bug']}</h3>
                            <p class="text-muted mb-0">Rapports de bugs</p>
                        </div>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white;">
                                <i class="fas fa-lightbulb"></i>
                            </div>
                            <h3 class="fw-bold">{stats['improvement']}</h3>
                            <p class="text-muted mb-0">Suggestions</p>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3>
                        <i class="fas fa-list me-2"></i>
                        Messages reçus ({stats['total']})
                    </h3>
                    <div>
                        <a href="/admin/messages?password={admin_password}&export=json" class="btn btn-success btn-sm">
                            <i class="fas fa-download me-1"></i> Exporter JSON
                        </a>
                        <button class="btn btn-warning btn-sm ms-2" onclick="toggleAllMessages()">
                            <i class="fas fa-eye me-1"></i> Tout afficher/masquer
                        </button>
                    </div>
                </div>
        """
        
        # Liste des messages
        for i, contact in enumerate(contacts, 1):
            # Gestion des erreurs de lecture
            if 'error' in contact:
                html += f"""
                <div class="message-card">
                    <div class="message-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge bg-danger badge-subject">
                                    <i class="fas fa-exclamation-triangle me-1"></i> ERREUR
                                </span>
                            </div>
                            <small class="text-muted">{contact.get('modified', 'Date inconnue')}</small>
                        </div>
                    </div>
                    <p class="text-danger">
                        <i class="fas fa-times-circle me-1"></i>
                        Erreur de lecture : {contact.get('error', 'Inconnue')}
                    </p>
                    <p class="mb-2"><strong>Fichier :</strong> {contact.get('filename')}</p>
                    <div class="text-end">
                        <a href="/admin/messages?password={admin_password}&action=delete&file={contact.get('filename')}" 
                           class="btn btn-danger btn-sm btn-action"
                           onclick="return confirm('Supprimer ce fichier corrompu ?')">
                            <i class="fas fa-trash"></i> Supprimer
                        </a>
                    </div>
                </div>
                """
                continue
            
            # Message normal
            subject_display = subject_translation.get(
                contact.get('subject', 'other'),
                contact.get('subject', 'Autre')
            )
            
            # Couleur du badge selon le sujet
            badge_color = {
                'bug': 'danger',
                'improvement': 'warning',
                'partnership': 'info',
                'other': 'secondary'
            }.get(contact.get('subject', 'other'), 'secondary')
            
            processed = contact.get('processed', False)
            processed_class = 'processed' if processed else ''
            
            # Date formatée
            received_at = contact.get('received_at', '')
            if 'T' in received_at:
                date_part, time_part = received_at.split('T')
                time_part = time_part.split('.')[0]
                display_date = f"{date_part} {time_part}"
            else:
                display_date = received_at
            
            html += f"""
            <div class="message-card {processed_class}" id="message-{i}">
                <div class="message-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-{badge_color} badge-subject">
                                {subject_display}
                            </span>
                            <span class="badge {'bg-success' if processed else 'bg-secondary'} badge-subject ms-2">
                                <i class="fas fa-{'check' if processed else 'clock'} me-1"></i>
                                {'Traité' if processed else 'En attente'}
                            </span>
                        </div>
                        <div>
                            <small class="text-muted me-3">
                                <i class="fas fa-calendar me-1"></i> {display_date}
                            </small>
                            <small class="text-muted">
                                <i class="fas fa-hashtag me-1"></i> #{i}
                            </small>
                        </div>
                    </div>
                    
                    <div class="row mt-2">
                        <div class="col-md-4">
                            <p class="mb-1"><strong><i class="fas fa-user me-1"></i> Nom :</strong></p>
                            <p class="mb-0">{contact.get('first_name', 'N/A')} {contact.get('last_name', 'N/A')}</p>
                        </div>
                        <div class="col-md-4">
                            <p class="mb-1"><strong><i class="fas fa-envelope me-1"></i> Email :</strong></p>
                            <p class="mb-0">
                                <a href="mailto:{contact.get('email', '')}" class="text-decoration-none">
                                    {contact.get('email', 'N/A')}
                                </a>
                            </p>
                        </div>
                        <div class="col-md-4">
                            <p class="mb-1"><strong><i class="fas fa-phone me-1"></i> Téléphone :</strong></p>
                            <p class="mb-0">{contact.get('phone', 'Non renseigné')}</p>
                        </div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <p class="mb-1"><strong><i class="fas fa-comment me-1"></i> Message :</strong></p>
                    <div class="message-content" id="content-{i}">
                        {contact.get('message', 'Aucun message')}
                    </div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center">
                    <div class="text-muted small">
                        <i class="fas fa-file me-1"></i> {contact.get('filename')}
                        <span class="mx-2">•</span>
                        <i class="fas fa-hdd me-1"></i> {contact.get('file_size', 'N/A')}
                        <span class="mx-2">•</span>
                        <i class="fas fa-globe me-1"></i> {contact.get('ip_address', 'N/A')}
                    </div>
                    
                    <div>
                        <button class="btn btn-outline-primary btn-sm btn-action" 
                                onclick="copyToClipboard('{contact.get('email', '')}')"
                                title="Copier l'email">
                            <i class="fas fa-copy"></i>
                        </button>
                        
                        <a href="mailto:{contact.get('email', '')}" 
                           class="btn btn-outline-success btn-sm btn-action"
                           title="Répondre">
                            <i class="fas fa-reply"></i>
                        </a>
                        
                        <a href="/admin/messages?password={admin_password}&action=toggle_processed&file={contact.get('filename')}" 
                           class="btn {'btn-success' if not processed else 'btn-secondary'} btn-sm btn-action"
                           title="{'Marquer comme traité' if not processed else 'Marquer non traité'}">
                            <i class="fas fa-{'check' if not processed else 'undo'}"></i>
                        </a>
                        
                        <a href="/admin/messages?password={admin_password}&action=delete&file={contact.get('filename')}" 
                           class="btn btn-outline-danger btn-sm btn-action"
                           onclick="return confirm('Supprimer définitivement ce message ?')"
                           title="Supprimer">
                            <i class="fas fa-trash"></i>
                        </a>
                    </div>
                </div>
            </div>
            """
    
    # Footer et scripts
    html += f"""
            </div>
            
            <div class="admin-content border-top">
                <div class="row">
                    <div class="col-md-6">
                        <div class="alert alert-info">
                            <h5><i class="fas fa-info-circle me-2"></i> Informations</h5>
                            <ul class="mb-0">
                                <li>Messages sauvegardés dans <code>data/contacts/</code></li>
                                <li>Chaque message est un fichier JSON indépendant</li>
                                <li>Statistiques mises à jour en temps réel</li>
                                <li>Session admin protégée par mot de passe</li>
                            </ul>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="alert alert-warning">
                            <h5><i class="fas fa-exclamation-triangle me-2"></i> Sécurité</h5>
                            <p class="mb-2">Pour plus de sécurité :</p>
                            <ol class="mb-0">
                                <li>Configurez <code>ADMIN_PASSWORD</code> sur Render</li>
                                <li>Changez régulièrement le mot de passe</li>
                                <li>Limitez l'accès à cette page</li>
                            </ol>
                        </div>
                    </div>
                </div>
                
                <div class="text-center mt-4">
                    <a href="/admin/messages?password={admin_password}&export=json" class="btn btn-success me-2">
                        <i class="fas fa-download me-1"></i> Exporter tous les messages (JSON)
                    </a>
                    <a href="/admin/messages?password={admin_password}&cleanup=true" class="btn btn-warning me-2"
                       onclick="return confirm('Supprimer les messages de plus de 30 jours ?')">
                        <i class="fas fa-broom me-1"></i> Nettoyer les anciens
                    </a>
                    <a href="/" class="btn btn-outline-primary">
                        <i class="fas fa-home me-1"></i> Retour à l'accueil
                    </a>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JS -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        
        <script>
            // Copier l'email dans le presse-papier
            function copyToClipboard(email) {{
                navigator.clipboard.writeText(email).then(function() {{
                    alert('Email copié : ' + email);
                }}, function(err) {{
                    alert('Erreur de copie : ' + err);
                }});
            }}
            
            // Afficher/masquer tous les messages
            function toggleAllMessages() {{
                const messageContents = document.querySelectorAll('[id^="content-"]');
                const allHidden = Array.from(messageContents).every(content => 
                    content.style.display === 'none' || content.style.maxHeight === '0px'
                );
                
                messageContents.forEach(content => {{
                    if (allHidden) {{
                        content.style.display = 'block';
                        content.style.maxHeight = 'none';
                    }} else {{
                        content.style.display = 'none';
                        content.style.maxHeight = '0px';
                    }}
                }});
                
                const btn = document.querySelector('button[onclick="toggleAllMessages()"]');
                btn.innerHTML = allHidden ? 
                    '<i class="fas fa-eye-slash me-1"></i> Tout masquer' : 
                    '<i class="fas fa-eye me-1"></i> Tout afficher';
            }}
            
            // Initialiser : masquer les longs messages
            document.addEventListener('DOMContentLoaded', function() {{
                const messageContents = document.querySelectorAll('[id^="content-"]');
                messageContents.forEach(content => {{
                    if (content.scrollHeight > 200) {{
                        content.style.maxHeight = '200px';
                        content.style.overflowY = 'auto';
                    }}
                }});
                
                // Message de confirmation pour suppression
                const deleteLinks = document.querySelectorAll('a[href*="action=delete"]');
                deleteLinks.forEach(link => {{
                    link.addEventListener('click', function(e) {{
                        if (!confirm('Êtes-vous sûr de vouloir supprimer ce message ?')) {{
                            e.preventDefault();
                        }}
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    # Gérer l'export JSON
    if request.args.get('export') == 'json':
        clean_contacts = []
        for contact in contacts:
            if 'error' not in contact:
                clean_contacts.append({
                    k: v for k, v in contact.items() 
                    if k not in ['filename', 'file_size', 'modified']
                })
        return jsonify(clean_contacts)
    
    # Gérer le nettoyage
    if request.args.get('cleanup') == 'true':
        cutoff_time = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        deleted = 0
        for filepath in contacts_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    deleted += 1
                except:
                    pass
        return redirect(f'/admin/messages?password={admin_password}&cleaned={deleted}')
    
    return html


@legal_bp.route('/mentions-legales')
def legal_notices():
    content = f"""
    <div class="info-box">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Information importante :</strong> Cette application traite vos fichiers PDF uniquement en mémoire.
        Aucun fichier n'est stocké de manière permanente sur nos serveurs.
    </div>
    
    <h2>Éditeur du service</h2>
    <p>Le service <strong>{AppConfig.NAME}</strong> est développé et maintenu par <strong>{AppConfig.DEVELOPER_NAME}</strong>.</p>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-user-tie"></i>
        </div>
        <div>
            <h4 class="h5 mb-2">Pour nous contacter :</h4>
            <p>Utilisez notre <a href="/contact" class="btn btn-outline-primary btn-sm">
                <i class="fas fa-envelope me-1"></i> Formulaire de contact
            </a></p>
            <p class="small text-muted">Nous répondons généralement dans les 48 heures.</p>
        </div>
    </div>
    
    <h2>Hébergement</h2>
    <p>Ce service est hébergé sur la plateforme <strong>{AppConfig.HOSTING}</strong> (<a href="https://{AppConfig.DOMAIN}" target="_blank">{AppConfig.DOMAIN}</a>).</p>
    <p>Les serveurs sont localisés dans des centres de données sécurisés et conformes aux normes européennes de protection des données.</p>
    
    <h2>Propriété intellectuelle</h2>
    <p>L'ensemble des contenus présents sur ce site (design, code source, interfaces, textes, graphismes) est protégé par les lois relatives à la propriété intellectuelle.</p>
    <p>Toute reproduction, modification, distribution ou exploitation non autorisée est strictement interdite.</p>
    
    <h2>Responsabilité</h2>
    <p>L'utilisateur reste l'unique responsable des fichiers PDF qu'il téléverse et traite via ce service.</p>
    <p>Il s'engage à ne pas utiliser le service pour des contenus illicites ou protégés par des droits d'auteur sans autorisation.</p>
    
    <h2>Disponibilité du service</h2>
    <p>Nous nous efforçons d'assurer une disponibilité continue du service, mais ne pouvons garantir un fonctionnement ininterrompu.</p>
    <p>Des périodes de maintenance technique peuvent être nécessaires pour améliorer le service.</p>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Mentions Légales",
        badge="Information légale",
        subtitle="Informations légales concernant l'utilisation du service PDF Fusion Pro",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )


@legal_bp.route('/politique-confidentialite')
def privacy_policy():
    content = f"""
    <h2>Respect de votre vie privée</h2>
    <p>Votre confidentialité est notre priorité. Cette politique explique comment nous collectons, utilisons et protégeons vos informations.</p>
    
    <div class="info-box">
        <i class="fas fa-shield-alt me-2"></i>
        <strong>Engagement de confidentialité :</strong> Nous ne stockons jamais le contenu de vos fichiers PDF.
        Tous les traitements sont effectués en mémoire vive et les fichiers sont supprimés immédiatement après traitement.
    </div>
    
    <h2>Données collectées</h2>
    <h3>Données techniques</h3>
    <p>Nous collectons des données techniques anonymes pour améliorer le service :</p>
    <ul>
        <li>Type d'opération effectuée (fusion, division, rotation, compression)</li>
        <li>Nombre de pages traitées</li>
        <li>Heure et date des opérations (anonymisées)</li>
        <li>Informations sur le navigateur et l'appareil (type, version)</li>
    </ul>
    
    <h3>Cookies</h3>
    <p>Nous utilisons uniquement des cookies techniques essentiels :</p>
    <ul>
        <li><strong>Session cookie :</strong> Pour maintenir votre session de travail</li>
        <li><strong>Préférences :</strong> Pour mémoriser vos paramètres d'interface</li>
    </ul>
    
    <h2>Publicité — Google AdSense</h2>
    <p>Ce site utilise <strong>Google AdSense</strong> (ID: {AppConfig.ADSENSE_CLIENT_ID}) pour afficher des publicités pertinentes.</p>
    <p>Google utilise des cookies pour personnaliser les annonces en fonction de votre navigation sur ce site et d'autres sites web.</p>
    <p>Vous pouvez désactiver la personnalisation des annonces via les <a href="https://adssettings.google.com" target="_blank">paramètres des annonces Google</a>.</p>
    
    <h2>Vos droits (RGPD)</h2>
    <p>Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des droits suivants :</p>
    <ul>
        <li>Droit d'accès à vos données</li>
        <li>Droit de rectification</li>
        <li>Droit à l'effacement</li>
        <li>Droit à la limitation du traitement</li>
        <li>Droit à la portabilité des données</li>
    </ul>
    
    <p>Pour exercer ces droits, utilisez notre <a href="/contact" class="btn btn-outline-primary btn-sm">
        <i class="fas fa-envelope me-1"></i> Formulaire de contact
    </a> en précisant "Exercice de droits RGPD" dans le sujet.</p>
    
    <h2>Sécurité des données</h2>
    <p>Nous mettons en œuvre des mesures de sécurité techniques et organisationnelles appropriées pour protéger vos données contre tout accès non autorisé, altération ou destruction.</p>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Politique de Confidentialité",
        badge="Protection des données",
        subtitle="Comment nous protégeons et utilisons vos données",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )


@legal_bp.route('/conditions-utilisation')
def terms_of_service():
    content = f"""
    <h2>Acceptation des conditions</h2>
    <p>En utilisant le service <strong>{AppConfig.NAME}</strong>, vous acceptez pleinement et sans réserve les présentes conditions d'utilisation.</p>
    
    <div class="info-box">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Avertissement important :</strong> Ce service est fourni "tel quel". 
        Nous déclinons toute responsabilité concernant les fichiers traités par l'utilisateur.
    </div>
    
    <h2>Usage autorisé</h2>
    <p>Vous vous engagez à utiliser le service de manière responsable et légale :</p>
    
    <h3>Interdictions</h3>
    <ul>
        <li>Téléverser des fichiers contenant des données illicites ou protégés par des droits d'auteur sans autorisation</li>
        <li>Utiliser le service pour des activités frauduleuses ou malveillantes</li>
        <li>Tenter de contourner les mesures de sécurité du service</li>
        <li>Surcharger délibérément le service (attaques DoS/DDoS)</li>
        <li>Réutiliser le contenu du service à des fins commerciales sans autorisation</li>
    </ul>
    
    <h3>Obligations</h3>
    <ul>
        <li>Respecter les droits de propriété intellectuelle des documents traités</li>
        <li>Assurer la confidentialité de vos propres fichiers</li>
        <li>Utiliser le service conformément à sa destination première</li>
    </ul>
    
    <h2>Limitation de responsabilité</h2>
    <p>Le service est fourni sans aucune garantie, expresse ou implicite, y compris, mais sans s'y limiter, les garanties de qualité marchande, d'adéquation à un usage particulier et de non-contrefaçon.</p>
    
    <p>En aucun cas, <strong>{AppConfig.DEVELOPER_NAME}</strong> ne pourra être tenu responsable :</p>
    <ul>
        <li>Des dommages directs ou indirects résultant de l'utilisation ou de l'impossibilité d'utiliser le service</li>
        <li>De la perte ou de l'altération des fichiers PDF traités</li>
        <li>Des conséquences de l'utilisation des fichiers générés par le service</li>
    </ul>
    
    <h2>Modifications des conditions</h2>
    <p>Nous nous réservons le droit de modifier ces conditions d'utilisation à tout moment.</p>
    <p>Les utilisateurs seront informés des changements significatifs via une notification sur le site.</p>
    
    <h2>Propriété intellectuelle</h2>
    <p>Le service, son code source, son design et son contenu sont la propriété exclusive de <strong>{AppConfig.DEVELOPER_NAME}</strong>.</p>
    <p>Toute reproduction, même partielle, est interdite sans autorisation préalable écrite.</p>
    
    <div class="alert alert-info mt-4">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Pour toute question concernant ces conditions :</strong>
        <div class="mt-2">
            <a href="/contact" class="btn btn-outline-primary">
                <i class="fas fa-envelope me-1"></i> Nous contacter via le formulaire
            </a>
        </div>
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Conditions d'Utilisation",
        badge="Règles d'usage",
        subtitle="Règles et conditions d'utilisation du service PDF Fusion Pro",
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