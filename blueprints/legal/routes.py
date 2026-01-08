"""
Routes pour les pages légales
"""

from flask import render_template_string
from datetime import datetime
from . import legal_bp
from config import AppConfig

# Template pour les pages légales (copié de votre code)
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
            max-width: 900px;
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
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--light-color);
        }
        
        .legal-content h3 {
            color: var(--primary-color);
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
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
            margin: 1rem 0;
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
        
        @media (max-width: 768px) {
            .legal-container {
                margin: 1rem;
                border-radius: 15px;
            }
            
            .legal-header, .legal-content {
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
                        <i class="fas fa-envelope me-1"></i> {{ config.DEVELOPER_EMAIL }}
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
    </script>
</body>
</html>
"""

@legal_bp.route('/mentions-legales')
def legal_notices():
    content = f"""
    <div class="info-box">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Information importante :</strong> Cette application traite vos fichiers PDF uniquement en mémoire.
        Aucun fichier n'est stocké de manière permanente sur nos serveurs.
    </div>
    
    <h2>Éditeur du service</h2>
    <p>Le service <strong>{AppConfig.NAME}</strong> est développé et maintenu par :</p>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-user-tie"></i>
        </div>
        <div>
            <strong>{AppConfig.DEVELOPER_NAME}</strong><br>
            <a href="mailto:{AppConfig.DEVELOPER_EMAIL}">{AppConfig.DEVELOPER_EMAIL}</a>
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
    
    <p>Pour exercer ces droits, contactez-nous à : <a href="mailto:{AppConfig.DEVELOPER_EMAIL}">{AppConfig.DEVELOPER_EMAIL}</a></p>
    
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

@legal_bp.route('/contact')
def contact():
    content = f"""
    <h2>Nous contacter</h2>
    <p>Pour toute question, suggestion ou demande concernant le service, n'hésitez pas à nous écrire.</p>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-envelope"></i>
        </div>
        <div>
            <h3 class="h5 mb-1">Adresse email</h3>
            <a href="mailto:{AppConfig.DEVELOPER_EMAIL}" class="fs-5">{AppConfig.DEVELOPER_EMAIL}</a>
        </div>
    </div>
    
    <div class="info-box mt-4">
        <i class="fas fa-clock me-2"></i>
        <strong>Temps de réponse :</strong> Nous nous efforçons de répondre à tous les messages dans un délai de 48 heures.
    </div>
    
    <h2 class="mt-4">Types de demandes</h2>
    
    <h3><i class="fas fa-wrench me-2"></i> Support technique</h3>
    <p>Pour signaler un bug, un problème technique ou proposer une amélioration fonctionnelle.</p>
    
    <h3><i class="fas fa-shield-alt me-2"></i> Confidentialité / RGPD</h3>
    <p>Pour exercer vos droits relatifs à la protection des données personnelles.</p>
    
    <h3><i class="fas fa-ad me-2"></i> Publicité</h3>
    <p>Pour toute question concernant Google AdSense ou la publicité affichée.</p>
    
    <h3><i class="fas fa-handshake me-2"></i> Partenariats</h3>
    <p>Pour discuter d'opportunités de collaboration ou d'intégration.</p>
    
    <h2>Informations importantes</h2>
    <p>Lors de votre demande, merci de préciser :</p>
    <ul>
        <li>L'objet précis de votre demande</li>
        <li>Votre nom ou pseudonyme</li>
        <li>Toute information contextuelle utile</li>
    </ul>
    
    <div class="alert alert-warning mt-4">
        <i class="fas fa-exclamation-circle me-2"></i>
        <strong>Note :</strong> Pour des raisons de sécurité, nous ne traitons pas les demandes concernant des fichiers PDF spécifiques via email.
        Tous les traitements de fichiers doivent être effectués directement via l'interface web.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Contact",
        badge="Support",
        subtitle="Comment nous contacter pour toute question ou demande",
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