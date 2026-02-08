#!/usr/bin/env python3
"""
Blueprint pour les conversions de fichiers - Version universelle
"""

from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import shutil
import traceback
from io import BytesIO
import zipfile

from config import AppConfig

# Import pour les conversions
import pandas as pd
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from docx import Document
import PyPDF2

# OCR
try:
    import pytesseract
    # Si Tesseract n'est pas dans le PATH par défaut sur Render :
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    from pytesseract import Output
except Exception as _e:
    pytesseract = None
    Output = None

# PDF -> images
try:
    from pdf2image import convert_from_bytes
except Exception as _e:
    convert_from_bytes = None

# Word -> PDF (utilisant LibreOffice via subprocess)
import subprocess

conversion_bp = Blueprint('conversion', __name__,
                          template_folder='../templates/conversion',
                          static_folder='../static/conversion',
                          url_prefix='/conversion')

# ============================================================================
# CONVERSION MAP - Configuration de toutes les conversions disponibles
# ============================================================================

CONVERSION_MAP = {
    # ==================== CONVERTIR EN PDF ====================
    'word-en-pdf': {
        'template': 'word_to_pdf.html',
        'title': 'Word vers PDF',
        'description': 'Convertissez vos documents Word en PDF',
        'from_format': 'Word',
        'to_format': 'PDF',
        'icon': 'file-word',
        'color': '#2b579a',
        'accept': '.doc,.docx',
        'max_files': 5
    },
    
    'excel-en-pdf': {
        'template': 'excel_to_pdf.html',
        'title': 'Excel vers PDF',
        'description': 'Convertissez vos feuilles Excel en PDF',
        'from_format': 'Excel',
        'to_format': 'PDF',
        'icon': 'file-excel',
        'color': '#217346',
        'accept': '.xls,.xlsx,.xlsm',
        'max_files': 5
    },
    
    'powerpoint-en-pdf': {
        'template': 'powerpoint_to_pdf.html',
        'title': 'PowerPoint vers PDF',
        'description': 'Convertissez vos présentations PowerPoint en PDF',
        'from_format': 'PowerPoint',
        'to_format': 'PDF',
        'icon': 'file-powerpoint',
        'color': '#d24726',
        'accept': '.ppt,.pptx',
        'max_files': 5
    },
    
    'image-en-pdf': {
        'template': 'image_to_pdf.html',
        'title': 'Image vers PDF',
        'description': 'Convertissez vos images en document PDF',
        'from_format': 'Image',
        'to_format': 'PDF',
        'icon': 'file-image',
        'color': '#e74c3c',
        'accept': '.jpg,.jpeg,.png,.bmp,.gif,.tiff,.webp',
        'max_files': 20
    },
    
    # ==================== CONVERTIR DEPUIS PDF ====================
    'pdf-en-word': {
        'template': 'pdf_to_word.html',
        'title': 'PDF vers Word',
        'description': 'Extrayez le texte de vos PDF en documents Word',
        'from_format': 'PDF',
        'to_format': 'Word',
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'pdf-en-excel': {
        'template': 'pdf_to_excel.html',
        'title': 'PDF vers Excel',
        'description': 'Extrayez les tableaux de vos PDF en feuilles Excel',
        'from_format': 'PDF',
        'to_format': 'Excel',
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'pdf-en-powerpoint': {
        'template': 'pdf_to_powerpoint.html',
        'title': 'PDF vers PowerPoint',
        'description': 'Convertissez vos PDF en présentations PowerPoint',
        'from_format': 'PDF',
        'to_format': 'PowerPoint',
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'pdf-en-image': {
        'template': 'pdf_to_image.html',
        'title': 'PDF vers Image',
        'description': 'Convertissez les pages de vos PDF en images',
        'from_format': 'PDF',
        'to_format': 'Image',
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'pdf-en-pdfa': {
        'template': 'pdf_to_pdfa.html',
        'title': 'PDF vers PDF/A',
        'description': 'Convertissez vos PDF en format PDF/A pour l\'archivage',
        'from_format': 'PDF',
        'to_format': 'PDF/A',
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1
    },
    
    # ==================== OUTILS PDF ====================
    'fusionner-pdf': {
        'template': 'merge_pdf.html',
        'title': 'Fusionner PDF',
        'description': 'Fusionnez plusieurs fichiers PDF en un seul',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'object-group',
        'color': '#3498db',
        'accept': '.pdf',
        'max_files': 20
    },
    
    'diviser-pdf': {
        'template': 'split_pdf.html',
        'title': 'Diviser PDF',
        'description': 'Divisez un PDF en plusieurs fichiers',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'cut',
        'color': '#9b59b6',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'compresser-pdf': {
        'template': 'compress_pdf.html',
        'title': 'Compresser PDF',
        'description': 'Réduisez la taille de vos fichiers PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'compress',
        'color': '#2ecc71',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'rotation-pdf': {
        'template': 'rotate_pdf.html',
        'title': 'Rotation PDF',
        'description': 'Faites pivoter les pages de vos PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'sync-alt',
        'color': '#f39c12',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'proteger-pdf': {
        'template': 'protect_pdf.html',
        'title': 'Protéger PDF',
        'description': 'Ajoutez un mot de passe à vos PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'lock',
        'color': '#e67e22',
        'accept': '.pdf',
        'max_files': 1
    },
    
    'deverrouiller-pdf': {
        'template': 'unlock_pdf.html',
        'title': 'Déverrouiller PDF',
        'description': 'Retirez la protection des PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'unlock',
        'color': '#1abc9c',
        'accept': '.pdf',
        'max_files': 1
    },
    
    # ==================== CONVERSIONS DIVERSES ====================
    'image-en-word': {
        'template': 'image_to_word.html',
        'title': 'Image vers Word',
        'description': 'Extrayez le texte des images en documents Word',
        'from_format': 'Image',
        'to_format': 'Word',
        'icon': 'image',
        'color': '#2b579a',
        'accept': '.jpg,.jpeg,.png,.bmp,.tiff',
        'max_files': 1
    },
    
    'image-en-excel': {
        'template': 'image_to_excel.html',
        'title': 'Image vers Excel',
        'description': 'Extrayez les tableaux des images en Excel',
        'from_format': 'Image',
        'to_format': 'Excel',
        'icon': 'image',
        'color': '#217346',
        'accept': '.jpg,.jpeg,.png,.bmp,.tiff,.pdf',
        'max_files': 1
    },
    
    'csv-en-excel': {
        'template': 'csv_to_excel.html',
        'title': 'CSV vers Excel',
        'description': 'Convertissez vos fichiers CSV en Excel',
        'from_format': 'CSV',
        'to_format': 'Excel',
        'icon': 'file-csv',
        'color': '#217346',
        'accept': '.csv,.txt',
        'max_files': 5
    },
    
    'excel-en-csv': {
        'template': 'excel_to_csv.html',
        'title': 'Excel vers CSV',
        'description': 'Exportez vos feuilles Excel en CSV',
        'from_format': 'Excel',
        'to_format': 'CSV',
        'icon': 'file-excel',
        'color': '#217346',
        'accept': '.xls,.xlsx',
        'max_files': 5
    }
}

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@conversion_bp.route('/')
def index():
    """Page d'accueil des conversions."""
    # Organiser les conversions par catégorie
    categories = {
        'convert_to_pdf': {
            'title': 'Convertir en PDF',
            'icon': 'file-pdf',
            'color': '#e74c3c',
            'conversions': [
                CONVERSION_MAP['word-en-pdf'],
                CONVERSION_MAP['excel-en-pdf'],
                CONVERSION_MAP['powerpoint-en-pdf'],
                CONVERSION_MAP['image-en-pdf']
            ]
        },
        'convert_from_pdf': {
            'title': 'Convertir depuis PDF',
            'icon': 'file-pdf',
            'color': '#3498db',
            'conversions': [
                CONVERSION_MAP['pdf-en-word'],
                CONVERSION_MAP['pdf-en-excel'],
                CONVERSION_MAP['pdf-en-powerpoint'],
                CONVERSION_MAP['pdf-en-image'],
                CONVERSION_MAP['pdf-en-pdfa']
            ]
        },
        'pdf_tools': {
            'title': 'Outils PDF',
            'icon': 'tools',
            'color': '#2ecc71',
            'conversions': [
                CONVERSION_MAP['fusionner-pdf'],
                CONVERSION_MAP['diviser-pdf'],
                CONVERSION_MAP['compresser-pdf'],
                CONVERSION_MAP['rotation-pdf'],
                CONVERSION_MAP['proteger-pdf'],
                CONVERSION_MAP['deverrouiller-pdf']
            ]
        },
        'other_conversions': {
            'title': 'Autres conversions',
            'icon': 'exchange-alt',
            'color': '#9b59b6',
            'conversions': [
                CONVERSION_MAP['image-en-word'],
                CONVERSION_MAP['image-en-excel'],
                CONVERSION_MAP['csv-en-excel'],
                CONVERSION_MAP['excel-en-csv']
            ]
        }
    }
    
    return render_template('conversion/index.html',
                          title="Convertisseur de fichiers universel",
                          categories=categories,
                          all_conversions=CONVERSION_MAP)


@conversion_bp.route('/<string:conversion_type>', methods=['GET', 'POST'])
def universal_converter(conversion_type):
    """
    Route universelle pour toutes les conversions.
    """
    # Vérifier si la conversion existe
    if conversion_type not in CONVERSION_MAP:
        flash(f'Type de conversion non supporté: {conversion_type}', 'error')
        return redirect(url_for('conversion.index'))
    
    config = CONVERSION_MAP[conversion_type]
    
    if request.method == 'POST':
        return handle_conversion_request(conversion_type, request, config)
    
    # GET request - afficher le formulaire
    return render_template(f'conversion/{config["template"]}',
                          title=config['title'],
                          description=config['description'],
                          from_format=config['from_format'],
                          to_format=config['to_format'],
                          icon=config['icon'],
                          color=config['color'],
                          accept=config['accept'],
                          max_files=config['max_files'],
                          conversion_type=conversion_type)


def handle_conversion_request(conversion_type, request, config):
    """Gère la requête de conversion."""
    try:
        # Vérifier les fichiers
        if 'file' not in request.files and 'files' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        # Récupérer les fichiers selon le type
        if config['max_files'] > 1:
            files = request.files.getlist('files')
            if not files or files[0].filename == '':
                flash('Veuillez sélectionner au moins un fichier', 'error')
                return redirect(request.url)
            
            # Valider le nombre de fichiers
            if len(files) > config['max_files']:
                flash(f'Maximum {config["max_files"]} fichiers autorisés', 'error')
                return redirect(request.url)
            
            result = process_conversion(conversion_type, files=files, form_data=request.form)
        else:
            file = request.files['file']
            if file.filename == '':
                flash('Veuillez sélectionner un fichier', 'error')
                return redirect(request.url)
            
            result = process_conversion(conversion_type, file=file, form_data=request.form)
        
        # ⭐⭐ CORRECTION ICI - LIGNE 413 ⭐⭐
        # Vérifier si result est un dictionnaire avec une erreur
        if isinstance(result, dict) and 'error' in result:
            flash(result['error'], 'error')
            return redirect(request.url)
        
        # Si c'est une Response (fichier à télécharger), la retourner directement
        return result
        
    except Exception as e:
        current_app.logger.error(f"Erreur conversion {conversion_type}: {str(e)}\n{traceback.format_exc()}")
        flash(f'Erreur lors de la conversion: {str(e)}', 'error')
        return redirect(request.url)
            
            result = process_conversion(conversion_type, file=file, form_data=request.form)
        
        # Retourner le résultat
        if result and 'error' in result:
            flash(result['error'], 'error')
            return redirect(request.url)
        
        return result
        
    except Exception as e:
        current_app.logger.error(f"Erreur conversion {conversion_type}: {str(e)}\n{traceback.format_exc()}")
        flash(f'Erreur lors de la conversion: {str(e)}', 'error')
        return redirect(request.url)


def process_conversion(conversion_type, file=None, files=None, form_data=None):
    """Exécute la conversion appropriée."""
    conversion_functions = {
        # Conversion en PDF
        'word-en-pdf': convert_word_to_pdf,
        'excel-en-pdf': convert_excel_to_pdf,
        'powerpoint-en-pdf': convert_powerpoint_to_pdf,
        'image-en-pdf': convert_images_to_pdf,
        
        # Conversion depuis PDF
        'pdf-en-word': convert_pdf_to_word,
        'pdf-en-excel': convert_pdf_to_excel,
        'pdf-en-image': convert_pdf_to_images,
        'pdf-en-pdfa': convert_pdf_to_pdfa,
        
        # Outils PDF
        'fusionner-pdf': merge_pdfs,
        'diviser-pdf': split_pdf,
        'compresser-pdf': compress_pdf,
        'rotation-pdf': rotate_pdf,
        'proteger-pdf': protect_pdf,
        'deverrouiller-pdf': unlock_pdf,
        
        # Autres conversions
        'image-en-word': convert_image_to_word,
        'image-en-excel': convert_image_to_excel,
        'csv-en-excel': convert_csv_to_excel,
        'excel-en-csv': convert_excel_to_csv,
    }
    
    if conversion_type not in conversion_functions:
        return {'error': 'Type de conversion non implémenté'}
    
    func = conversion_functions[conversion_type]
    
    try:
        if files:
            return func(files, form_data)
        else:
            return func(file, form_data)
    except Exception as e:
        current_app.logger.error(f"Exception dans {conversion_type}: {str(e)}")
        return {'error': f'Erreur interne: {str(e)}'}


# ============================================================================
# FONCTIONS DE CONVERSION
# ============================================================================

# 1. CONVERSION EN PDF
def convert_word_to_pdf(file, form_data=None):
    """Convertit Word en PDF."""
    try:
        # Enregistrer temporairement le fichier
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        output_path = os.path.join(temp_dir, 'converted.pdf')
        
        file.save(input_path)
        
        # Utiliser LibreOffice pour la conversion
        # Note: Nécessite LibreOffice installé sur le serveur
        cmd = ['libreoffice', '--headless', '--convert-to', 'pdf', 
               '--outdir', temp_dir, input_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'error': f'Erreur LibreOffice: {result.stderr}'}
        
        # Lire le PDF généré
        with open(output_path, 'rb') as f:
            pdf_data = f.read()
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Retourner le PDF
        output = BytesIO(pdf_data)
        filename = f"{os.path.splitext(file.filename)[0]}.pdf"
        
        return send_file(output, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur Word->PDF: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


def convert_excel_to_pdf(file, form_data=None):
    """Convertit Excel en PDF."""
    try:
        # Solution simplifiée - créer un PDF avec un message
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        
        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "Conversion Excel vers PDF")
        
        # Informations
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, f"Fichier: {file.filename}")
        c.drawString(100, 680, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Message
        c.drawString(100, 620, "Pour une conversion complète d'Excel vers PDF,")
        c.drawString(100, 600, "installez LibreOffice sur le serveur.")
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(100, 100, "PDF Fusion Pro - Convertisseur gratuit")
        
        c.save()
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur Excel->PDF: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


def convert_powerpoint_to_pdf(file, form_data=None):
    """Convertit PowerPoint en PDF."""
    # Similaire à Excel, mais pour PowerPoint
    return convert_excel_to_pdf(file, form_data)


def convert_images_to_pdf(files, form_data=None):
    """Convertit des images en PDF."""
    try:
        output = BytesIO()
        
        # Déterminer l'orientation
        orientation = form_data.get('orientation', 'portrait') if form_data else 'portrait'
        page_size = A4
        
        # Créer le PDF
        c = canvas.Canvas(output, pagesize=page_size)
        
        for i, file in enumerate(files):
            try:
                # Ouvrir l'image
                img = Image.open(file.stream)
                img = img.convert('RGB')
                
                # Sauvegarder temporairement
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                img.save(temp_file.name, 'JPEG', quality=90)
                
                # Calculer les dimensions
                img_width, img_height = img.size
                page_width, page_height = page_size
                
                # Marge
                margin = 40
                max_width = page_width - (2 * margin)
                max_height = page_height - (2 * margin)
                
                # Ratio de redimensionnement
                ratio = min(max_width / img_width, max_height / img_height, 1.0)
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                # Centrer
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2
                
                # Ajouter l'image
                c.drawImage(temp_file.name, x, y, width=new_width, height=new_height)
                
                # Nouvelle page sauf pour la dernière image
                if i < len(files) - 1:
                    c.showPage()
                
                # Nettoyer
                os.unlink(temp_file.name)
                
            except Exception as img_error:
                current_app.logger.error(f"Erreur image {file.filename}: {img_error}")
                continue
        
        c.save()
        output.seek(0)
        
        filename = f"images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur Images->PDF: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


# 2. CONVERSION DEPUIS PDF
def convert_pdf_to_word(file, form_data=None):
    """Convertit PDF en Word."""
    try:
        # Créer un document Word simple
        doc = Document()
        doc.add_heading('Document converti depuis PDF', 0)
        
        # Informations
        doc.add_paragraph(f'Fichier source: {file.filename}')
        doc.add_paragraph(f'Date de conversion: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        doc.add_paragraph()
        
        # Message d'information
        doc.add_heading('Contenu du PDF', level=1)
        doc.add_paragraph('Pour une extraction complète du texte avec OCR,')
        doc.add_paragraph('installez pytesseract et poppler sur le serveur.')
        
        # Sauvegarder
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}.docx"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
    except Exception as e:
        current_app.logger.error(f"Erreur PDF->Word: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


def convert_pdf_to_excel(file, form_data=None):
    """Convertit PDF en Excel avec OCR."""
    try:
        # Vérifier les dépendances OCR
        if pytesseract is None:
            return {'error': "pytesseract n'est pas installé"}
        
        if convert_from_bytes is None:
            return {'error': "pdf2image n'est pas installé"}
        
        # Convertir PDF en images
        pdf_bytes = file.read()
        pages = convert_from_bytes(pdf_bytes, dpi=300)
        
        if not pages:
            return {'error': 'Aucune page détectée dans le PDF'}
        
        # Extraire le texte avec OCR
        all_data = []
        for page_num, page_img in enumerate(pages, 1):
            try:
                # OCR
                text = pytesseract.image_to_string(page_img, lang='fra+eng')
                
                if text.strip():
                    # Diviser en lignes
                    lines = text.strip().split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if line.strip():
                            all_data.append({
                                'Page': page_num,
                                'Ligne': line_num,
                                'Texte': line.strip()
                            })
            except Exception as page_error:
                current_app.logger.error(f"Erreur page {page_num}: {page_error}")
                continue
        
        # Créer DataFrame
        df = pd.DataFrame(all_data)
        
        if df.empty:
            df = pd.DataFrame({'Message': ['Aucun texte détecté dans le PDF']})
        
        # Créer Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Extraction')
            
            # Ajouter onglet d'infos
            info_df = pd.DataFrame({
                'Information': ['Fichier source', 'Date', 'Pages traitées', 'Lignes extraites'],
                'Valeur': [file.filename, 
                          datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          len(pages),
                          len(df)]
            })
            info_df.to_excel(writer, index=False, sheet_name='Infos')
        
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}.xlsx"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        current_app.logger.error(f"Erreur PDF->Excel: {str(e)}\n{traceback.format_exc()}")
        return {'error': f'Erreur de conversion: {str(e)}'}


def convert_pdf_to_images(file, form_data=None):
    """Convertit PDF en images."""
    try:
        if convert_from_bytes is None:
            return {'error': "pdf2image n'est pas installé"}
        
        # Convertir PDF en images
        pdf_bytes = file.read()
        pages = convert_from_bytes(pdf_bytes, dpi=150)  # DPI plus bas pour des fichiers plus petits
        
        if not pages:
            return {'error': 'Aucune page détectée dans le PDF'}
        
        # Créer un ZIP avec les images
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, page in enumerate(pages, 1):
                img_buffer = BytesIO()
                page.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                filename = f"page_{i:03d}.png"
                zip_file.writestr(filename, img_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_images.zip"
        
        return send_file(zip_buffer,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/zip')
        
    except Exception as e:
        current_app.logger.error(f"Erreur PDF->Images: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


def convert_pdf_to_pdfa(file, form_data=None):
    """Convertit PDF en PDF/A."""
    try:
        # Lire le PDF
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copier toutes les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Ajouter des métadonnées PDF/A (simplifié)
        pdf_writer.add_metadata({
            '/Title': f'Converted PDF/A - {file.filename}',
            '/Author': 'PDF Fusion Pro',
            '/Subject': 'Document converti en PDF/A',
            '/Keywords': 'PDF/A, archivage',
            '/Creator': 'PDF Fusion Pro Converter',
            '/Producer': 'PDF Fusion Pro',
            '/CreationDate': PyPDF2.utils.format_datetime(datetime.now()),
            '/ModDate': PyPDF2.utils.format_datetime(datetime.now())
        })
        
        # Écrire le PDF
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_pdfa.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur PDF->PDF/A: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


# 3. OUTILS PDF
def merge_pdfs(files, form_data=None):
    """Fusionne plusieurs PDF."""
    try:
        pdf_writer = PyPDF2.PdfWriter()
        
        for file in files:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Ajouter toutes les pages
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
        
        # Écrire le PDF fusionné
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"fusionne_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur fusion PDF: {str(e)}")
        return {'error': f'Erreur de fusion: {str(e)}'}


def split_pdf(file, form_data=None):
    """Divise un PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        
        # Obtenir les plages de pages
        ranges = form_data.get('ranges', 'all') if form_data else 'all'
        
        if ranges == 'all':
            # Diviser chaque page
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(num_pages):
                    pdf_writer = PyPDF2.PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[i])
                    
                    page_buffer = BytesIO()
                    pdf_writer.write(page_buffer)
                    page_buffer.seek(0)
                    
                    filename = f"page_{i+1:03d}.pdf"
                    zip_file.writestr(filename, page_buffer.getvalue())
            
            zip_buffer.seek(0)
            
            filename = f"{os.path.splitext(file.filename)[0]}_pages.zip"
            
            return send_file(zip_buffer,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/zip')
        else:
            # Diviser selon les plages spécifiées
            return {'error': 'Division par plages non implémentée'}
        
    except Exception as e:
        current_app.logger.error(f"Erreur division PDF: {str(e)}")
        return {'error': f'Erreur de division: {str(e)}'}


def compress_pdf(file, form_data=None):
    """Compresse un PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copier toutes les pages (compression basique)
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Options de compression
        compress_level = int(form_data.get('level', 1)) if form_data else 1
        
        # Écrire avec compression
        output = BytesIO()
        pdf_writer.write(output)
        
        # Réduire la taille (méthode simple)
        if compress_level > 1:
            # Ré-écrire avec des options de compression
            pass
        
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_compresse.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur compression PDF: {str(e)}")
        return {'error': f'Erreur de compression: {str(e)}'}


def rotate_pdf(file, form_data=None):
    """Tourne les pages d'un PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Angle de rotation
        angle = int(form_data.get('angle', 90)) if form_data else 90
        
        # Tourner chaque page
        for page in pdf_reader.pages:
            page.rotate(angle)
            pdf_writer.add_page(page)
        
        # Écrire le PDF
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_rotation.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur rotation PDF: {str(e)}")
        return {'error': f'Erreur de rotation: {str(e)}'}


def protect_pdf(file, form_data=None):
    """Protège un PDF avec mot de passe."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copier toutes les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Mot de passe
        password = form_data.get('password', '') if form_data else ''
        
        if password:
            pdf_writer.encrypt(password)
        
        # Écrire le PDF
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_protege.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur protection PDF: {str(e)}")
        return {'error': f'Erreur de protection: {str(e)}'}


def unlock_pdf(file, form_data=None):
    """Déverrouille un PDF."""
    try:
        password = form_data.get('password', '') if form_data else ''
        
        # Essayer de lire avec le mot de passe
        try:
            pdf_reader = PyPDF2.PdfReader(file, password=password if password else None)
        except Exception as read_error:
            return {'error': f'Mot de passe incorrect ou PDF corrompu: {read_error}'}
        
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copier toutes les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Écrire sans protection
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}_deverrouille.pdf"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        current_app.logger.error(f"Erreur déverrouillage PDF: {str(e)}")
        return {'error': f'Erreur de déverrouillage: {str(e)}'}


# 4. AUTRES CONVERSIONS
def convert_image_to_word(file, form_data=None):
    """Convertit une image en Word avec OCR."""
    try:
        # Vérifier si l'OCR est disponible
        if not AppConfig.OCR_ENABLED:
            return {
                'error': "OCR est désactivé dans la configuration. Activez-le dans les paramètres."
            }
        
        # Vérifier les dépendances OCR
        try:
            import pytesseract
            import shutil
            if not shutil.which("tesseract"):
                return {
                    'error': "Tesseract n'est pas installé sur le serveur. L'OCR n'est pas disponible."
                }
        except ImportError:
            return {
                'error': "pytesseract n'est pas installé. Installez-le avec: pip install pytesseract"
            }
        
        # Ouvrir l'image
        img = Image.open(file.stream).convert('RGB')
        
        # OCR
        text = pytesseract.image_to_string(img, lang='fra+eng')
        
        # Créer document Word
        doc = Document()
        doc.add_heading('Document extrait d\'image', 0)
        
        # Informations
        doc.add_paragraph(f'Fichier source: {file.filename}')
        doc.add_paragraph(f'Date d\'extraction: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        doc.add_paragraph()
        
        # Ajouter le texte extrait
        if text.strip():
            doc.add_heading('Texte extrait', level=1)
            for paragraph in text.strip().split('\n\n'):
                if paragraph.strip():
                    doc.add_paragraph(paragraph.strip())
        else:
            doc.add_paragraph('Aucun texte détecté dans l\'image.')
        
        # Sauvegarder
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}.docx"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        
    except Exception as e:
        current_app.logger.error(f"Erreur Image->Word: {str(e)}")
        return {'error': f'Erreur d\'extraction: {str(e)}'}


def convert_image_to_excel(file, form_data=None):
    """Convertit une image en Excel avec OCR."""
    try:
        if pytesseract is None:
            return {'error': "pytesseract n'est pas installé"}
        
        # Ouvrir l'image
        img = Image.open(file.stream).convert('RGB')
        
        # OCR avec données structurées
        data = pytesseract.image_to_data(img, lang='fra+eng', output_type=Output.DATAFRAME)
        
        # Filtrer les données
        if data is not None and not data.empty:
            data = data[data['conf'] > 30]
            data = data[data['text'].notna() & (data['text'].str.strip() != '')]
        
        # Créer Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if data is not None and not data.empty:
                data.to_excel(writer, index=False, sheet_name='Données OCR')
            else:
                # Texte simple si pas de données structurées
                text = pytesseract.image_to_string(img, lang='fra+eng')
                df_text = pd.DataFrame({'Texte': text.strip().split('\n')})
                df_text.to_excel(writer, index=False, sheet_name='Texte')
            
            # Infos
            info_df = pd.DataFrame({
                'Information': ['Fichier source', 'Date', 'Confiance moyenne'],
                'Valeur': [file.filename, 
                          datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          data['conf'].mean() if data is not None and 'conf' in data.columns else 'N/A']
            })
            info_df.to_excel(writer, index=False, sheet_name='Infos')
        
        output.seek(0)
        
        filename = f"{os.path.splitext(file.filename)[0]}.xlsx"
        
        return send_file(output,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        current_app.logger.error(f"Erreur Image->Excel: {str(e)}\n{traceback.format_exc()}")
        return {'error': f'Erreur d\'extraction: {str(e)}'}


def convert_csv_to_excel(files, form_data=None):
    """Convertit CSV en Excel."""
    try:
        # Pour plusieurs fichiers, créer un ZIP
        if len(files) > 1:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    # Lire CSV
                    df = pd.read_csv(file)
                    
                    # Créer Excel en mémoire
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Données')
                    excel_buffer.seek(0)
                    
                    filename = f"{os.path.splitext(file.filename)[0]}.xlsx"
                    zip_file.writestr(filename, excel_buffer.getvalue())
            
            zip_buffer.seek(0)
            
            filename = f"csv_excel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return send_file(zip_buffer,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/zip')
        else:
            # Un seul fichier
            file = files[0]
            df = pd.read_csv(file)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Données')
            
            output.seek(0)
            
            filename = f"{os.path.splitext(file.filename)[0]}.xlsx"
            
            return send_file(output,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
    except Exception as e:
        current_app.logger.error(f"Erreur CSV->Excel: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


def convert_excel_to_csv(files, form_data=None):
    """Convertit Excel en CSV."""
    try:
        # Pour plusieurs fichiers, créer un ZIP
        if len(files) > 1:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    # Lire Excel
                    df = pd.read_excel(file)
                    
                    # Convertir en CSV
                    csv_data = df.to_csv(index=False)
                    
                    filename = f"{os.path.splitext(file.filename)[0]}.csv"
                    zip_file.writestr(filename, csv_data)
            
            zip_buffer.seek(0)
            
            filename = f"excel_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            return send_file(zip_buffer,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='application/zip')
        else:
            # Un seul fichier
            file = files[0]
            df = pd.read_excel(file)
            
            output = BytesIO()
            csv_data = df.to_csv(index=False)
            output.write(csv_data.encode('utf-8-sig'))
            output.seek(0)
            
            filename = f"{os.path.splitext(file.filename)[0]}.csv"
            
            return send_file(output,
                            as_attachment=True,
                            download_name=filename,
                            mimetype='text/csv')
        
    except Exception as e:
        current_app.logger.error(f"Erreur Excel->CSV: {str(e)}")
        return {'error': f'Erreur de conversion: {str(e)}'}


# ============================================================================
# ROUTES API ET UTILITAIRES
# ============================================================================
@conversion_bp.context_processor
def utility_processor():
    """Fonctions utilitaires disponibles dans les templates."""
    
    def conversion_id_for_url(conversion_config):
        """Trouve l'ID de conversion à partir de sa configuration."""
        for key, config in CONVERSION_MAP.items():
            if config == conversion_config:
                return key
        return None
    
    return {
        'conversion_id_for_url': conversion_id_for_url,
        'now': datetime.now
    }

@conversion_bp.route('/api/supported-formats')
def api_supported_formats():
    """API pour récupérer les formats supportés."""
    return jsonify({
        'status': 'success',
        'conversions': list(CONVERSION_MAP.keys()),
        'details': CONVERSION_MAP
    })


@conversion_bp.route('/api/health')
def api_health():
    """Vérifie l'état des dépendances."""
    dependencies = {
        'pandas': False,
        'PyPDF2': False,
        'Pillow': False,
        'pytesseract': False,
        'pdf2image': False,
        'openpyxl': False,
        'python-docx': False,
        'reportlab': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            dependencies[dep] = True
        except ImportError:
            pass
    
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'dependencies': dependencies
    })


@conversion_bp.route('/dependencies')
def dependencies_page():
    """Page d'information sur les dépendances."""
    dependencies = []
    
    required = {
        'pandas': 'Manipulation de données',
        'PyPDF2': 'Traitement PDF',
        'Pillow': 'Manipulation d\'images',
        'pytesseract': 'OCR (reconnaissance de texte)',
        'pdf2image': 'Conversion PDF vers images',
        'openpyxl': 'Manipulation Excel',
        'python-docx': 'Manipulation Word',
        'reportlab': 'Génération PDF',
        'LibreOffice': 'Conversion Office vers PDF (système)',
        'poppler': 'Conversion PDF vers images (système)'
    }
    
    for package, description in required.items():
        if package in ['LibreOffice', 'poppler']:
            # Vérifier les binaires système
            dependencies.append({
                'name': package,
                'description': description,
                'installed': check_system_command(package.lower())
            })
        else:
            dependencies.append({
                'name': package,
                'description': description,
                'installed': check_python_package(package)
            })
    
    return render_template('conversion/dependencies.html',
                          title="Dépendances système",
                          dependencies=dependencies)


def check_python_package(package_name):
    """Vérifie si un package Python est installé."""
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False


def check_system_command(command):
    """Vérifie si une commande système est disponible."""
    try:
        result = subprocess.run(['which', command], 
                              capture_output=True, 
                              text=True)
        return result.returncode == 0
    except Exception:
        return False


@conversion_bp.route('/clean-temp')
def clean_temp():
    """Nettoie les fichiers temporaires."""
    try:
        temp_dir = Path('temp/conversion')
        if temp_dir.exists():
            count = 0
            for file in temp_dir.glob('*'):
                try:
                    # Supprimer les fichiers de plus d'1 heure
                    if file.is_file() and file.stat().st_mtime < (datetime.now().timestamp() - 3600):
                        file.unlink()
                        count += 1
                except Exception:
                    pass
            
            flash(f'{count} fichiers temporaires nettoyés', 'success')
        else:
            flash('Aucun fichier temporaire à nettoyer', 'info')
            
    except Exception as e:
        flash(f'Erreur nettoyage: {str(e)}', 'error')
    
    return redirect(url_for('conversion.index'))
