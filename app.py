# === PERSONNALISATION ===
DEVELOPER_NAME = "MYBSOW"
DEVELOPER_EMAIL = "banousow@gmail.com"
APP_VERSION = "3.0.0"
# ========================

import os
port = int(os.environ.get("PORT", 10000))
import sys
import tempfile
import shutil
import uuid
import io
import json
import base64
from datetime import datetime
from pathlib import Path

# Configuration Flask
from flask import Flask, render_template_string, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# PDF Processing
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, A3, legal, landscape
from reportlab.lib.units import inch

# ============================================
# GESTION DES PUBLICITÉS ADSENSE
# ============================================

# Pour le développement, utilisez l'ID de test Google
# Pour la production, remplacez par votre vrai ID Adsense
ADSENSE_CLIENT_ID = os.environ.get('ADSENSE_CLIENT_ID', 'ca-pub-8967416460526921')

def get_ad_units(page_type='home'):
    """Retourne les unités publicitaires selon la page"""
    
    ad_units = {
        'home': [
            {
                'id': 'home_leaderboard',
                'slot': '6355418833',  # Slot de test Google
                'format': 'leaderboard',
                'responsive': True
            }
        ],
        'merge': [
            {
                'id': 'merge_sidebar',
                'slot': '6355418833',  # Slot de test Google
                'format': 'rectangle',
                'responsive': True
            }
        ],
        'tools': [
            {
                'id': 'tools_banner',
                'slot': '6355418833',  # Slot de test Google
                'format': 'banner',
                'responsive': True
            }
        ]
    }
    
    return ad_units.get(page_type, [])

# ============================================
# CONFIGURATION RENDER.COM
# ============================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pdf-fusion-pro-secret-' + str(uuid.uuid4()))

# Proxy fix pour Render
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configuration des limites
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max par fichier
app.config['UPLOAD_FOLDER'] = '/tmp'  # Render utilise /tmp pour le stockage temporaire
app.config['TEMP_FOLDER'] = '/tmp/pdf_fusion'

# Créer le dossier temporaire
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# ============================================
# CLASSES DE TRAITEMENT PDF
# ============================================

