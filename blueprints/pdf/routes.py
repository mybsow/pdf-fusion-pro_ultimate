"""
Routes principales pour les outils PDF
"""

from flask import render_template_string
from datetime import datetime
from . import pdf_bp
from config import AppConfig

# RÉDUISEZ VOTRE HTML POUR TESTER D'ABORD
HTML_TEMPLATE_SIMPLE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <meta name="description" content="{{ description }}">
    
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ config.ADSENSE_PUBLISHER_ID }}" crossorigin="anonymous"></script>
    
    <style>
        body { font-family: Arial; padding: 20px; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1 class="success">✅ {{ config.NAME }} v{{ config.VERSION }}</h1>
    <p>Google AdSense actif - ID: {{ config.ADSENSE_PUBLISHER_ID }}</p>
    
    <!-- Test AdSense -->
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
         data-ad-slot="1234567890"
         data-ad-format="auto"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    
    <p>© {{ current_year }} {{ config.DEVELOPER_NAME }}</p>
</body>
</html>
"""

@pdf_bp.route('/')
def home():
    """Page d'accueil principale - version simple"""
    return render_template_string(
        HTML_TEMPLATE_SIMPLE,
        title="PDF Fusion Pro – Outil PDF Moderne",
        description="Fusionnez, divisez, tournez et compressez vos fichiers PDF gratuitement.",
        config=AppConfig,
        current_year=datetime.now().year
    )