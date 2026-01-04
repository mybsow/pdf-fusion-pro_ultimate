# === PERSONNALISATION ===
DEVELOPER_NAME = "MYBSOW"  # ← VOTRE NOM ICI
DEVELOPER_EMAIL = "banousow@gmail.com"  # ← VOTRE EMAIL
APP_VERSION = "3.0.0"
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
        
        return pages  # <-- CORRECTION: Ajout du return
                    
    def merge_pdfs(self, pdf_files, options=None):
        """Fusionner plusieurs PDFs avec options"""
        if options is None:
            options = {}
        
        writer = PyPDF2.PdfWriter()
        watermark = options.get('watermark', {})
        metadata = options.get('metadata', {})
        rotation = options.get('rotation', {})  # ← Nouveau: option rotation
        
        # Créer le filigrane si demandé
        watermark_pdf = None
        if watermark.get('enabled') and watermark.get('text'):
            watermark_pdf = self.create_watermark(
                watermark['text'],
                watermark.get('position', 'center'),
                watermark.get('opacity', 0.3),
                watermark.get('font_size', 48)
            )
        
        # CORRECTION: Indentation corrigée ici
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
    return render_template_string(HTML_TEMPLATE)

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
                'pages': pages
            })
        finally:
            processor.cleanup()
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# TEMPLATE HTML (corrigé)
# ============================================

# Le template HTML est trop long pour être affiché en entier ici
# Mais voici les corrections principales dans le JavaScript :

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
        /* ... (le CSS reste inchangé) ... */
    </style>
</head>
<body>
    <!-- ... (le HTML reste inchangé jusqu'au JavaScript) ... -->
    
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
            ['homePage', 'mergePage', 'toolsPage', 'aboutPage'].forEach(id => {
                document.getElementById(id).style.display = 'none';
            });
            
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
                        data: e.target.result.split(',')[1],  // Base64 sans le préfixe
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
                        resolve(1);
                    }
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
            const totalPages = files.reduce((sum, file) => sum + (file.pages || 0), 0);
            const totalSize = files.reduce((sum, file) => sum + (file.size || 0), 0);
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
            const mergeBtn = document.getElementById('mergeBtn');
            if (mergeBtn) {
                mergeBtn.disabled = files.length === 0;
            }
        }
        
        // Mettre à jour l'aperçu du filigrane
        function updateWatermarkPreview() {
            const text = document.getElementById('watermarkText').value || 'EXEMPLE';
            const preview = document.getElementById('watermarkPreview');
            if (preview) {
                preview.textContent = text;
            }
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
                    },
                    rotation: {
                        enabled: document.getElementById('enableRotation') ? document.getElementById('enableRotation').checked : false,
                        angle: parseInt(document.getElementById('rotationAngleSelect') ? document.getElementById('rotationAngleSelect').value : 90),
                        pages: document.getElementById('rotationPages') ? document.getElementById('rotationPages').value.trim() || 'all' : 'all'
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
                
                // Vérifier la taille
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
                    // Lire le fichier
                    const reader = new FileReader();
                    reader.onload = async function(e) {
                        const fileData = {
                            name: file.name,
                            size: file.size,
                            data: e.target.result.split(',')[1]
                        };
                        
                        // Préparer les données
                        const requestData = {
                            file: fileData,
                            angle: parseInt(angle),
                            pages: pages || 'all'
                        };
                        
                        document.getElementById('progressBar').style.width = '50%';
                        document.getElementById('progressMessage').textContent = 'Envoi au serveur...';
                        
                        // Envoyer au serveur
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
        print(f"Démarrage du serveur sur le port {port}...")
        serve(app, host='0.0.0.0', port=port)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)