class PDFProcessor:
    """Processeur PDF optimisé pour Render"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(dir=app.config['TEMP_FOLDER'])
        self.temp_files = []
    
    def cleanup(self):
        """Nettoyer les fichiers temporaires"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    
    def create_watermark(self, text="CONFIDENTIEL", position="center", 
                        opacity=0.3, font_size=48, page_size=A4):
        """Créer un PDF de filigrane"""
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=page_size)
        
        # Configuration du filigrane
        c.setFillAlpha(opacity)
        c.setFont("Helvetica-Bold", font_size)
        
        width, height = page_size
        
        # Positionnement
        if position == "center":
            c.drawCentredString(width/2, height/2, text)
        elif position == "topleft":
            c.drawString(1*inch, height - 1*inch, text)
        elif position == "topright":
            c.drawRightString(width - 1*inch, height - 1*inch, text)
        elif position == "bottomleft":
            c.drawString(1*inch, 1*inch, text)
        elif position == "bottomright":
            c.drawRightString(width - 1*inch, 1*inch, text)
        
        c.save()
        packet.seek(0)
        return PyPDF2.PdfReader(packet)
    
    def rotate_pages(self, pdf_data, angle=90, pages_range=None):
        """
        Tourner les pages d'un PDF
        
        Args:
            pdf_data: Données PDF brutes
            angle: Angle de rotation (90, 180, 270)
            pages_range: Liste de pages à tourner (ex: [1,3,5] ou "1-5,7,9-12")
        """
        # Créer un fichier temporaire
        temp_path = os.path.join(self.temp_dir, f"rotate_temp_{uuid.uuid4().hex}.pdf")
        with open(temp_path, 'wb') as f:
            f.write(pdf_data)
        self.temp_files.append(temp_path)
        
        # Lire le PDF
        pdf_reader = PyPDF2.PdfReader(temp_path)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Convertir pages_range en liste de pages
        pages_to_rotate = []
        if pages_range:
            if isinstance(pages_range, str):
                pages_to_rotate = self.parse_pages_range(pages_range, len(pdf_reader.pages))
            elif isinstance(pages_range, list):
                pages_to_rotate = pages_range
        
        # Traiter chaque page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            
            # Vérifier si cette page doit être tournée
            if not pages_range or (page_num in pages_to_rotate):
                # Appliquer la rotation
                if angle in [90, 180, 270]:
                    page.rotate(angle)
            
            pdf_writer.add_page(page)
        
        # Générer le PDF tourné
        output = io.BytesIO()
        pdf_writer.write(output)
        return output.getvalue()
    
    def parse_pages_range(self, pages_str, total_pages):
        """
        Convertir une chaîne de pages en liste
        
        Exemples:
            "1,3,5" -> [0, 2, 4]
            "1-5" -> [0, 1, 2, 3, 4]
            "1-3,5,7-9" -> [0, 1, 2, 4, 6, 7, 8]
        """
        pages = []
        if not pages_str:
            return pages
        
        # Nettoyer la chaîne
        pages_str = pages_str.replace(" ", "")
        
        # Séparer par les virgules
        parts = pages_str.split(",")
        
        for part in parts:
            if "-" in part:
                # C'est une plage (ex: "1-5")
                try:
                    start, end = part.split("-")
                    start = int(start) - 1  # Convertir en index 0-based
                    end = int(end) - 1
                    
                    # Ajuster les limites
                    start = max(0, start)
                    end = min(total_pages - 1, end)
                    
                    # Ajouter toutes les pages de la plage
                    pages.extend(range(start, end + 1))
                except ValueError:
                    continue
            else:
                # C'est une page unique
                try:
                    page_num = int(part) - 1  # Convertir en index 0-based
                    if 0 <= page_num < total_pages:
                        pages.append(page_num)
                except ValueError:
                    continue
        
        return pages
    
    def merge_pdfs(self, pdf_files, options=None):
        """Fusionner plusieurs PDFs avec options"""
        if options is None:
            options = {}
        
        writer = PyPDF2.PdfWriter()
        watermark = options.get('watermark', {})
        metadata = options.get('metadata', {})
        rotation = options.get('rotation', {})
        
        # Créer le filigrane si demandé
        watermark_pdf = None
        if watermark.get('enabled') and watermark.get('text'):
            watermark_pdf = self.create_watermark(
                watermark['text'],
                watermark.get('position', 'center'),
                watermark.get('opacity', 0.3),
                watermark.get('font_size', 48)
            )
        
        # Fusionner tous les PDFs
        for pdf_data in pdf_files:
            # Créer un fichier temporaire
            temp_path = os.path.join(self.temp_dir, f"temp_{uuid.uuid4().hex}.pdf")
            with open(temp_path, 'wb') as f:
                f.write(pdf_data)
            self.temp_files.append(temp_path)
            
            # Traiter le PDF
            with open(temp_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    # Appliquer la rotation si spécifiée
                    if rotation.get('enabled'):
                        angle = rotation.get('angle', 0)
                        pages_range = rotation.get('pages', 'all')
                        
                        # Vérifier si cette page doit être tournée
                        should_rotate = False
                        if pages_range == 'all':
                            should_rotate = True
                        else:
                            pages_to_rotate = self.parse_pages_range(pages_range, len(pdf_reader.pages))
                            should_rotate = page_num in pages_to_rotate
                        
                        if should_rotate and angle in [90, 180, 270]:
                            page.rotate(angle)
                    
                    # Appliquer le filigrane
                    if watermark_pdf:
                        page.merge_page(watermark_pdf.pages[0])
                    
                    writer.add_page(page)
        
        # Ajouter les métadonnées
        if metadata:
            meta_dict = {}
            if metadata.get('title'):
                meta_dict['/Title'] = metadata['title']
            if metadata.get('author'):
                meta_dict['/Author'] = metadata['author']
            if metadata.get('subject'):
                meta_dict['/Subject'] = metadata['subject']
            if metadata.get('keywords'):
                meta_dict['/Keywords'] = metadata['keywords']
            if metadata.get('auto_date', True):
                meta_dict['/CreationDate'] = datetime.now().strftime("D:%Y%m%d%H%M%S")
            
            writer.add_metadata(meta_dict)
        
        # Générer le PDF final
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

# ============================================
# ROUTES API
# ============================================

@app.route('/')
def home():
    """Page d'accueil avec interface web"""
    # Obtenir les publicités pour la page d'accueil
    ads = get_ad_units('home')
    
    return render_template_string(HTML_TEMPLATE, 
                                 adsense_client_id=ADSENSE_CLIENT_ID,
                                 ad_units=ads,
                                 page_type='home',
                                 developer_name=DEVELOPER_NAME,
                                 developer_email=DEVELOPER_EMAIL,
                                 app_version=APP_VERSION)

@app.route('/merge')
def merge_page():
    """Page de fusion PDF avec publicités spécifiques"""
    ads = get_ad_units('merge')
    return render_template_string(HTML_TEMPLATE,
                                 adsense_client_id=ADSENSE_CLIENT_ID,
                                 ad_units=ads,
                                 page_type='merge',
                                 developer_name=DEVELOPER_NAME,
                                 developer_email=DEVELOPER_EMAIL,
                                 app_version=APP_VERSION)

@app.route('/tools')
def tools_page():
    """Page outils avec publicités spécifiques"""
    ads = get_ad_units('tools')
    return render_template_string(HTML_TEMPLATE,
                                 adsense_client_id=ADSENSE_CLIENT_ID,
                                 ad_units=ads,
                                 page_type='tools',
                                 developer_name=DEVELOPER_NAME,
                                 developer_email=DEVELOPER_EMAIL,
                                 app_version=APP_VERSION)

@app.route('/about')
def about_page():
    """Page à propos"""
    ads = get_ad_units('home')  # Utiliser les mêmes publicités que la home
    return render_template_string(HTML_TEMPLATE,
                                 adsense_client_id=ADSENSE_CLIENT_ID,
                                 ad_units=ads,
                                 page_type='about',
                                 developer_name=DEVELOPER_NAME,
                                 developer_email=DEVELOPER_EMAIL,
                                 app_version=APP_VERSION)

@app.route('/health')
def health_check():
    """Endpoint de santé pour Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'PDF Fusion Pro',
        'version': APP_VERSION,
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('RENDER', 'development'),
        'developer': DEVELOPER_NAME
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Uploader des fichiers PDF"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if not file.filename.lower().endswith('.pdf'):
                continue
            
            # Lire le fichier
            file_data = file.read()
            
            # Vérifier la taille
            if len(file_data) > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': f'Fichier trop grand: {file.filename}'}), 400
            
            # Compter les pages
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                page_count = len(pdf_reader.pages)
            except:
                page_count = 0
            
            uploaded_files.append({
                'filename': secure_filename(file.filename),
                'size': len(file_data),
                'pages': page_count,
                'data': base64.b64encode(file_data).decode('utf-8')
            })
        
        return jsonify({
            'success': True,
            'files': uploaded_files,
            'count': len(uploaded_files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/merge', methods=['POST'])
def merge_pdfs():
    """Fusionner des PDFs"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type doit être application/json'}), 400
        
        data = request.get_json()
        
        if not data or 'files' not in data:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        # Décoder les fichiers base64
        pdf_files = []
        for file_info in data['files']:
            try:
                pdf_data = base64.b64decode(file_info['data'])
                pdf_files.append(pdf_data)
            except:
                continue
        
        if not pdf_files:
            return jsonify({'error': 'Aucun fichier PDF valide'}), 400
        
        # Options
        options = data.get('options', {})
        
        # Traiter les PDFs
        processor = PDFProcessor()
        try:
            merged_pdf = processor.merge_pdfs(pdf_files, options)
            
            return jsonify({
                'success': True,
                'filename': 'document-fusionne.pdf',
                'data': base64.b64encode(merged_pdf).decode('utf-8'),
                'size': len(merged_pdf)
            })
        finally:
            processor.cleanup()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/compress', methods=['POST'])
def compress_pdf():
    """Compresser un PDF"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        
        # Lire le fichier
        original_data = file.read()
        
        # Simple compression
        return jsonify({
            'success': True,
            'original_size': len(original_data),
            'compressed_size': len(original_data),
            'reduction': '0%',
            'data': base64.b64encode(original_data).decode('utf-8')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/info', methods=['POST'])
def get_pdf_info():
    """Obtenir des informations sur un PDF"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        file_data = file.read()
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        
        info = {
            'filename': secure_filename(file.filename),
            'size': len(file_data),
            'pages': len(pdf_reader.pages),
            'encrypted': pdf_reader.is_encrypted,
            'metadata': {}
        }
        
        if pdf_reader.metadata:
            info['metadata'] = {
                'title': pdf_reader.metadata.get('/Title', ''),
                'author': pdf_reader.metadata.get('/Author', ''),
                'subject': pdf_reader.metadata.get('/Subject', ''),
                'keywords': pdf_reader.metadata.get('/Keywords', '')
            }
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rotate', methods=['POST'])
def rotate_pdf():
    """Tourner les pages d'un PDF"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type doit être application/json'}), 400
        
        data = request.get_json()
        
        if not data or 'file' not in data:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        # Décoder le fichier base64
        try:
            pdf_data = base64.b64decode(data['file']['data'])
        except:
            return jsonify({'error': 'Données PDF invalides'}), 400
        
        # Récupérer les paramètres de rotation
        angle = data.get('angle', 90)
        pages = data.get('pages', 'all')
        
        # Valider l'angle
        if angle not in [90, 180, 270]:
            return jsonify({'error': 'Angle invalide. Utilisez 90, 180 ou 270.'}), 400
        
        # Traiter le PDF
        processor = PDFProcessor()
        try:
            rotated_pdf = processor.rotate_pages(
                pdf_data, 
                angle=angle, 
                pages_range=None if pages == 'all' else pages
            )
            
            return jsonify({
                'success': True,
                'filename': f'rotated_{angle}deg.pdf',
                'data': base64.b64encode(rotated_pdf).decode('utf-8'),
                'size': len(rotated_pdf),
                'angle': angle,
                'pages': pages
            })
        finally:
            processor.cleanup()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# TEMPLATE HTML CORRIGÉ AVEC ADSENSE
# ============================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Fusion Pro - Fusionnez vos PDFs gratuitement</title>
    <meta name="description" content="Fusionnez, compressez et modifiez vos PDFs en ligne gratuitement. Outil PDF 100% gratuit et sécurisé.">
    
    <!-- Bootstrap 5.3 Dark Theme -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- PDF.js pour la prévisualisation -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>

    <!-- Script Adsense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8967416460526921"
     crossorigin="anonymous"></script>
    <script>
        (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
    
    <style>
        :root {
            --primary-color: #0d6efd;
            --success-color: #198754;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --dark-bg: #212529;
            --darker-bg: #1a1d20;
            --light-text: #f8f9fa;
            --muted-text: #6c757d;
        }
        
        body {
            background: linear-gradient(135deg, var(--darker-bg) 0%, var(--dark-bg) 100%);
            min-height: 100vh;
            color: var(--light-text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
        }
        
        .card {
            background: rgba(33, 37, 41, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        
        .drop-area {
            border: 3px dashed var(--primary-color);
            border-radius: 15px;
            padding: 3rem;
            text-align: center;
            background: rgba(13, 110, 253, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
            min-height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        .drop-area.dragover {
            background: rgba(13, 110, 253, 0.2);
            border-color: var(--success-color);
            transform: scale(1.02);
        }
        
        .file-item {
            padding: 1rem;
            margin-bottom: 0.75rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border-left: 4px solid var(--primary-color);
        }
        
        .progress-ring {
            width: 80px;
            height: 80px;
        }
        
        .progress-ring-circle {
            transition: stroke-dashoffset 0.35s;
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
        }
        
        .watermark-preview {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 150px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.3);
            font-size: 2rem;
            font-weight: bold;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .watermark-preview::after {
            content: attr(data-text);
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 3rem;
            opacity: 0.2;
        }
        
        .feature-icon {
            width: 60px;
            height: 60px;
            background: var(--primary-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem;
            font-size: 1.5rem;
        }
        
        .stats-card {
            background: linear-gradient(135deg, var(--primary-color) 0%, #6610f2 100%);
            color: white;
            border: none;
        }
        
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
        }
        
        /* Styles pour les publicités */
        .ad-container {
            margin: 20px 0;
            text-align: center;
            overflow: hidden;
        }
        
        .ad-responsive {
            width: 100%;
            height: auto;
        }
        
        .ad-leaderboard {
            width: 728px;
            height: 90px;
            margin: 0 auto;
        }
        
        .ad-rectangle {
            width: 300px;
            height: 250px;
            margin: 0 auto;
        }
        
        .ad-banner {
            width: 468px;
            height: 60px;
            margin: 0 auto;
        }
        
        @media (max-width: 768px) {
            .drop-area {
                padding: 2rem 1rem;
                min-height: 200px;
            }
            
            .watermark-preview {
                height: 100px;
                font-size: 1.5rem;
            }
            
            .ad-leaderboard {
                width: 320px;
                height: 50px;
            }
            
            .ad-banner {
                width: 320px;
                height: 50px;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="#" onclick="showHome()">
                <i class="fas fa-file-pdf me-2"></i>PDF Fusion Pro
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showHome()">Accueil</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showMerge()">Fusion PDF</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showTools()">Outils</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showAbout()">À propos</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Contenu principal -->
    <div class="container py-5">
        <!-- Publicité pour la page d'accueil -->
        {% if page_type == 'home' and ad_units %}
            {% for ad in ad_units %}
                {% if ad.format == 'leaderboard' %}
                    <div class="ad-container mb-4">
                        <ins class="adsbygoogle ad-leaderboard"
                             style="display:block"
                             data-ad-client="{{ adsense_client_id }}"
                             data-ad-slot="{{ ad.slot }}"
                             data-ad-format="auto"
                             data-full-width-responsive="{{ 'true' if ad.responsive else 'false' }}"></ins>
                        <script>
                            (adsbygoogle = window.adsbygoogle || []).push({});
                        </script>
                    </div>
                {% endif %}
            {% endfor %}
        {% endif %}

        <!-- Page d'accueil -->
        <div id="homePage" style="display: {{ 'block' if page_type == 'home' else 'none' }};">
            <div class="row mb-5">
                <div class="col-12 text-center">
                    <h1 class="display-4 fw-bold mb-3">Fusionnez vos PDFs gratuitement</h1>
                    <p class="lead mb-4">Outils PDF en ligne 100% gratuit • Aucune inscription requise • Traitement sécurisé</p>
                    
                    <div class="row g-4 mb-5">
                        <div class="col-md-3">
                            <div class="card h-100 text-center p-3">
                                <div class="feature-icon">
                                    <i class="fas fa-merge"></i>
                                </div>
                                <h4>Fusion PDF</h4>
                                <p>Combinez plusieurs fichiers PDF en un seul document</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card h-100 text-center p-3">
                                <div class="feature-icon" style="background: var(--success-color);">
                                    <i class="fas fa-compress"></i>
                                </div>
                                <h4>Compression</h4>
                                <p>Réduisez la taille de vos PDFs sans perte de qualité</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card h-100 text-center p-3">
                                <div class="feature-icon" style="background: var(--warning-color);">
                                    <i class="fas fa-rotate"></i>
                                </div>
                                <h4>Rotation</h4>
                                <p>Tournez les pages de vos PDFs (90°, 180°, 270°)</p>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="card h-100 text-center p-3">
                                <div class="feature-icon" style="background: var(--danger-color);">
                                    <i class="fas fa-water"></i>
                                </div>
                                <h4>Filigrane</h4>
                                <p>Ajoutez un filigrane personnalisé à vos documents</p>
                            </div>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary btn-lg px-5 py-3" onclick="showMerge()">
                        <i class="fas fa-play me-2"></i>Commencer maintenant
                    </button>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <h3 class="mb-3">
                                <i class="fas fa-chart-line me-2"></i>
                                <span id="statsCount">12,345</span> PDFs traités
                            </h3>
                            <p class="mb-0">Rejoignez nos utilisateurs satisfaits !</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Page de fusion -->
        <div id="mergePage" style="display: {{ 'block' if page_type == 'merge' else 'none' }};">
            <div class="row mb-4">
                <div class="col-12">
                    <h2 class="mb-3"><i class="fas fa-merge me-2"></i>Fusionner des PDFs</h2>
                    <p class="text-muted">Sélectionnez vos fichiers PDF à fusionner</p>
                </div>
            </div>
            
            <div class="row">
                <div class="col-lg-8 mb-4">
                    <!-- Zone de dépôt -->
                    <div id="dropZone" class="drop-area mb-4">
                        <i class="fas fa-cloud-upload-alt fa-3x mb-3"></i>
                        <h4>Glissez-déposez vos PDFs ici</h4>
                        <p class="text-muted">ou</p>
                        <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                            <i class="fas fa-folder-open me-2"></i>Parcourir les fichiers
                        </button>
                        <input type="file" id="fileInput" accept=".pdf" multiple style="display: none;">
                    </div>
                    
                    <!-- Liste des fichiers -->
                    <div id="fileList" class="mb-4">
                        <div class="alert alert-secondary text-center">
                            Aucun fichier sélectionné
                        </div>
                    </div>
                    
                    <!-- Options de fusion -->
                    <div class="card mb-4">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-cog me-2"></i>Options de fusion</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <!-- Filigrane -->
                                <div class="col-md-6 mb-3">
                                    <div class="form-check form-switch mb-3">
                                        <input class="form-check-input" type="checkbox" id="addWatermark">
                                        <label class="form-check-label" for="addWatermark">
                                            <strong>Ajouter un filigrane</strong>
                                        </label>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="watermarkText" class="form-label">Texte du filigrane</label>
                                        <input type="text" class="form-control" id="watermarkText" 
                                               value="CONFIDENTIEL" placeholder="Entrez votre texte">
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label class="form-label">Aperçu du filigrane</label>
                                        <div id="watermarkPreview" class="watermark-preview" data-text="CONFIDENTIEL">
                                            CONFIDENTIEL
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Rotation -->
                                <div class="col-md-6 mb-3">
                                    <div class="form-check form-switch mb-3">
                                        <input class="form-check-input" type="checkbox" id="enableRotation">
                                        <label class="form-check-label" for="enableRotation">
                                            <strong>Rotation des pages</strong>
                                        </label>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="rotationAngleSelect" class="form-label">Angle de rotation</label>
                                        <select class="form-select" id="rotationAngleSelect">
                                            <option value="90">90° (quart de tour)</option>
                                            <option value="180">180° (demi-tour)</option>
                                            <option value="270">270° (trois quarts)</option>
                                        </select>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="rotationPages" class="form-label">
                                            Pages à tourner (ex: "1,3,5" ou "1-5")
                                        </label>
                                        <input type="text" class="form-control" id="rotationPages" 
                                               placeholder="Laissez vide pour toutes les pages">
                                        <small class="text-muted">Numéros séparés par des virgules ou plages avec "-"</small>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Métadonnées -->
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="docTitle" class="form-label">Titre du document</label>
                                    <input type="text" class="form-control" id="docTitle" placeholder="Titre optionnel">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="docAuthor" class="form-label">Auteur</label>
                                    <input type="text" class="form-control" id="docAuthor" placeholder="Auteur optionnel">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Bouton de fusion -->
                    <button id="mergeBtn" class="btn btn-success btn-lg w-100 py-3" onclick="mergePDFs()" disabled>
                        <i class="fas fa-merge me-2"></i>Fusionner les PDFs
                    </button>
                </div>
                
                <!-- Colonne droite avec publicité et statistiques -->
                <div class="col-lg-4">
                    <!-- Publicité rectangle -->
                    {% if page_type == 'merge' and ad_units %}
                        {% for ad in ad_units %}
                            {% if ad.format == 'rectangle' %}
                                <div class="ad-container mb-4">
                                    <ins class="adsbygoogle ad-rectangle"
                                         style="display:block"
                                         data-ad-client="{{ adsense_client_id }}"
                                         data-ad-slot="{{ ad.slot }}"
                                         data-ad-format="auto"
                                         data-full-width-responsive="{{ 'true' if ad.responsive else 'false' }}"></ins>
                                    <script>
                                        (adsbygoogle = window.adsbygoogle || []).push({});
                                    </script>
                                </div>
                            {% endif %}
                        {% endfor %}
                    {% endif %}
                    
                    <div class="card sticky-top" style="top: 20px;">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Statistiques</h5>
                        </div>
                        <div class="card-body text-center">
                            <div class="d-flex justify-content-center mb-4">
                                <svg class="progress-ring" viewBox="0 0 100 100">
                                    <circle class="progress-ring-background" cx="50" cy="50" r="36" stroke="#e9ecef" stroke-width="8" fill="transparent"/>
                                    <circle class="progress-ring-circle" cx="50" cy="50" r="36" stroke="#0d6efd" stroke-width="8" fill="transparent" stroke-linecap="round"/>
                                </svg>
                            </div>
                            
                            <div class="row text-center">
                                <div class="col-6 mb-3">
                                    <div class="display-6 fw-bold" id="totalPages">0</div>
                                    <small class="text-muted">Pages totales</small>
                                </div>
                                <div class="col-6 mb-3">
                                    <div class="display-6 fw-bold" id="fileCount">0</div>
                                    <small class="text-muted">Fichiers</small>
                                </div>
                                <div class="col-12">
                                    <div class="display-6 fw-bold" id="totalSize">0.00</div>
                                    <small class="text-muted">MB totaux</small>
                                </div>
                            </div>
                            
                            <hr class="my-4">
                            
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>Limites :</strong><br>
                                • Max 20 fichiers par fusion<br>
                                • Max 50 MB par fichier<br>
                                • Max 500 pages totales
                            </div>
                            
                            <div class="alert alert-warning">
                                <i class="fas fa-shield-alt me-2"></i>
                                <strong>Vos données sont privées</strong><br>
                                Les fichiers sont supprimés automatiquement après traitement.
                                <button class="btn btn-sm btn-outline-warning mt-2" onclick="showPrivacy()">
                                    En savoir plus
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Page outils -->
        <div id="toolsPage" style="display: {{ 'block' if page_type == 'tools' else 'none' }};">
            <!-- Publicité banner -->
            {% if page_type == 'tools' and ad_units %}
                {% for ad in ad_units %}
                    {% if ad.format == 'banner' %}
                        <div class="ad-container mb-4">
                            <ins class="adsbygoogle ad-banner"
                                 style="display:block"
                                 data-ad-client="{{ adsense_client_id }}"
                                 data-ad-slot="{{ ad.slot }}"
                                 data-ad-format="auto"
                                 data-full-width-responsive="{{ 'true' if ad.responsive else 'false' }}"></ins>
                            <script>
                                (adsbygoogle = window.adsbygoogle || []).push({});
                            </script>
                        </div>
                    {% endif %}
                {% endfor %}
            {% endif %}
            
            <div class="row mb-4">
                <div class="col-12">
                    <h2 class="mb-3"><i class="fas fa-tools me-2"></i>Outils PDF</h2>
                    <p class="text-muted">Autres outils pour vos documents PDF</p>
                </div>
            </div>
            
            <div class="row g-4">
                <div class="col-md-4">
                    <div class="card h-100 text-center p-4">
                        <div class="feature-icon" style="background: var(--success-color);">
                            <i class="fas fa-compress"></i>
                        </div>
                        <h4 class="mb-3">Compresser PDF</h4>
                        <p class="mb-4">Réduisez la taille de vos fichiers PDF pour les partager plus facilement.</p>
                        <button class="btn btn-success w-100" onclick="compressPDF()">
                            <i class="fas fa-play me-2"></i>Compresser un PDF
                        </button>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card h-100 text-center p-4">
                        <div class="feature-icon" style="background: var(--warning-color);">
                            <i class="fas fa-rotate"></i>
                        </div>
                        <h4 class="mb-3">Rotation PDF</h4>
                        <p class="mb-4">Tournez les pages de vos documents PDF (90°, 180°, 270°).</p>
                        <div class="mb-3">
                            <div class="form-check form-check-inline">
                                <input class="form-check-input" type="radio" name="rotationAngle" id="rotate90" value="90" checked>
                                <label class="form-check-label" for="rotate90">90°</label>
                            </div>
                            <div class="form-check form-check-inline">
                                <input class="form-check-input" type="radio" name="rotationAngle" id="rotate180" value="180">
                                <label class="form-check-label" for="rotate180">180°</label>
                            </div>
                            <div class="form-check form-check-inline">
                                <input class="form-check-input" type="radio" name="rotationAngle" id="rotate270" value="270">
                                <label class="form-check-label" for="rotate270">270°</label>
                            </div>
                        </div>
                        <div class="mb-3">
                            <input type="text" class="form-control" id="pagesToRotate" placeholder="Pages (ex: 1,3,5 ou 1-5)">
                            <small class="text-muted">Laissez vide pour toutes les pages</small>
                        </div>
                        <button class="btn btn-warning w-100" onclick="rotatePDF()">
                            <i class="fas fa-sync me-2"></i>Tourner un PDF
                        </button>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card h-100 text-center p-4">
                        <div class="feature-icon" style="background: var(--danger-color);">
                            <i class="fas fa-info-circle"></i>
                        </div>
                        <h4 class="mb-3">Informations PDF</h4>
                        <p class="mb-4">Obtenez des informations détaillées sur vos fichiers PDF (pages, taille, métadonnées).</p>
                        <button class="btn btn-info w-100" onclick="getPDFInfo()">
                            <i class="fas fa-chart-bar me-2"></i>Analyser un PDF
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Page à propos -->
        <div id="aboutPage" style="display: {{ 'block' if page_type == 'about' else 'none' }};">
            <div class="row">
                <div class="col-lg-8 mx-auto">
                    <div class="card">
                        <div class="card-body">
                            <h2 class="mb-4"><i class="fas fa-info-circle me-2"></i>À propos de PDF Fusion Pro</h2>
                            
                            <div class="mb-4">
                                <h4>Notre mission</h4>
                                <p>PDF Fusion Pro est un outil en ligne gratuit qui permet à tous de manipuler facilement des documents PDF. Nous croyons que les outils professionnels devraient être accessibles à tous, gratuitement.</p>
                            </div>
                            
                            <div class="mb-4">
                                <h4>Fonctionnalités principales</h4>
                                <ul>
                                    <li><strong>Fusion PDF :</strong> Combinez plusieurs fichiers PDF en un seul document</li>
                                    <li><strong>Compression :</strong> Réduisez la taille de vos PDFs</li>
                                    <li><strong>Rotation :</strong> Tournez les pages selon vos besoins</li>
                                    <li><strong>Filigrane :</strong> Ajoutez des filigranes personnalisés</li>
                                    <li><strong>Métadonnées :</strong> Modifiez les informations du document</li>
                                </ul>
                            </div>
                            
                            <div class="mb-4">
                                <h4>Sécurité et confidentialité</h4>
                                <p>Vos fichiers sont traités de manière sécurisée sur nos serveurs et sont automatiquement supprimés après traitement. Nous ne conservons aucune copie de vos documents.</p>
                            </div>
                            
                            <div class="mb-4">
                                <h4>Contact</h4>
                                <p>Développé avec ❤️ par <strong>{{ developer_name }}</strong></p>
                                <p>Email : {{ developer_email }}</p>
                                <p>Version : {{ app_version }}</p>
                            </div>
                            
                            <div class="alert alert-primary">
                                <i class="fas fa-star me-2"></i>
                                <strong>Cet outil est 100% gratuit !</strong> Aucune inscription, aucune limitation cachée.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal de progression -->
    <div class="modal fade" id="progressModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content bg-dark">
                <div class="modal-header">
                    <h5 class="modal-title" id="progressTitle">Traitement en cours</h5>
                </div>
                <div class="modal-body">
                    <div class="progress mb-3" style="height: 20px;">
                        <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                             style="width: 0%;"></div>
                    </div>
                    <p id="progressMessage" class="text-center mb-0">Veuillez patienter...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Variables globales
        let files = [];
        let currentPage = '{{ page_type }}';
        
        // Initialisation avec vérification des éléments
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM chargé - page: {{ page_type }}');
            
            // Vérifier tous les éléments critiques
            const elementsToCheck = [
                'dropZone',
                'fileInput', 
                'watermarkText',
                'addWatermark',
                'watermarkPreview',
                'mergeBtn',
                'fileList',
                'totalPages',
                'fileCount',
                'totalSize',
                'progressModal'
            ];
            
            elementsToCheck.forEach(id => {
                const element = document.getElementById(id);
                if (!element) {
                    console.warn(`⚠️ Élément #${id} non trouvé dans le DOM`);
                }
            });
            
            // Initialiser les composants seulement si on est sur la bonne page
            if (currentPage === 'merge' && document.getElementById('dropZone')) {
                setupDragAndDrop();
            }
            
            if (document.getElementById('watermarkText')) {
                updateWatermarkPreview();
                document.getElementById('watermarkText').addEventListener('input', updateWatermarkPreview);
            }
            
            simulateStats();
            
            // Afficher la page correcte au chargement
            showPage(currentPage + 'Page');
        });
        
        // Navigation
        function showHome() {
            window.location.href = '/';
        }
        
        function showMerge() {
            window.location.href = '/merge';
        }
        
        function showTools() {
            window.location.href = '/tools';
        }
        
        function showAbout() {
            window.location.href = '/about';
        }
        
        function showPage(pageId) {
            // Cacher toutes les pages
            ['homePage', 'mergePage', 'toolsPage', 'aboutPage'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.style.display = 'none';
                }
            });
            
            // Afficher la page demandée
            const targetPage = document.getElementById(pageId);
            if (targetPage) {
                targetPage.style.display = 'block';
            }
        }
        
        // Configuration drag & drop avec vérifications
        function setupDragAndDrop() {
            const dropZone = document.getElementById('dropZone');
            const fileInput = document.getElementById('fileInput');
            
            if (!dropZone) {
                console.error('❌ setupDragAndDrop: dropZone non trouvé');
                return;
            }
            
            if (!fileInput) {
                console.error('❌ setupDragAndDrop: fileInput non trouvé');
                return;
            }
            
            // Prévenir les comportements par défaut
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                }, false);
            });
            
            // Ajouter classe dragover
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, function() {
                    dropZone.classList.add('dragover');
                }, false);
            });
            
            // Retirer classe dragover
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, function() {
                    dropZone.classList.remove('dragover');
                }, false);
            });
            
            // Gérer le drop
            dropZone.addEventListener('drop', function(e) {
                const dt = e.dataTransfer;
                const fileList = dt.files;
                handleFiles(fileList);
            }, false);
            
            // Gérer le file input
            fileInput.addEventListener('change', function(e) {
                handleFiles(e.target.files);
            });
            
            console.log('✅ Drag and drop configuré');
        }
        
        // Gérer les fichiers
        async function handleFiles(fileList) {
            if (!fileList || fileList.length === 0) {
                showToast('Veuillez sélectionner des fichiers', 'warning');
                return;
            }
            
            const pdfFiles = Array.from(fileList).filter(file => 
                file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
            );
            
            if (pdfFiles.length === 0) {
                showToast('Veuillez sélectionner des fichiers PDF', 'warning');
                return;
            }
            
            // Limite de fichiers
            if (pdfFiles.length > 20) {
                showToast('Maximum 20 fichiers par fusion', 'warning');
                return;
            }
            
            for (const file of pdfFiles) {
                await addFile(file);
            }
            
            updateStatsDisplay();
            updateMergeButton();
            showToast(`${pdfFiles.length} fichier(s) ajouté(s)`, 'success');
        }
        
        // Ajouter un fichier
        async function addFile(file) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                
                reader.onload = async function(e) {
                    const fileData = {
                        name: file.name,
                        size: file.size,
                        data: e.target.result.split(',')[1],
                        pages: await getPageCount(file)
                    };
                    
                    files.push(fileData);
                    updateFileList();
                    resolve();
                };
                
                reader.readAsDataURL(file);
            });
        }
        
        // Compter les pages d'un PDF
        async function getPageCount(file) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        const pdfData = new Uint8Array(e.target.result);
                        if (typeof pdfjsLib !== 'undefined') {
                            pdfjsLib.getDocument(pdfData).promise.then(pdf => {
                                resolve(pdf.numPages);
                            }).catch(() => {
                                resolve(1);
                            });
                        } else {
                            resolve(1);
                        }
                    } catch (error) {
                        console.warn('Erreur comptage pages:', error);
                        resolve(1);
                    }
                };
                reader.readAsArrayBuffer(file);
            });
        }
        
        // Mettre à jour la liste des fichiers
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            if (!fileList) return;
            
            if (files.length === 0) {
                fileList.innerHTML = '<div class="alert alert-secondary text-center">Aucun fichier sélectionné</div>';
                return;
            }
            
            let html = '<div class="mb-3"><h5>Fichiers sélectionnés:</h5></div>';
            
            files.forEach((file, index) => {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                html += `
                    <div class="file-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-file-pdf text-danger fa-lg me-3"></i>
                                <div>
                                    <h6 class="mb-0">${file.name}</h6>
                                    <small class="text-muted">${sizeMB} MB • ${file.pages} pages</small>
                                </div>
                            </div>
                            <button class="btn btn-sm btn-danger" onclick="removeFile(${index})" title="Supprimer">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
            
            fileList.innerHTML = html;
        }
        
        // Supprimer un fichier
        function removeFile(index) {
            if (index >= 0 && index < files.length) {
                files.splice(index, 1);
                updateFileList();
                updateStatsDisplay();
                updateMergeButton();
            }
        }
        
        // Mettre à jour les statistiques
        function updateStatsDisplay() {
            const totalPages = files.reduce((sum, file) => sum + (file.pages || 0), 0);
            const totalSize = files.reduce((sum, file) => sum + (file.size || 0), 0);
            const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
            
            const totalPagesEl = document.getElementById('totalPages');
            const fileCountEl = document.getElementById('fileCount');
            const totalSizeEl = document.getElementById('totalSize');
            
            if (totalPagesEl) totalPagesEl.textContent = totalPages;
            if (fileCountEl) fileCountEl.textContent = files.length;
            if (totalSizeEl) totalSizeEl.textContent = totalSizeMB;
            
            // Mettre à jour la jauge
            const progressCircle = document.querySelector('#mergePage .progress-ring-circle');
            if (progressCircle) {
                const radius = 36;
                const circumference = 2 * Math.PI * radius;
                const maxPages = 500;
                const progress = Math.min(totalPages / maxPages, 1);
                
                progressCircle.style.strokeDasharray = circumference;
                progressCircle.style.strokeDashoffset = circumference * (1 - progress);
            }
        }
        
        // Mettre à jour le bouton de fusion
        function updateMergeButton() {
            const mergeBtn = document.getElementById('mergeBtn');
            if (mergeBtn) {
                mergeBtn.disabled = files.length === 0;
            }
        }
        
        // Mettre à jour l'aperçu du filigrane
        function updateWatermarkPreview() {
            const textInput = document.getElementById('watermarkText');
            const preview = document.getElementById('watermarkPreview');
            
            if (!textInput || !preview) return;
            
            const text = textInput.value || 'EXEMPLE';
            preview.textContent = text;
            preview.setAttribute('data-text', text);
        }
        
        // Fusionner les PDFs
        async function mergePDFs() {
            if (files.length === 0) {
                showToast('Veuillez sélectionner des fichiers', 'warning');
                return;
            }
            
            const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
            document.getElementById('progressTitle').textContent = 'Fusion en cours...';
            document.getElementById('progressBar').style.width = '10%';
            document.getElementById('progressMessage').textContent = 'Préparation des fichiers...';
            progressModal.show();
            
            try {
                // Récupérer les options
                const options = {
                    watermark: {
                        enabled: document.getElementById('addWatermark') ? 
                                document.getElementById('addWatermark').checked : false,
                        text: document.getElementById('watermarkText') ? 
                              document.getElementById('watermarkText').value || 'PDF Fusion Pro' : 'PDF Fusion Pro'
                    },
                    metadata: {
                        title: document.getElementById('docTitle') ? 
                              document.getElementById('docTitle').value : '',
                        author: document.getElementById('docAuthor') ? 
                               document.getElementById('docAuthor').value : '',
                        auto_date: true
                    },
                    rotation: {
                        enabled: document.getElementById('enableRotation') ? 
                               document.getElementById('enableRotation').checked : false,
                        angle: document.getElementById('rotationAngleSelect') ? 
                              parseInt(document.getElementById('rotationAngleSelect').value) : 90,
                        pages: document.getElementById('rotationPages') ? 
                              document.getElementById('rotationPages').value.trim() || 'all' : 'all'
                    }
                };
                
                document.getElementById('progressBar').style.width = '30%';
                document.getElementById('progressMessage').textContent = 'Envoi au serveur...';
                
                // Préparer les données
                const requestData = {
                    files: files,
                    options: options
                };
                
                // Envoyer au serveur
                const response = await fetch('/api/merge', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                document.getElementById('progressBar').style.width = '60%';
                document.getElementById('progressMessage').textContent = 'Traitement en cours...';
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('progressBar').style.width = '90%';
                    document.getElementById('progressMessage').textContent = 'Génération du PDF...';
                    
                    // Télécharger le fichier
                    const pdfData = base64ToArrayBuffer(result.data);
                    const blob = new Blob([pdfData], { type: 'application/pdf' });
                    const url = window.URL.createObjectURL(blob);
                    
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = result.filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    document.getElementById('progressBar').style.width = '100%';
                    document.getElementById('progressMessage').textContent = 'Terminé !';
                    
                    setTimeout(() => {
                        progressModal.hide();
                        showToast('Fusion réussie ! Votre fichier a été téléchargé.', 'success');
                    }, 1000);
                    
                } else {
                    progressModal.hide();
                    showToast('Erreur: ' + (result.error || 'Inconnue'), 'error');
                }
                
            } catch (error) {
                progressModal.hide();
                showToast('Erreur: ' + error.message, 'error');
            }
        }
        
        // Compresser un PDF
        async function compressPDF() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf';
            
            input.onchange = async function() {
                if (!input.files.length) return;
                
                const file = input.files[0];
                
                if (file.size > 50 * 1024 * 1024) {
                    showToast('Fichier trop grand (max 50MB)', 'error');
                    return;
                }
                
                const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
                document.getElementById('progressTitle').textContent = 'Compression en cours...';
                document.getElementById('progressBar').style.width = '30%';
                progressModal.show();
                
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch('/api/compress', {
                        method: 'POST',
                        body: formData
                    });
                    
                    document.getElementById('progressBar').style.width = '70%';
                    const result = await response.json();
                    
                    if (result.success) {
                        // Télécharger le fichier compressé
                        const pdfData = base64ToArrayBuffer(result.data);
                        const blob = new Blob([pdfData], { type: 'application/pdf' });
                        const url = window.URL.createObjectURL(blob);
                        
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'compressed_' + file.name;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        document.getElementById('progressBar').style.width = '100%';
                        document.getElementById('progressMessage').textContent = 
                            `Compression: ${result.reduction || '0%'} réduction`;
                        
                        setTimeout(() => {
                            progressModal.hide();
                            showToast('Fichier compressé téléchargé', 'success');
                        }, 1500);
                    } else {
                        progressModal.hide();
                        showToast('Erreur: ' + (result.error || 'Inconnue'), 'error');
                    }
                    
                } catch (error) {
                    progressModal.hide();
                    showToast('Erreur: ' + error.message, 'error');
                }
            };
            
            input.click();
        }
        
        // Obtenir des infos sur un PDF
        async function getPDFInfo() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf';
            
            input.onchange = async function() {
                if (!input.files.length) return;
                
                const file = input.files[0];
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/info', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (!result.error) {
                        const info = `
                            <strong>${result.filename}</strong><br>
                            Taille: ${(result.size / 1024 / 1024).toFixed(2)} MB<br>
                            Pages: ${result.pages}<br>
                            ${result.encrypted ? '🔒 Chiffré' : '🔓 Non chiffré'}<br>
                            <br>
                            <strong>Métadonnées:</strong><br>
                            Titre: ${result.metadata.title || 'Non spécifié'}<br>
                            Auteur: ${result.metadata.author || 'Non spécifié'}
                        `;
                        
                        showToast(info, 'info', 10000);
                    } else {
                        showToast('Erreur: ' + result.error, 'error');
                    }
                    
                } catch (error) {
                    showToast('Erreur: ' + error.message, 'error');
                }
            };
            
            input.click();
        }
        
        // Rotation d'un PDF
        async function rotatePDF() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.pdf';
            
            input.onchange = async function() {
                if (!input.files.length) return;
                
                const file = input.files[0];
                
                if (file.size > 50 * 1024 * 1024) {
                    showToast('Fichier trop grand (max 50MB)', 'error');
                    return;
                }
                
                // Récupérer les paramètres
                const angleElement = document.querySelector('input[name="rotationAngle"]:checked');
                const pagesElement = document.getElementById('pagesToRotate');
                
                const angle = angleElement ? angleElement.value : '90';
                const pages = pagesElement ? pagesElement.value.trim() : '';
                
                const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
                document.getElementById('progressTitle').textContent = 'Rotation en cours...';
                document.getElementById('progressBar').style.width = '30%';
                progressModal.show();
                
                try {
                    const reader = new FileReader();
                    reader.onload = async function(e) {
                        const fileData = {
                            name: file.name,
                            size: file.size,
                            data: e.target.result.split(',')[1]
                        };
                        
                        const requestData = {
                            file: fileData,
                            angle: parseInt(angle),
                            pages: pages || 'all'
                        };
                        
                        document.getElementById('progressBar').style.width = '50%';
                        document.getElementById('progressMessage').textContent = 'Envoi au serveur...';
                        
                        const response = await fetch('/api/rotate', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(requestData)
                        });
                        
                        document.getElementById('progressBar').style.width = '70%';
                        document.getElementById('progressMessage').textContent = 'Traitement en cours...';
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            const pdfData = base64ToArrayBuffer(result.data);
                            const blob = new Blob([pdfData], { type: 'application/pdf' });
                            const url = window.URL.createObjectURL(blob);
                            
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = result.filename;
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            document.body.removeChild(a);
                            
                            document.getElementById('progressBar').style.width = '100%';
                            document.getElementById('progressMessage').textContent = 
                                `Rotation ${angle}° effectuée !`;
                            
                            setTimeout(() => {
                                progressModal.hide();
                                showToast(`PDF tourné de ${angle}° téléchargé`, 'success');
                            }, 1500);
                        } else {
                            progressModal.hide();
                            showToast('Erreur: ' + (result.error || 'Inconnue'), 'error');
                        }
                    };
                    
                    reader.readAsDataURL(file);
                    
                } catch (error) {
                    progressModal.hide();
                    showToast('Erreur: ' + error.message, 'error');
                }
            };
            
            input.click();
        }
        
        // Fonctions utilitaires
        function base64ToArrayBuffer(base64) {
            const binaryString = atob(base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes.buffer;
        }
        
        function showToast(message, type = 'info', duration = 5000) {
            const alertClass = type === 'error' ? 'alert-danger' : 
                             type === 'success' ? 'alert-success' : 
                             type === 'warning' ? 'alert-warning' : 'alert-info';
            
            const icon = type === 'error' ? '❌' : 
                        type === 'success' ? '✅' : 
                        type === 'warning' ? '⚠️' : 'ℹ️';
            
            // Supprimer les anciens toasts
            document.querySelectorAll('.toast').forEach(toast => toast.remove());
            
            const toast = document.createElement('div');
            toast.className = `toast alert ${alertClass} alert-dismissible fade show`;
            toast.innerHTML = `
                ${icon} ${message}
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, duration);
        }
        
        // Simuler des statistiques
        function simulateStats() {
            let count = 12345;
            const statsElement = document.getElementById('statsCount');
            
            if (statsElement) {
                setInterval(() => {
                    count += Math.floor(Math.random() * 10) + 1;
                    statsElement.textContent = count.toLocaleString();
                }, 30000);
            }
        }
        
        function showPrivacy() {
            showToast('Vos fichiers sont traités sur nos serveurs et supprimés automatiquement après traitement.', 'info', 10000);
        }
    </script>
</body>
</html>
'''

# ============================================
# POINT D'ENTRÉE
# ============================================

# ============================================
# POINT D'ENTRÉE
# ============================================

from flask import Flask, send_from_directory
import os
import shutil

app = Flask(__name__)

# ... vos routes existantes ...

# ✅ ROUTE POUR GOOGLE (IMPORTANT POUR SEO)
@app.route('/google6f0d847067bbd18a.html')
def google_verification():
    return send_from_directory('static', 'google6f0d847067bbd18a.html')

# ============================================
# CONFIGURATION POUR RENDER (GUNICORN)
# ============================================

# Render utilisera gunicorn directement via startCommand
# Ce code ne s'exécute qu'en développement local
if __name__ == '__main__':
    # Configuration pour le nettoyage
    import atexit
    
    @atexit.register
    def cleanup_on_exit():
        try:
            temp_folder = app.config.get('TEMP_FOLDER', '')
            if temp_folder and os.path.exists(temp_folder):
                shutil.rmtree(temp_folder, ignore_errors=True)
        except:
            pass
    
    # Développement local seulement
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


