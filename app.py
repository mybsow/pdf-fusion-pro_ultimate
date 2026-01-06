# === PERSONNALISATION ===
DEVELOPER_NAME = "MBSOW"  # ← VOTRE NOM ICI
DEVELOPER_EMAIL = "banousow@gmail.com"  # ← VOTRE EMAIL
APP_VERSION = "3.1.0"  # Version mise à jour
# ========================

import os
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
from flask import Flask, render_template_string, request, jsonify, send_file, Response, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# PDF Processing
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, A3, legal, landscape
from reportlab.lib.units import inch

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
        
        # Retirer les doublons et trier
        return sorted(set(pages))
    
    def merge_pdfs(self, pdf_files, options=None):
        """Fusionner plusieurs PDFs"""
        if options is None:
            options = {}
        
        writer = PyPDF2.PdfWriter()
        watermark = options.get('watermark', {})
        metadata = options.get('metadata', {})
        
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
                
                for page in pdf_reader.pages:
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

# ⭐⭐ ROUTE DE VÉRIFICATION GOOGLE ⭐⭐
@app.route('/google6f0d847067bbd18a.html')
def google_verification():
    """Route de vérification Google Search Console"""
    return render_template_string('google-site-verification: google6f0d847067bbd18a.html')

# ⭐⭐ ROUTE SITEMAP (AJOUTEZ-MOI) ⭐⭐
@app.route('/sitemap.xml')
def sitemap():
    sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://pdf-fusion-pro-ultimate.onrender.com/</loc>
    <lastmod>2024-01-15</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://pdf-fusion-pro-ultimate.onrender.com/google6f0d847067bbd18a.html</loc>
    <lastmod>2024-01-15</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>'''
    return Response(sitemap_content, mimetype='application/xml')

@app.route('/')
def home():
    """Page d'accueil avec interface web"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health_check():
    """Endpoint de santé pour Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'PDF Fusion Pro',
        'version': APP_VERSION,
        'developer': DEVELOPER_NAME,
        'email': DEVELOPER_EMAIL,
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('RENDER', 'development')
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
            'count': len(uploaded_files),
            'developer': DEVELOPER_NAME
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
                'size': len(merged_pdf),
                'developer': DEVELOPER_NAME,
                'version': APP_VERSION
            })
        finally:
            processor.cleanup()
            
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
        pages = data.get('pages', 'all')  # 'all' ou chaîne comme "1,3,5" ou "1-5"
        
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
                'pages': pages,
                'developer': DEVELOPER_NAME
            })
        finally:
            processor.cleanup()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# TEMPLATE HTML AMÉLIORÉ
# ============================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Fusion Pro - Outil PDF 100% Gratuit</title>
    <meta name="description" content="Fusionnez, tournez, compressez et modifiez vos PDFs en ligne gratuitement. Outil PDF professionnel et sécurisé.">
    <meta name="google-site-verification" content="google6f0d847067bbd18a" />
    
    <!-- Bootstrap 5.3 Dark Theme -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary: #4361ee;
            --secondary: #3a0ca3;
            --accent: #4cc9f0;
            --success: #06d6a0;
            --danger: #ef476f;
            --warning: #ffd166;
            --dark: #1a1b2e;
            --light: #f8f9fa;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: var(--light);
            min-height: 100vh;
        }
        
        /* Header Navigation */
        .navbar {
            background: rgba(26, 27, 46, 0.95) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .nav-link {
            color: var(--light) !important;
            font-weight: 500;
            padding: 10px 20px !important;
            border-radius: 50px;
            margin: 0 5px;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover, .nav-link.active {
            background: rgba(67, 97, 238, 0.2);
            color: var(--accent) !important;
            transform: translateY(-2px);
        }
        
        /* Hero Section */
        .hero-section {
            background: linear-gradient(rgba(15, 12, 41, 0.9), rgba(15, 12, 41, 0.9)),
                        url('https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover;
            background-position: center;
            border-radius: 25px;
            padding: 80px 40px;
            margin-top: 30px;
            position: relative;
            overflow: hidden;
        }
        
        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(67, 97, 238, 0.1) 0%, transparent 70%);
            animation: pulse 15s infinite alternate;
        }
        
        @keyframes pulse {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(-25%, -25%) scale(1.2); }
        }
        
        /* Feature Cards */
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            height: 100%;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            border-color: var(--accent);
            box-shadow: 0 15px 30px rgba(67, 97, 238, 0.2);
        }
        
        .feature-icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 25px;
            color: white;
            font-size: 30px;
            box-shadow: 0 10px 20px rgba(67, 97, 238, 0.3);
        }
        
        .feature-card h4 {
            color: var(--accent);
            margin-bottom: 15px;
        }
        
        /* Main Content */
        .main-content {
            background: rgba(26, 27, 46, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 25px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        /* Drop Zone */
        .drop-zone {
            border: 3px dashed var(--primary);
            border-radius: 20px;
            padding: 60px 30px;
            text-align: center;
            background: rgba(67, 97, 238, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .drop-zone::before {
            content: '';
            position: absolute;
            top: -10px;
            left: -10px;
            right: -10px;
            bottom: -10px;
            background: linear-gradient(45deg, transparent, rgba(67, 97, 238, 0.1), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .drop-zone:hover::before {
            opacity: 1;
        }
        
        .drop-zone:hover, .drop-zone.dragover {
            background: rgba(67, 97, 238, 0.1);
            border-color: var(--accent);
            transform: translateY(-5px);
        }
        
        /* File Items */
        .file-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 5px solid var(--primary);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .file-item:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(10px);
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .file-icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--danger), var(--warning));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
        }
        
        /* Buttons */
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border: none;
            padding: 14px 35px;
            font-weight: 600;
            border-radius: 12px;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(67, 97, 238, 0.4);
        }
        
        .btn-accent {
            background: linear-gradient(135deg, var(--accent), #00b4d8);
            border: none;
            padding: 16px 45px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 15px;
            transition: all 0.3s ease;
        }
        
        .btn-accent:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(76, 201, 240, 0.4);
        }
        
        /* Tabs */
        .nav-tabs {
            border: none;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 5px;
        }
        
        .nav-tabs .nav-link {
            border: none;
            color: var(--light);
            border-radius: 10px;
            margin: 0 5px;
            padding: 12px 25px;
        }
        
        .nav-tabs .nav-link.active {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
        }
        
        /* Forms */
        .form-control, .form-select {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--light);
            border-radius: 10px;
            padding: 12px 20px;
            transition: all 0.3s ease;
        }
        
        .form-control:focus, .form-select:focus {
            background: rgba(255, 255, 255, 0.12);
            border-color: var(--accent);
            color: var(--light);
            box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.25);
        }
        
        /* Stats */
        .stat-card {
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.1), rgba(76, 201, 240, 0.1));
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(76, 201, 240, 0.2);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        /* Preview Box */
        .preview-box {
            height: 200px;
            border: 2px dashed rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }
        
        .watermark-preview {
            font-size: 48px;
            opacity: 0.3;
            transform: rotate(-45deg);
            color: rgba(255, 255, 255, 0.7);
            font-weight: bold;
        }
        
        /* Footer */
        .footer {
            background: rgba(15, 12, 41, 0.9);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px 0;
            margin-top: 80px;
        }
        
        .developer-badge {
            background: linear-gradient(135deg, rgba(67, 97, 238, 0.2), rgba(76, 201, 240, 0.2));
            border: 1px solid rgba(76, 201, 240, 0.3);
            border-radius: 50px;
            padding: 12px 30px;
            display: inline-flex;
            align-items: center;
            gap: 15px;
            backdrop-filter: blur(10px);
        }
        
        /* Toast Notifications */
        .toast {
            position: fixed;
            top: 100px;
            right: 30px;
            z-index: 9999;
            min-width: 300px;
            max-width: 350px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(26, 27, 46, 0.95);
            backdrop-filter: blur(10px);
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero-section {
                padding: 40px 20px;
                text-align: center;
            }
            
            .drop-zone {
                padding: 30px 15px;
            }
            
            .feature-card {
                margin-bottom: 20px;
            }
            
            .file-item {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
            
            .file-info {
                flex-direction: column;
                gap: 10px;
            }
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, var(--accent), var(--primary));
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="#">
                <i class="fas fa-file-pdf me-2" style="color: var(--accent);"></i>
                <span style="background: linear-gradient(135deg, var(--accent), var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    PDF Fusion Pro
                </span>
            </a>
            <div class="d-flex align-items-center">
                <button class="btn btn-outline-light btn-sm me-3" onclick="showAbout()">
                    <i class="fas fa-question-circle me-1"></i>Aide
                </button>
                <button class="btn btn-accent" onclick="showMerge()">
                    <i class="fas fa-play me-2"></i>Commencer
                </button>
            </div>
        </div>
    </nav>

    <!-- Contenu principal -->
    <div class="container py-5 mt-5">
        <!-- Hero Section -->
        <div class="hero-section mb-5">
            <div class="row align-items-center">
                <div class="col-lg-8">
                    <h1 class="display-4 fw-bold mb-4">
                        L'outil PDF ultime
                        <span style="background: linear-gradient(135deg, var(--accent), var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            100% gratuit
                        </span>
                    </h1>
                    <p class="lead mb-4">
                        Fusionnez, tournez, compressez et modifiez vos fichiers PDF en ligne.
                        Professionnel, sécurisé, sans publicité.
                    </p>
                    
                    <div class="d-flex gap-3 flex-wrap">
                        <button class="btn btn-accent" onclick="showMerge()">
                            <i class="fas fa-layer-group me-2"></i>Fusionner PDF
                        </button>
                        <button class="btn btn-outline-light" onclick="showTools()">
                            <i class="fas fa-tools me-2"></i>Voir tous les outils
                        </button>
                    </div>
                </div>
                
                <div class="col-lg-4 text-center">
                    <div class="stat-card mt-4 mt-lg-0">
                        <div class="stat-number" id="statsCount">12,457</div>
                        <p class="mb-0">PDFs traités aujourd'hui</p>
                        <small class="text-muted">Service 100% gratuit</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Fonctionnalités principales -->
        <div class="row mb-5">
            <div class="col-12 mb-4">
                <h2 class="text-center mb-5">Fonctionnalités principales</h2>
            </div>
            
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="feature-card" onclick="showMerge()">
                    <div class="feature-icon">
                        <i class="fas fa-layer-group"></i>
                    </div>
                    <h4>Fusion PDF</h4>
                    <p>Combinez plusieurs fichiers PDF en un seul document</p>
                    <ul class="list-unstyled text-muted small">
                        <li><i class="fas fa-check text-success me-2"></i>Illimité</li>
                        <li><i class="fas fa-check text-success me-2"></i>Ajout de filigrane</li>
                        <li><i class="fas fa-check text-success me-2"></i>Organisation flexible</li>
                    </ul>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="feature-card" onclick="showMerge()">
                    <div class="feature-icon">
                        <i class="fas fa-sync-alt"></i>
                    </div>
                    <h4>Rotation PDF</h4>
                    <p>Tournez des pages spécifiques ou tout le document</p>
                    <ul class="list-unstyled text-muted small">
                        <li><i class="fas fa-check text-success me-2"></i>90°, 180°, 270°</li>
                        <li><i class="fas fa-check text-success me-2"></i>Pages spécifiques</li>
                        <li><i class="fas fa-check text-success me-2"></i>Prévisualisation</li>
                    </ul>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="feature-card" onclick="showTools()">
                    <div class="feature-icon">
                        <i class="fas fa-compress-alt"></i>
                    </div>
                    <h4>Compression</h4>
                    <p>Réduisez la taille de vos PDFs sans perte de qualité</p>
                    <ul class="list-unstyled text-muted small">
                        <li><i class="fas fa-check text-success me-2"></i>Optimisation intelligente</li>
                        <li><i class="fas fa-check text-success me-2"></i>Jusqu'à 70% de réduction</li>
                        <li><i class="fas fa-check text-success me-2"></i>Qualité préservée</li>
                    </ul>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="feature-card" onclick="showTools()">
                    <div class="feature-icon">
                        <i class="fas fa-water"></i>
                    </div>
                    <h4>Filigrane</h4>
                    <p>Protégez vos documents avec des filigranes personnalisés</p>
                    <ul class="list-unstyled text-muted small">
                        <li><i class="fas fa-check text-success me-2"></i>Texte personnalisé</li>
                        <li><i class="fas fa-check text-success me-2"></i>Positionnement flexible</li>
                        <li><i class="fas fa-check text-success me-2"></i>Transparence ajustable</li>
                    </ul>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="feature-card" onclick="showTools()">
                    <div class="feature-icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <h4>Analyse PDF</h4>
                    <p>Obtenez des informations détaillées sur vos fichiers</p>
                    <ul class="list-unstyled text-muted small">
                        <li><i class="fas fa-check text-success me-2"></i>Nombre de pages</li>
                        <li><i class="fas fa-check text-success me-2"></i>Taille du fichier</li>
                        <li><i class="fas fa-check text-success me-2"></i>Métadonnées</li>
                    </ul>
                </div>
            </div>
            
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="feature-card" onclick="showAbout()">
                    <div class="feature-icon">
                        <i class="fas fa-shield-alt"></i>
                    </div>
                    <h4>Sécurité totale</h4>
                    <p>Vos fichiers sont traités de manière sécurisée</p>
                    <ul class="list-unstyled text-muted small">
                        <li><i class="fas fa-check text-success me-2"></i>Suppression automatique</li>
                        <li><i class="fas fa-check text-success me-2"></i>HTTPS sécurisé</li>
                        <li><i class="fas fa-check text-success me-2"></i>Données privées</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Interface principale de traitement -->
        <div id="mainInterface" class="main-content p-4 p-md-5">
            <!-- Onglets -->
            <ul class="nav nav-tabs mb-4" id="mainTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="merge-tab" data-bs-toggle="tab" 
                            data-bs-target="#merge" type="button" role="tab">
                        <i class="fas fa-layer-group me-2"></i>Fusion
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="rotate-tab" data-bs-toggle="tab" 
                            data-bs-target="#rotate" type="button" role="tab">
                        <i class="fas fa-sync-alt me-2"></i>Rotation
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="tools-tab" data-bs-toggle="tab" 
                            data-bs-target="#tools" type="button" role="tab">
                        <i class="fas fa-tools me-2"></i>Outils
                    </button>
                </li>
            </ul>

            <!-- Contenu des onglets -->
            <div class="tab-content">
                <!-- Onglet Fusion -->
                <div class="tab-pane fade show active" id="merge" role="tabpanel">
                    <div class="row">
                        <div class="col-lg-8">
                            <div class="drop-zone mb-4" id="dropZone" onclick="document.getElementById('fileInput').click()">
                                <i class="fas fa-cloud-upload-alt fa-4x mb-3" style="color: var(--accent);"></i>
                                <h4>Glissez-déposez vos fichiers PDF ici</h4>
                                <p class="text-muted mb-3">ou cliquez pour parcourir vos fichiers</p>
                                <input type="file" id="fileInput" class="d-none" multiple accept=".pdf">
                                <div class="mt-3">
                                    <span class="badge bg-primary me-2">PDF uniquement</span>
                                    <span class="badge bg-success">Max 50MB par fichier</span>
                                    <span class="badge bg-info">Jusqu'à 20 fichiers</span>
                                </div>
                            </div>
                            
                            <div id="fileList" class="mb-4"></div>
                            
                            <div class="card bg-transparent border-secondary mb-4">
                                <div class="card-header" style="background: rgba(255,255,255,0.05);">
                                    <h5 class="mb-0"><i class="fas fa-cog me-2"></i>Options de fusion</h5>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <div class="form-check form-switch">
                                                <input class="form-check-input" type="checkbox" id="addWatermark" style="width: 3em; height: 1.5em;">
                                                <label class="form-check-label" for="addWatermark">
                                                    Ajouter un filigrane
                                                </label>
                                            </div>
                                            <div class="mt-3">
                                                <label class="form-label">Texte du filigrane</label>
                                                <input type="text" class="form-control" id="watermarkText" placeholder="EXEMPLE">
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">Métadonnées du document</label>
                                                <input type="text" class="form-control mb-2" id="docTitle" placeholder="Titre du document">
                                                <input type="text" class="form-control" id="docAuthor" placeholder="Auteur">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-lg-4">
                            <div class="sticky-top" style="top: 100px;">
                                <div class="stat-card mb-4">
                                    <h5 class="mb-3"><i class="fas fa-chart-bar me-2"></i>Résumé</h5>
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Fichiers:</span>
                                        <strong id="fileCount">0</strong>
                                    </div>
                                    <div class="d-flex justify-content-between mb-2">
                                        <span>Pages totales:</span>
                                        <strong id="totalPages">0</strong>
                                    </div>
                                    <div class="d-flex justify-content-between mb-3">
                                        <span>Taille totale:</span>
                                        <strong id="totalSize">0 MB</strong>
                                    </div>
                                    <button class="btn btn-accent w-100 py-3" id="mergeBtn" onclick="mergePDFs()" disabled>
                                        <i class="fas fa-rocket me-2"></i>Fusionner maintenant
                                    </button>
                                </div>
                                
                                <div class="card bg-transparent border-warning mb-4">
                                    <div class="card-header" style="background: rgba(255, 209, 102, 0.1);">
                                        <h5 class="mb-0"><i class="fas fa-eye me-2"></i>Aperçu filigrane</h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="preview-box mb-3">
                                            <div id="watermarkPreview" class="watermark-preview">EXEMPLE</div>
                                        </div>
                                        <button class="btn btn-outline-warning w-100" onclick="updateWatermarkPreview()">
                                            <i class="fas fa-sync me-2"></i>Actualiser l'aperçu
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Onglet Rotation -->
                <div class="tab-pane fade" id="rotate" role="tabpanel">
                    <div class="row align-items-center">
                        <div class="col-lg-6">
                            <h4 class="mb-4"><i class="fas fa-sync-alt me-2"></i>Rotation de PDF</h4>
                            <p class="text-muted mb-4">
                                Tournez des pages spécifiques ou l'ensemble de votre document PDF.
                                Sélectionnez l'angle et les pages à modifier.
                            </p>
                            
                            <div class="mb-4">
                                <label class="form-label mb-3">Angle de rotation:</label>
                                <div class="btn-group w-100" role="group">
                                    <input type="radio" class="btn-check" name="rotationAngle" id="rotate90" value="90" checked>
                                    <label class="btn btn-outline-primary" for="rotate90">
                                        <i class="fas fa-redo me-1"></i>90°
                                    </label>
                                    
                                    <input type="radio" class="btn-check" name="rotationAngle" id="rotate180" value="180">
                                    <label class="btn btn-outline-primary" for="rotate180">
                                        <i class="fas fa-undo-alt me-1"></i>180°
                                    </label>
                                    
                                    <input type="radio" class="btn-check" name="rotationAngle" id="rotate270" value="270">
                                    <label class="btn btn-outline-primary" for="rotate270">
                                        <i class="fas fa-redo-alt me-1"></i>270°
                                    </label>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label class="form-label">Pages à tourner:</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="pagesToRotate" 
                                           placeholder="Toutes les pages (ou ex: 1,3,5 ou 2-5)">
                                    <span class="input-group-text bg-transparent border-secondary">
                                        <i class="fas fa-info-circle" 
                                           title="Exemples: '1,3,5' pour les pages 1,3,5 - '2-5' pour les pages 2 à 5"></i>
                                    </span>
                                </div>
                                <small class="text-muted">Laissez vide pour toutes les pages</small>
                            </div>
                            
                            <div class="mb-4">
                                <label class="form-label">Sélectionnez votre PDF:</label>
                                <div class="drop-zone-sm" onclick="document.getElementById('rotateInput').click()" 
                                     style="padding: 30px; cursor: pointer;">
                                    <i class="fas fa-file-pdf fa-3x mb-3" style="color: var(--danger);"></i>
                                    <p class="mb-0">Cliquez pour sélectionner un PDF</p>
                                </div>
                                <input type="file" id="rotateInput" class="d-none" accept=".pdf">
                            </div>
                            
                            <button class="btn btn-warning btn-lg w-100 py-3" onclick="rotatePDF()">
                                <i class="fas fa-sync-alt me-2"></i>Tourner le PDF
                            </button>
                        </div>
                        
                        <div class="col-lg-6 text-center">
                            <div class="rotation-visual mb-4">
                                <div class="position-relative" style="width: 200px; height: 280px; margin: 0 auto;">
                                    <div class="position-absolute" style="width: 100%; height: 100%; background: rgba(67, 97, 238, 0.1); border-radius: 10px; border: 2px dashed var(--primary);"></div>
                                    <div id="rotationDemo" class="position-absolute" style="width: 100%; height: 100%; background: linear-gradient(135deg, var(--primary), var(--secondary)); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; transition: transform 0.5s ease;">
                                        PDF
                                    </div>
                                </div>
                            </div>
                            <p class="text-muted">Prévisualisation de la rotation</p>
                        </div>
                    </div>
                </div>

                <!-- Onglet Outils -->
                <div class="tab-pane fade" id="tools" role="tabpanel">
                    <h4 class="mb-4"><i class="fas fa-tools me-2"></i>Outils PDF avancés</h4>
                    
                    <div class="row">
                        <div class="col-md-6 mb-4">
                            <div class="card bg-transparent border-secondary h-100">
                                <div class="card-body text-center p-4">
                                    <div class="feature-icon mb-3">
                                        <i class="fas fa-compress-alt"></i>
                                    </div>
                                    <h4>Compresser PDF</h4>
                                    <p class="text-muted mb-4">Réduisez la taille de vos fichiers PDF</p>
                                    <input type="file" id="compressInput" class="d-none" accept=".pdf">
                                    <button class="btn btn-primary btn-lg" onclick="compressPDF()">
                                        <i class="fas fa-file-upload me-2"></i>Choisir un fichier
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-6 mb-4">
                            <div class="card bg-transparent border-secondary h-100">
                                <div class="card-body text-center p-4">
                                    <div class="feature-icon mb-3">
                                        <i class="fas fa-info-circle"></i>
                                    </div>
                                    <h4>Informations PDF</h4>
                                    <p class="text-muted mb-4">Obtenez des détails sur vos fichiers PDF</p>
                                    <input type="file" id="infoInput" class="d-none" accept=".pdf">
                                    <button class="btn btn-info btn-lg" onclick="getPDFInfo()">
                                        <i class="fas fa-search me-2"></i>Analyser un PDF
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-6 mb-4 mb-md-0">
                    <div class="developer-badge">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-user-tie fa-lg"></i>
                            <div class="ms-3">
                                <h6 class="mb-0" style="color: var(--accent);">Développeur</h6>
                                <p class="mb-0">{{ DEVELOPER_NAME }}</p>
                                <a href="mailto:{{ DEVELOPER_EMAIL }}" class="text-light small">{{ DEVELOPER_EMAIL }}</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 text-md-end">
                    <p class="mb-2">
                        <i class="fas fa-code me-1"></i>PDF Fusion Pro Ultimate v{{ APP_VERSION }}
                    </p>
                    <p class="text-muted small mb-0">
                        © 2025 • Service 100% gratuit • Hébergé sur Render.com
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <!-- Modal de progression -->
    <div class="modal fade" id="progressModal" tabindex="-1" data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="background: rgba(26, 27, 46, 0.95); backdrop-filter: blur(10px);">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title"><i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours</h5>
                </div>
                <div class="modal-body text-center py-4">
                    <div class="spinner-border" style="width: 3rem; height: 3rem; color: var(--accent);"></div>
                    <h5 class="mt-3" id="progressTitle">Fusion des PDFs...</h5>
                    <p id="progressMessage" class="text-muted">Veuillez patienter</p>
                    <div class="progress bg-secondary mt-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             id="progressBar" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Variables globales
        let files = [];
        
        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            setupDragAndDrop();
            updateWatermarkPreview();
            updateRotationDemo();
            
            // Événements
            document.getElementById('watermarkText').addEventListener('input', updateWatermarkPreview);
            document.querySelectorAll('input[name="rotationAngle"]').forEach(radio => {
                radio.addEventListener('change', updateRotationDemo);
            });
            
            // Simuler les statistiques
            simulateStats();
        });
        
        // Navigation simplifiée
        function showMerge() {
            document.getElementById('merge-tab').click();
        }
        
        function showTools() {
            document.getElementById('tools-tab').click();
        }
        
        function showAbout() {
            showToast('<h6>À propos de PDF Fusion Pro</h6><p>Service PDF 100% gratuit développé par ' + 
                     DEVELOPER_NAME + '.</p><p>Email: <a href="mailto:' + DEVELOPER_EMAIL + '">' + 
                     DEVELOPER_EMAIL + '</a></p>', 'info', 10000);
        }
        
        // Configuration drag & drop
        function setupDragAndDrop() {
            const dropZone = document.getElementById('dropZone');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => {
                    dropZone.classList.add('dragover');
                });
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => {
                    dropZone.classList.remove('dragover');
                });
            });
            
            dropZone.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const fileList = dt.files;
                handleFiles(fileList);
            }
            
            // Gestion du file input
            document.getElementById('fileInput').addEventListener('change', function(e) {
                handleFiles(e.target.files);
            });
        }
        
        // Gérer les fichiers
        async function handleFiles(fileList) {
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
                try {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        // Simple estimation basée sur la taille
                        // Dans une vraie application, utiliser pdf.js
                        const pageEstimate = Math.max(1, Math.floor(file.size / (100 * 1024)));
                        resolve(pageEstimate);
                    };
                    reader.readAsArrayBuffer(file);
                } catch {
                    resolve(1);
                }
            });
        }
        
        // Mettre à jour la liste des fichiers
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            
            if (files.length === 0) {
                fileList.innerHTML = '<div class="alert alert-secondary text-center">Aucun fichier sélectionné</div>';
                return;
            }
            
            let html = '<div class="mb-3"><h5>Fichiers sélectionnés:</h5></div>';
            
            files.forEach((file, index) => {
                const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                html += `
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-icon">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div>
                                <h6 class="mb-0">${file.name}</h6>
                                <small class="text-muted">${sizeMB} MB • ${file.pages} pages</small>
                            </div>
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="removeFile(${index})" title="Supprimer">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
            });
            
            fileList.innerHTML = html;
        }
        
        // Supprimer un fichier
        function removeFile(index) {
            files.splice(index, 1);
            updateFileList();
            updateStatsDisplay();
            updateMergeButton();
        }
        
        // Mettre à jour les statistiques
        function updateStatsDisplay() {
            const totalPages = files.reduce((sum, file) => sum + file.pages, 0);
            const totalSize = files.reduce((sum, file) => sum + file.size, 0);
            const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
            
            document.getElementById('totalPages').textContent = totalPages;
            document.getElementById('fileCount').textContent = files.length;
            document.getElementById('totalSize').textContent = totalSizeMB + ' MB';
        }
        
        // Mettre à jour le bouton de fusion
        function updateMergeButton() {
            document.getElementById('mergeBtn').disabled = files.length === 0;
        }
        
        // Mettre à jour l'aperçu du filigrane
        function updateWatermarkPreview() {
            const text = document.getElementById('watermarkText').value || 'EXEMPLE';
            const preview = document.getElementById('watermarkPreview');
            preview.textContent = text;
        }
        
        // Mettre à jour la démo de rotation
        function updateRotationDemo() {
            const angle = document.querySelector('input[name="rotationAngle"]:checked').value;
            const demo = document.getElementById('rotationDemo');
            demo.style.transform = `rotate(${angle}deg)`;
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
            progressModal.show();
            
            try {
                // Options
                const options = {
                    watermark: {
                        enabled: document.getElementById('addWatermark').checked,
                        text: document.getElementById('watermarkText').value || 'PDF Fusion Pro'
                    },
                    metadata: {
                        title: document.getElementById('docTitle').value || '',
                        author: document.getElementById('docAuthor').value || '',
                        auto_date: true
                    }
                };
                
                document.getElementById('progressBar').style.width = '30%';
                
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
                
                document.getElementById('progressBar').style.width = '70%';
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('progressBar').style.width = '100%';
                    
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
                    
                    setTimeout(() => {
                        progressModal.hide();
                        showToast('Fusion réussie ! Votre fichier a été téléchargé.', 'success');
                    }, 1000);
                    
                } else {
                    progressModal.hide();
                    showToast('Erreur: ' + result.error, 'error');
                }
                
            } catch (error) {
                progressModal.hide();
                showToast('Erreur: ' + error.message, 'error');
            }
        }
        
        // Rotation de PDF
        async function rotatePDF() {
            const input = document.getElementById('rotateInput');
            
            if (input.files.length === 0) {
                showToast('Veuillez sélectionner un fichier PDF', 'warning');
                return;
            }
            
            const file = input.files[0];
            
            // Vérifier la taille
            if (file.size > 50 * 1024 * 1024) {
                showToast('Fichier trop grand (max 50MB)', 'error');
                return;
            }
            
            // Récupérer les paramètres
            const angle = document.querySelector('input[name="rotationAngle"]:checked').value;
            const pages = document.getElementById('pagesToRotate').value || 'all';
            
            const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
            document.getElementById('progressTitle').textContent = 'Rotation en cours...';
            document.getElementById('progressBar').style.width = '30%';
            progressModal.show();
            
            try {
                // Lire le fichier
                const reader = new FileReader();
                reader.onload = async function(e) {
                    const fileData = {
                        name: file.name,
                        size: file.size,
                        data: e.target.result.split(',')[1]
                    };
                    
                    // Envoyer au serveur
                    const requestData = {
                        file: fileData,
                        angle: parseInt(angle),
                        pages: pages
                    };
                    
                    document.getElementById('progressBar').style.width = '60%';
                    
                    const response = await fetch('/api/rotate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestData)
                    });
                    
                    document.getElementById('progressBar').style.width = '90%';
                    const result = await response.json();
                    
                    if (result.success) {
                        // Télécharger le fichier tourné
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
                        
                        setTimeout(() => {
                            progressModal.hide();
                            showToast(`Rotation réussie ! Fichier tourné de ${angle}°`, 'success');
                        }, 1000);
                        
                    } else {
                        progressModal.hide();
                        showToast('Erreur: ' + result.error, 'error');
                    }
                };
                reader.readAsDataURL(file);
                
            } catch (error) {
                progressModal.hide();
                showToast('Erreur: ' + error.message, 'error');
            }
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
            
            const toast = document.createElement('div');
            toast.className = `toast alert ${alertClass} alert-dismissible fade show`;
            toast.innerHTML = message + 
                '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>';
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, duration);
        }
        
        // Simuler des statistiques
        function simulateStats() {
            let count = 12457;
            const statsElement = document.getElementById('statsCount');
            
            setInterval(() => {
                count += Math.floor(Math.random() * 10) + 1;
                statsElement.textContent = count.toLocaleString();
            }, 30000);
        }
        
        // Variables globales côté client
        const DEVELOPER_NAME = "{{ DEVELOPER_NAME }}";
        const DEVELOPER_EMAIL = "{{ DEVELOPER_EMAIL }}";
        const APP_VERSION = "{{ APP_VERSION }}";
    </script>
</body>
</html>
'''

# Variables pour le template
HTML_TEMPLATE = HTML_TEMPLATE.replace('{{ DEVELOPER_NAME }}', DEVELOPER_NAME)\
                             .replace('{{ DEVELOPER_EMAIL }}', DEVELOPER_EMAIL)\
                             .replace('{{ APP_VERSION }}', APP_VERSION)

# ============================================
# POINT D'ENTRÉE
# ============================================

if __name__ == '__main__':
    # Nettoyage à la fermeture
    import atexit
    @atexit.register
    def cleanup_on_exit():
        try:
            if os.path.exists(app.config['TEMP_FOLDER']):
                shutil.rmtree(app.config['TEMP_FOLDER'], ignore_errors=True)
        except:
            pass
    
    # Démarrer le serveur
    port = int(os.environ.get('PORT', 5000))
    
    # Utiliser waitress pour la production
    if os.environ.get('RENDER'):
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
