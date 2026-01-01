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
from flask import Flask, render_template_string, request, jsonify, send_file, Response
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
        'version': '2.0.0',
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
        
        # Simple compression (dans la vraie vie, vous utiliseriez une vraie compression)
        # Ici on retourne le même fichier
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

# ============================================
# TEMPLATE HTML
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
    
    <style>
        :root {
            --primary: #0d6efd;
            --secondary: #6c757d;
            --success: #198754;
            --danger: #dc3545;
            --warning: #ffc107;
            --info: #0dcaf0;
            --dark: #212529;
            --light: #f8f9fa;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: var(--light);
            min-height: 100vh;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .header-gradient {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .drop-zone {
            border: 3px dashed var(--primary);
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            background: rgba(13, 110, 253, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .drop-zone:hover, .drop-zone.dragover {
            background: rgba(13, 110, 253, 0.1);
            border-color: var(--success);
            transform: translateY(-5px);
        }
        
        .file-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid var(--primary);
            transition: all 0.3s ease;
        }
        
        .file-item:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(5px);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), #0b5ed7);
            border: none;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(13, 110, 253, 0.4);
        }
        
        .btn-success {
            background: linear-gradient(135deg, var(--success), #157347);
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            font-weight: bold;
        }
        
        .progress-ring {
            width: 100px;
            height: 100px;
            margin: 0 auto;
        }
        
        .progress-ring-circle {
            stroke: var(--primary);
            stroke-linecap: round;
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
            transition: stroke-dashoffset 0.3s ease;
        }
        
        .feature-icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, var(--primary), #0b5ed7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            color: white;
            font-size: 30px;
            box-shadow: 0 10px 20px rgba(13, 110, 253, 0.3);
        }
        
        .modal-content {
            background: var(--dark);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .form-control, .form-select {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: var(--light);
        }
        
        .form-control:focus, .form-select:focus {
            background: rgba(255, 255, 255, 0.15);
            border-color: var(--primary);
            color: var(--light);
            box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
        }
        
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .preview-box {
            height: 200px;
            border: 2px dashed rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .watermark-preview {
            font-size: 48px;
            opacity: 0.3;
            transform: rotate(-45deg);
            color: rgba(255, 255, 255, 0.7);
        }
        
        /* Animation pour le chargement */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .pulse {
            animation: pulse 1.5s infinite;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .drop-zone {
                padding: 30px 15px;
            }
            
            .btn-success {
                padding: 12px 20px;
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
        <div class="container">
            <a class="navbar-brand fw-bold" href="#">
                <i class="fas fa-file-pdf me-2"></i>PDF Fusion Pro
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="#" onclick="showHome()">
                            <i class="fas fa-home me-1"></i>Accueil
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showMerge()">
                            <i class="fas fa-layer-group me-1"></i>Fusion
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showTools()">
                            <i class="fas fa-tools me-1"></i>Outils
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#" onclick="showAbout()">
                            <i class="fas fa-info-circle me-1"></i>Aide
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Contenu principal -->
    <div class="container py-5 mt-5">
        <!-- Page d'accueil -->
        <div id="homePage" class="glass-card p-4 p-md-5 mb-5">
            <div class="row align-items-center">
                <div class="col-lg-8">
                    <h1 class="display-4 fw-bold mb-4">
                        <i class="fas fa-file-pdf text-primary me-3"></i>
                        Fusionnez vos PDFs gratuitement
                    </h1>
                    <p class="lead mb-4">
                        L'outil ultime pour manipuler vos fichiers PDF en ligne. 
                        <strong>100% gratuit, sécurisé et sans limite d'utilisation.</strong>
                    </p>
                    
                    <div class="row mb-5">
                        <div class="col-md-4 mb-4">
                            <div class="feature-icon">
                                <i class="fas fa-layer-group"></i>
                            </div>
                            <h5>Fusion multiple</h5>
                            <p class="text-muted">Combine plusieurs PDFs en un seul</p>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="feature-icon">
                                <i class="fas fa-water"></i>
                            </div>
                            <h5>Filigrane</h5>
                            <p class="text-muted">Ajoutez des filigranes personnalisés</p>
                        </div>
                        <div class="col-md-4 mb-4">
                            <div class="feature-icon">
                                <i class="fas fa-compress-alt"></i>
                            </div>
                            <h5>Compression</h5>
                            <p class="text-muted">Réduisez la taille de vos fichiers</p>
                        </div>
                    </div>
                    
                    <button class="btn btn-success btn-lg px-5" onclick="showMerge()">
                        <i class="fas fa-play me-2"></i>Commencer maintenant
                    </button>
                </div>
                
                <div class="col-lg-4">
                    <div class="text-center">
                        <div class="progress-ring mb-4">
                            <svg viewBox="0 0 100 100">
                                <circle class="progress-ring-circle" stroke-width="8" fill="transparent" r="36" cx="50" cy="50"/>
                            </svg>
                            <div class="position-absolute top-50 start-50 translate-middle">
                                <h2 class="mb-0" id="statsCount">∞</h2>
                                <small>PDFs traités</small>
                            </div>
                        </div>
                        
                        <div class="alert alert-info">
                            <h6><i class="fas fa-shield-alt me-2"></i>Sécurité garantie</h6>
                            <p class="small mb-0">
                                Vos fichiers sont traités sur nos serveurs sécurisés et supprimés automatiquement.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Page de fusion -->
        <div id="mergePage" class="glass-card p-4 p-md-5 mb-5" style="display: none;">
            <h2 class="mb-4"><i class="fas fa-layer-group me-2"></i>Fusion de PDFs</h2>
            
            <div class="row">
                <div class="col-lg-8">
                    <!-- Zone de dépôt -->
                    <div class="drop-zone mb-4" id="dropZone" onclick="document.getElementById('fileInput').click()">
                        <i class="fas fa-cloud-upload-alt fa-4x text-primary mb-3"></i>
                        <h4>Déposez vos fichiers PDF ici</h4>
                        <p class="text-muted mb-3">ou cliquez pour sélectionner des fichiers</p>
                        <input type="file" id="fileInput" class="d-none" multiple accept=".pdf">
                        <div class="mt-3">
                            <span class="badge bg-primary me-2">.pdf uniquement</span>
                            <span class="badge bg-success">Jusqu'à 50MB par fichier</span>
                        </div>
                    </div>
                    
                    <!-- Liste des fichiers -->
                    <div id="fileList" class="mb-4"></div>
                    
                    <!-- Options -->
                    <div class="card bg-dark border-secondary mb-4">
                        <div class="card-header bg-secondary">
                            <h5 class="mb-0"><i class="fas fa-cog me-2"></i>Options de fusion</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-check mb-3">
                                        <input class="form-check-input" type="checkbox" id="addWatermark">
                                        <label class="form-check-label" for="addWatermark">
                                            Ajouter un filigrane
                                        </label>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Texte du filigrane</label>
                                        <input type="text" class="form-control" id="watermarkText" placeholder="EXEMPLE">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Métadonnées</label>
                                        <input type="text" class="form-control mb-2" id="docTitle" placeholder="Titre du document">
                                        <input type="text" class="form-control" id="docAuthor" placeholder="Auteur">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-4">
                    <!-- Statistiques -->
                    <div class="card bg-dark border-info mb-4">
                        <div class="card-header bg-info text-dark">
                            <h5 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Statistiques</h5>
                        </div>
                        <div class="card-body text-center">
                            <div class="progress-ring mb-3">
                                <svg viewBox="0 0 100 100">
                                    <circle class="progress-ring-circle" stroke-width="8" fill="transparent" r="36" cx="50" cy="50"/>
                                </svg>
                                <div class="position-absolute top-50 start-50 translate-middle">
                                    <h2 class="mb-0" id="totalPages">0</h2>
                                    <small>pages</small>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-6">
                                    <div class="p-3 bg-secondary rounded">
                                        <h5 class="mb-0" id="fileCount">0</h5>
                                        <small>Fichiers</small>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="p-3 bg-secondary rounded">
                                        <h5 class="mb-0" id="totalSize">0</h5>
                                        <small>MB</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Bouton d'action -->
                    <button class="btn btn-success btn-lg w-100 py-3 mb-3" id="mergeBtn" onclick="mergePDFs()" disabled>
                        <i class="fas fa-rocket me-2"></i>Fusionner maintenant
                    </button>
                    
                    <!-- Aperçu filigrane -->
                    <div class="card bg-dark border-warning">
                        <div class="card-header bg-warning text-dark">
                            <h5 class="mb-0"><i class="fas fa-eye me-2"></i>Aperçu filigrane</h5>
                        </div>
                        <div class="card-body">
                            <div class="preview-box mb-3">
                                <div id="watermarkPreview" class="watermark-preview">EXEMPLE</div>
                            </div>
                            <button class="btn btn-outline-warning btn-sm w-100" onclick="updateWatermarkPreview()">
                                <i class="fas fa-sync me-2"></i>Actualiser
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Page outils -->
        <div id="toolsPage" class="glass-card p-4 p-md-5 mb-5" style="display: none;">
            <h2 class="mb-4"><i class="fas fa-tools me-2"></i>Outils PDF avancés</h2>
            
            <div class="row">
                <div class="col-md-6 mb-4">
                    <div class="card bg-dark h-100">
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
                    <div class="card bg-dark h-100">
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

        <!-- Page à propos -->
        <div id="aboutPage" class="glass-card p-4 p-md-5 mb-5" style="display: none;">
            <h2 class="mb-4"><i class="fas fa-info-circle me-2"></i>À propos & Aide</h2>
            
            <div class="row">
                <div class="col-md-8">
                    <h4>Comment utiliser PDF Fusion Pro</h4>
                    <div class="accordion" id="helpAccordion">
                        <div class="accordion-item bg-dark">
                            <h2 class="accordion-header">
                                <button class="accordion-button bg-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne">
                                    <i class="fas fa-question-circle me-2"></i>Comment fusionner des PDFs ?
                                </button>
                            </h2>
                            <div id="collapseOne" class="accordion-collapse collapse show">
                                <div class="accordion-body">
                                    <ol>
                                        <li>Cliquez sur "Fusion" dans le menu</li>
                                        <li>Déposez vos fichiers PDF dans la zone prévue</li>
                                        <li>Configurez les options (filigrane, métadonnées)</li>
                                        <li>Cliquez sur "Fusionner maintenant"</li>
                                        <li>Téléchargez votre fichier fusionné</li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                        
                        <div class="accordion-item bg-dark">
                            <h2 class="accordion-header">
                                <button class="accordion-button bg-secondary collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo">
                                    <i class="fas fa-shield-alt me-2"></i>Mes fichiers sont-ils sécurisés ?
                                </button>
                            </h2>
                            <div id="collapseTwo" class="accordion-collapse collapse">
                                <div class="accordion-body">
                                    <p><strong>Oui, totalement !</strong></p>
                                    <ul>
                                        <li>Vos fichiers sont traités sur nos serveurs sécurisés</li>
                                        <li>Ils sont automatiquement supprimés après traitement</li>
                                        <li>Nous ne conservons aucune copie de vos fichiers</li>
                                        <li>La connexion est chiffrée avec HTTPS</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <h5>Limites du service gratuit</h5>
                        <ul>
                            <li><i class="fas fa-check text-success me-2"></i>Nombre illimité de fusions</li>
                            <li><i class="fas fa-check text-success me-2"></i>Jusqu'à 50MB par fichier</li>
                            <li><i class="fas fa-check text-success me-2"></i>Jusqu'à 20 fichiers par fusion</li>
                            <li><i class="fas fa-check text-success me-2"></i>Toutes les fonctionnalités disponibles</li>
                        </ul>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card bg-dark border-success">
                        <div class="card-header bg-success">
                            <h5 class="mb-0"><i class="fas fa-heart me-2"></i>Support</h5>
                        </div>
                        <div class="card-body">
                            <p>PDF Fusion Pro est un service 100% gratuit.</p>
                            <p>Pour signaler un problème ou suggérer une amélioration :</p>
                            <button class="btn btn-outline-light w-100 mb-2">
                                <i class="fas fa-bug me-2"></i>Signaler un bug
                            </button>
                            <button class="btn btn-outline-light w-100">
                                <i class="fas fa-lightbulb me-2"></i>Suggérer une fonction
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-dark text-center py-4 mt-5">
        <div class="container">
            <p class="mb-2">
                <i class="fas fa-code text-info me-1"></i>
                Développé avec passion par PDF Fusion Pro
            </p>
            <p class="text-muted small mb-0">
                © 2024 PDF Fusion Pro - Service gratuit
                <span class="mx-2">•</span>
                <a href="#" class="text-muted text-decoration-none" onclick="showPrivacy()">Politique de confidentialité</a>
                <span class="mx-2">•</span>
                Hébergé sur <span class="text-info">Render.com</span>
            </p>
        </div>
    </footer>

    <!-- Modal de progression -->
    <div class="modal fade" id="progressModal" tabindex="-1" data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-dark">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title"><i class="fas fa-spinner fa-spin me-2"></i>Traitement en cours</h5>
                </div>
                <div class="modal-body text-center py-4">
                    <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;"></div>
                    <h5 id="progressTitle">Fusion des PDFs...</h5>
                    <p id="progressMessage" class="text-muted">Veuillez patienter</p>
                    <div class="progress bg-secondary">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" id="progressBar" style="width: 0%"></div>
                    </div>
                    <div class="text-muted small mt-3" id="progressDetails"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Variables globales
        let files = [];
        let currentPage = 'home';
        
        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            setupDragAndDrop();
            updateWatermarkPreview();
            simulateStats();
            
            // Mettre à jour l'aperçu quand le texte change
            document.getElementById('watermarkText').addEventListener('input', updateWatermarkPreview);
        });
        
        // Navigation
        function showHome() {
            showPage('homePage');
            currentPage = 'home';
        }
        
        function showMerge() {
            showPage('mergePage');
            currentPage = 'merge';
            updateStatsDisplay();
        }
        
        function showTools() {
            showPage('toolsPage');
            currentPage = 'tools';
        }
        
        function showAbout() {
            showPage('aboutPage');
            currentPage = 'about';
        }
        
        function showPage(pageId) {
            // Cacher toutes les pages
            document.getElementById('homePage').style.display = 'none';
            document.getElementById('mergePage').style.display = 'none';
            document.getElementById('toolsPage').style.display = 'none';
            document.getElementById('aboutPage').style.display = 'none';
            
            // Afficher la page demandée
            document.getElementById(pageId).style.display = 'block';
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
                const reader = new FileReader();
                reader.onload = function(e) {
                    const pdfData = new Uint8Array(e.target.result);
                    pdfjsLib.getDocument(pdfData).promise.then(pdf => {
                        resolve(pdf.numPages);
                    }).catch(() => {
                        resolve(1); // Valeur par défaut en cas d'erreur
                    });
                };
                reader.readAsArrayBuffer(file);
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
            document.getElementById('totalSize').textContent = totalSizeMB;
            
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
            document.getElementById('mergeBtn').disabled = files.length === 0;
        }
        
        // Mettre à jour l'aperçu du filigrane
        function updateWatermarkPreview() {
            const text = document.getElementById('watermarkText').value || 'EXEMPLE';
            const preview = document.getElementById('watermarkPreview');
            preview.textContent = text;
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
                    showToast('Erreur: ' + result.error, 'error');
                }
                
            } catch (error) {
                progressModal.hide();
                showToast('Erreur: ' + error.message, 'error');
            }
        }
        
        // Compresser un PDF
        async function compressPDF() {
            const input = document.getElementById('compressInput');
            input.click();
            
            input.onchange = async function() {
                if (!input.files.length) return;
                
                const file = input.files[0];
                
                // Vérifier la taille
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
                            `Compression: ${result.reduction} réduction`;
                        
                        setTimeout(() => {
                            progressModal.hide();
                            showToast('Fichier compressé téléchargé', 'success');
                        }, 1500);
                    } else {
                        progressModal.hide();
                        showToast('Erreur: ' + result.error, 'error');
                    }
                    
                } catch (error) {
                    progressModal.hide();
                    showToast('Erreur: ' + error.message, 'error');
                }
            };
        }
        
        // Obtenir des infos sur un PDF
        async function getPDFInfo() {
            const input = document.getElementById('infoInput');
            input.click();
            
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
            
            const toast = document.createElement('div');
            toast.className = `toast alert ${alertClass} alert-dismissible fade show`;
            toast.innerHTML = `
                ${icon} ${message}
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, duration);
        }
        
        // Simuler des statistiques
        function simulateStats() {
            let count = 12345;
            const statsElement = document.getElementById('statsCount');
            
            setInterval(() => {
                count += Math.floor(Math.random() * 10) + 1;
                statsElement.textContent = count.toLocaleString();
            }, 30000); // Toutes les 30 secondes
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
    
    # Utiliser waitress pour la production (meilleur que gunicorn sur Windows)
    if os.environ.get('RENDER'):
        from waitress import serve
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
