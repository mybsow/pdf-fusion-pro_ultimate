# === PERSONNALISATION ===
DEVELOPER_NAME = "MBSOW"
DEVELOPER_EMAIL = "banousow@gmail.com"
APP_VERSION = "3.1.0"
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
from flask import Flask, render_template_string, request, jsonify, Response
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

# PDF Processing
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# ============================================
# CONFIGURATION RENDER.COM
# ============================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4()))

# Proxy fix pour Render
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Configuration des limites
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max par fichier
app.config['UPLOAD_FOLDER'] = '/tmp'
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
        except Exception as e:
            app.logger.error(f"Erreur nettoyage: {e}")
    
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
                # C'est une plage
                try:
                    start, end = part.split("-")
                    start = int(start) - 1
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
                    page_num = int(part) - 1
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

@app.route('/google6f0d847067bbd18a.html')
def google_verification():
    """Route de vérification Google Search Console"""
    return render_template_string('google-site-verification: google6f0d847067bbd18a.html')

@app.route('/sitemap.xml')
def sitemap():
    """Sitemap pour SEO"""
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
    template = HTML_TEMPLATE.replace('{{ DEVELOPER_NAME }}', DEVELOPER_NAME)\
                           .replace('{{ DEVELOPER_EMAIL }}', DEVELOPER_EMAIL)\
                           .replace('{{ APP_VERSION }}', APP_VERSION)
    return render_template_string(template)

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
        app.logger.error(f"Erreur upload: {e}")
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
        app.logger.error(f"Erreur merge: {e}")
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
        
        # Récupérer les paramètres
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
                'pages': pages,
                'developer': DEVELOPER_NAME
            })
        finally:
            processor.cleanup()
            
    except Exception as e:
        app.logger.error(f"Erreur rotate: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# TEMPLATE HTML (version abrégée pour l'exemple)
# Note: Le template complet est trop long pour être inclus ici
# mais vous pouvez le garder séparé ou dans une variable
# ============================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="fr" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Fusion Pro - Outil PDF 100% Gratuit</title>
    <!-- ... reste du template HTML ... -->
</body>
</html>'''

# Note: Pour économiser de l'espace, je ne répète pas tout le HTML ici
# mais assurez-vous qu'il est complet dans votre fichier

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
        except Exception as e:
            print(f"Erreur lors du nettoyage final: {e}")
    
    # Démarrer le serveur
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
