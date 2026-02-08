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
    """Convertit PDF en Excel avec OCR - Version robuste une feuille."""
    try:
        # Vérifier les dépendances OCR
        if pytesseract is None:
            return {'error': "pytesseract n'est pas installé"}
        
        if convert_from_bytes is None:
            return {'error': "pdf2image n'est pas installé"}
        
        current_app.logger.info(f"Début conversion PDF->Excel: {file.filename}")
        
        # Lire le contenu du PDF
        pdf_bytes = file.read()
        file.seek(0)  # Réinitialiser le pointeur pour d'autres usages
        
        if not pdf_bytes:
            return {'error': 'Fichier PDF vide'}
        
        current_app.logger.info(f"Taille PDF: {len(pdf_bytes)} bytes")
        
        try:
            # Convertir PDF en images
            current_app.logger.info("Conversion PDF en images...")
            pages = convert_from_bytes(pdf_bytes, dpi=200)  # DPI réduit pour la vitesse
            
            if not pages:
                return {'error': 'Aucune page détectée dans le PDF'}
            
            current_app.logger.info(f"Pages converties: {len(pages)}")
            
        except Exception as conv_error:
            current_app.logger.error(f"Erreur conversion PDF->images: {conv_error}")
            return {'error': f'Erreur conversion PDF: {str(conv_error)}'}
        
        # Liste pour collecter toutes les données
        all_data = []
        total_confidence = 0
        total_words = 0
        
        # Traiter chaque page
        for page_num, page_img in enumerate(pages, 1):
            try:
                current_app.logger.info(f"Traitement page {page_num}/{len(pages)}")
                
                # Convertir l'image PIL en format compatible
                img = page_img.convert('RGB')
                
                # OCR avec données détaillées
                current_app.logger.info("Exécution OCR...")
                ocr_data = pytesseract.image_to_data(
                    img, 
                    lang='fra+eng',  # Seulement français et anglais disponibles
                    output_type=Output.DICT,
                    config='--psm 6'  # Mode bloc uniforme
                )
                
                # Convertir en DataFrame
                df_ocr = pd.DataFrame(ocr_data)
                
                # Filtrer les lignes avec du texte
                df_ocr = df_ocr[df_ocr['conf'] > 0]
                df_ocr['text'] = df_ocr['text'].astype(str).str.strip()
                df_ocr = df_ocr[df_ocr['text'] != '']
                
                if df_ocr.empty:
                    current_app.logger.warning(f"Page {page_num}: Aucun texte détecté")
                    all_data.append([f"Page {page_num}", "Aucun texte détecté"])
                    continue
                
                # Calculer les statistiques de confiance
                page_confidence = df_ocr['conf'].mean()
                page_words = len(df_ocr)
                total_confidence += page_confidence * page_words
                total_words += page_words
                
                current_app.logger.info(f"Page {page_num}: {page_words} mots, confiance {page_confidence:.1f}%")
                
                # Grouper les mots par lignes
                lines = {}
                for idx, row in df_ocr.iterrows():
                    top = row['top']
                    left = row['left']
                    text = row['text']
                    
                    # Trouver la ligne la plus proche (tolérance de 15 pixels)
                    found_line = None
                    for line_top in lines.keys():
                        if abs(top - line_top) < 15:
                            found_line = line_top
                            break
                    
                    if found_line is None:
                        found_line = top
                    
                    if found_line not in lines:
                        lines[found_line] = []
                    
                    lines[found_line].append((left, text))
                
                # Trier les lignes par position verticale
                sorted_lines = sorted(lines.items(), key=lambda x: x[0])
                
                # Ajouter un séparateur de page
                if all_data:  # Sauf pour la première page
                    all_data.append([])  # Ligne vide comme séparateur
                all_data.append([f"=== Page {page_num} ==="])
                
                # Ajouter les lignes de texte
                for line_top, words in sorted_lines:
                    # Trier les mots de gauche à droite
                    words.sort(key=lambda x: x[0])
                    
                    # Concaténer les mots de la ligne
                    line_text = ' '.join([word[1] for word in words])
                    all_data.append([line_text])
                    
            except Exception as page_error:
                current_app.logger.error(f"Erreur page {page_num}: {page_error}")
                all_data.append([f"Page {page_num}", f"Erreur: {str(page_error)[:50]}..."])
                continue
        
        # Si aucune donnée valide n'a été extraite
        if len(all_data) <= 1:  # Seulement les en-têtes de page
            return {'error': 'Aucun texte détecté dans le PDF'}
        
        current_app.logger.info(f"Données extraites: {len(all_data)} lignes")
        
        # Calculer la confiance moyenne
        avg_confidence = total_confidence / total_words if total_words > 0 else 0
        
        # Créer le DataFrame final
        df_final = pd.DataFrame(all_data, columns=['Contenu extrait'])
        
        # Créer Excel avec une seule feuille
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Écrire les données extraites
            df_final.to_excel(writer, index=False, sheet_name='Extraction PDF')
            
            # Personnaliser la feuille
            worksheet = writer.sheets['Extraction PDF']
            
            # Ajuster la largeur des colonnes
            worksheet.column_dimensions['A'].width = 80
            
            # Ajouter des statistiques
            stats_start_row = len(df_final) + 3
            
            # Créer un DataFrame pour les statistiques
            stats_data = {
                'Statistique': [
                    'Fichier source',
                    'Date d\'extraction',
                    'Pages traitées',
                    'Lignes extraites',
                    'Mots détectés',
                    'Confiance moyenne OCR',
                    'Format de sortie'
                ],
                'Valeur': [
                    file.filename,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    len(pages),
                    len(df_final),
                    total_words,
                    f"{avg_confidence:.1f}%" if avg_confidence > 0 else "N/A",
                    "Excel (XLSX)"
                ]
            }
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(
                writer,
                index=False,
                startrow=stats_start_row,
                sheet_name='Extraction PDF',
                header=False
            )
            
            # Ajouter une note explicative
            note_row = stats_start_row + len(stats_df) + 2
            worksheet.cell(row=note_row, column=1, 
                          value="Note: Les données sont extraites ligne par ligne. Pour une extraction tabulaire,")
            worksheet.cell(row=note_row + 1, column=1, 
                          value="utilisez l'outil 'Image vers Excel' avec des captures d'écran du PDF.")
        
        output.seek(0)
        file_size = len(output.getvalue())
        current_app.logger.info(f"Fichier Excel généré: {file_size} bytes")
        
        filename = f"{os.path.splitext(file.filename)[0]}_extrait.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
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
    """Convertit une image en Excel avec OCR - Version améliorée."""
    try:
        current_app.logger.info(f"Début conversion Image->Excel: {file.filename}")
        
        if pytesseract is None:
            return {'error': "pytesseract n'est pas installé"}
        
        # Ouvrir l'image
        try:
            img = Image.open(file.stream).convert('RGB')
            current_app.logger.info(f"Image chargée: {img.size[0]}x{img.size[1]}, mode: {img.mode}")
        except Exception as img_error:
            current_app.logger.error(f"Erreur ouverture image: {img_error}")
            return {'error': f'Format d\'image non supporté: {str(img_error)}'}
        
        # Prétraitement de l'image pour améliorer l'OCR
        try:
            img = preprocess_image_for_ocr(img)
            current_app.logger.info("Image prétraitée avec succès")
        except Exception as prep_error:
            current_app.logger.warning(f"Erreur prétraitement image: {prep_error}")
            # Continuer avec l'image originale
        
        # OCR avec données détaillées
        try:
            current_app.logger.info("Exécution OCR...")
            ocr_data = pytesseract.image_to_data(
                img, 
                lang='fra+eng', 
                output_type=Output.DICT,
                config='--psm 6'  # Mode: supposer un bloc uniforme de texte
            )
            current_app.logger.info(f"OCR terminé: {len(ocr_data['text'])} éléments détectés")
        except Exception as ocr_error:
            current_app.logger.error(f"Erreur OCR: {ocr_error}")
            return {'error': f'Erreur OCR: {str(ocr_error)}'}
        
        # Convertir en DataFrame pour faciliter le traitement
        df_ocr = pd.DataFrame(ocr_data)
        
        # Filtrer les lignes avec du texte
        df_ocr = df_ocr[df_ocr['conf'] > 0]
        df_ocr['text'] = df_ocr['text'].astype(str).str.strip()
        df_ocr = df_ocr[df_ocr['text'] != '']
        
        if df_ocr.empty:
            current_app.logger.warning("Aucun texte détecté dans l'image")
            return {'error': 'Aucun texte détecté dans l\'image'}
        
        current_app.logger.info(f"Texte filtré: {len(df_ocr)} mots, confiance moyenne: {df_ocr['conf'].mean():.1f}%")
        
        # RECONSTITUER LE TABLEAU STRUCTURÉ
        tableau_data = []
        headers = []
        
        # Grouper les mots par lignes (basé sur la coordonnée Y)
        lines = {}
        for idx, row in df_ocr.iterrows():
            top = row['top']
            left = row['left']
            text = row['text']
            
            # Trouver la ligne la plus proche (tolérance de 10 pixels)
            found_line = None
            for line_top in lines.keys():
                if abs(top - line_top) < 10:
                    found_line = line_top
                    break
            
            if found_line is None:
                found_line = top
            
            if found_line not in lines:
                lines[found_line] = []
            
            lines[found_line].append((left, text))
        
        # Trier les lignes par position verticale
        sorted_lines = sorted(lines.items(), key=lambda x: x[0])
        current_app.logger.info(f"Lignes détectées: {len(sorted_lines)}")
        
        # Détecter les colonnes basées sur la position horizontale
        try:
            column_positions = detect_column_positions(sorted_lines)
            current_app.logger.info(f"Colonnes détectées: {len(column_positions)}")
        except Exception as col_error:
            current_app.logger.warning(f"Erreur détection colonnes: {col_error}")
            # Utiliser une seule colonne par défaut
            column_positions = [(0, img.size[0])]
        
        # Reconstruire le tableau
        for line_top, words in sorted_lines:
            # Trier les mots de gauche à droite
            words.sort(key=lambda x: x[0])
            
            # Répartir les mots dans les colonnes
            row_data = [''] * len(column_positions)
            
            for left, text in words:
                # Trouver la colonne appropriée
                for i, (col_left, col_right) in enumerate(column_positions):
                    if col_left <= left <= col_right:
                        if row_data[i]:
                            row_data[i] += ' ' + text
                        else:
                            row_data[i] = text
                        break
            
            # Ajouter la ligne si elle contient des données
            if any(cell.strip() for cell in row_data):
                tableau_data.append(row_data)
        
        current_app.logger.info(f"Lignes de tableau reconstruites: {len(tableau_data)}")
        
        # Détecter l'en-tête (première ligne significative)
        if tableau_data:
            # Vérifier si la première ligne contient des mots typiques d'en-tête
            first_row_text = ' '.join([str(cell) for cell in tableau_data[0] if cell]).lower()
            header_keywords = ['réf', 'dsp', 'nom', 'valeur', 'total', 'montant', 'quantité', 'code', 'libellé', 'prix']
            
            if any(keyword in first_row_text for keyword in header_keywords) and len(tableau_data) > 1:
                headers = tableau_data[0]
                tableau_data = tableau_data[1:]
                current_app.logger.info(f"En-tête détecté: {headers}")
        
        # Créer le DataFrame final
        if headers:
            # Nettoyer les noms de colonnes
            cleaned_headers = []
            for header in headers:
                if isinstance(header, str):
                    cleaned_headers.append(header.strip())
                else:
                    cleaned_headers.append(f'Colonne {len(cleaned_headers) + 1}')
            
            # S'assurer que toutes les lignes ont le même nombre de colonnes
            max_cols = len(cleaned_headers)
            uniform_data = []
            for row in tableau_data:
                if len(row) < max_cols:
                    uniform_data.append(row + [''] * (max_cols - len(row)))
                elif len(row) > max_cols:
                    uniform_data.append(row[:max_cols])
                else:
                    uniform_data.append(row)
            
            df_final = pd.DataFrame(uniform_data, columns=cleaned_headers)
        else:
            # Créer des noms de colonnes génériques
            num_columns = max(len(row) for row in tableau_data) if tableau_data else 1
            col_names = [f'Colonne {i+1}' for i in range(num_columns)]
            
            # Uniformiser la longueur des lignes
            uniform_data = []
            for row in tableau_data:
                if len(row) < num_columns:
                    uniform_data.append(row + [''] * (num_columns - len(row)))
                elif len(row) > num_columns:
                    uniform_data.append(row[:num_columns])
                else:
                    uniform_data.append(row)
            
            df_final = pd.DataFrame(uniform_data, columns=col_names)
        
        # Si le tableau est vide ou très petit, utiliser une extraction simple
        if len(df_final) <= 1 or (len(df_final.columns) == 1 and len(df_final) < 3):
            current_app.logger.info("Tableau trop petit, extraction simple")
            # Extraction simple ligne par ligne
            simple_data = []
            for _, words in sorted_lines:
                words.sort(key=lambda x: x[0])
                line_text = ' '.join([word[1] for word in words])
                simple_data.append([line_text])
            
            df_final = pd.DataFrame(simple_data, columns=['Texte extrait'])
        
        current_app.logger.info(f"DataFrame final: {len(df_final)} lignes x {len(df_final.columns)} colonnes")
        
        # Créer Excel avec UNE SEULE FEUILLE
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Écrire le tableau principal
            sheet_name = 'Données extraites'
            df_final.to_excel(writer, index=False, sheet_name=sheet_name)
            
            # Personnaliser la feuille
            worksheet = writer.sheets[sheet_name]
            
            # Ajuster la largeur des colonnes
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Max 50 caractères
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Ajouter des statistiques
            if not df_final.empty:
                # Calculer les statistiques
                total_rows = len(df_final)
                total_columns = len(df_final.columns)
                total_cells = total_rows * total_columns
                avg_confidence = df_ocr['conf'].mean() if not df_ocr.empty else 0
                filled_cells = sum(1 for row in df_final.values.flatten() if str(row).strip())
                
                # Créer un DataFrame pour les statistiques
                stats_data = {
                    'Statistique': [
                        'Fichier source',
                        'Date d\'extraction',
                        'Type d\'image',
                        'Taille de l\'image',
                        'Lignes extraites',
                        'Colonnes détectées',
                        'Cellules remplies',
                        'Confiance moyenne OCR',
                        'Taux de remplissage'
                    ],
                    'Valeur': [
                        file.filename,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        img.format if hasattr(img, 'format') else 'Inconnu',
                        f"{img.size[0]}x{img.size[1]}",
                        total_rows,
                        total_columns,
                        f"{filled_cells}/{total_cells}",
                        f"{avg_confidence:.1f}%" if avg_confidence > 0 else "N/A",
                        f"{(filled_cells/total_cells*100):.1f}%" if total_cells > 0 else "0%"
                    ]
                }
                
                stats_df = pd.DataFrame(stats_data)
                
                # Écrire les statistiques après les données
                start_row = total_rows + 3  # 2 lignes d'espace
                stats_df.to_excel(
                    writer, 
                    index=False, 
                    startrow=start_row, 
                    sheet_name=sheet_name, 
                    header=False
                )
                
                # Ajouter une note
                note_row = start_row + len(stats_df) + 2
                worksheet.cell(row=note_row, column=1, 
                              value="Note: Pour de meilleurs résultats, utilisez des images nettes avec")
                worksheet.cell(row=note_row + 1, column=1, 
                              value="un bon contraste et des tableaux bien alignés.")
        
        output.seek(0)
        file_size = len(output.getvalue())
        current_app.logger.info(f"Fichier Excel généré: {file_size} bytes")
        
        filename = f"{os.path.splitext(file.filename)[0]}_extrait.xlsx"
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        current_app.logger.error(f"Erreur Image->Excel: {str(e)}\n{traceback.format_exc()}")
        return {'error': f'Erreur d\'extraction: {str(e)}'}

def detect_column_positions(sorted_lines, min_column_width=50):
    """Détecte les positions des colonnes basées sur les données."""
    column_positions = []
    
    # Collecter toutes les positions X des mots
    all_left_positions = []
    for _, words in sorted_lines:
        for left, _ in words:
            all_left_positions.append(left)
    
    if not all_left_positions:
        return [(0, 1000)]  # Par défaut
    
    # Trier et regrouper les positions
    all_left_positions.sort()
    
    # Détecter les clusters de positions (colonnes)
    current_column = None
    min_gap = min_column_width  # Espace minimum entre colonnes
    
    for pos in all_left_positions:
        if current_column is None:
            current_column = [pos, pos]
        elif pos - current_column[1] < min_gap:
            # Dans la même colonne
            current_column[1] = max(current_column[1], pos)
        else:
            # Nouvelle colonne
            column_positions.append((current_column[0], current_column[1]))
            current_column = [pos, pos]
    
    if current_column is not None:
        column_positions.append((current_column[0], current_column[1]))
    
    # Si aucune colonne détectée, retourner une colonne par défaut
    if not column_positions:
        min_pos = min(all_left_positions)
        max_pos = max(all_left_positions)
        column_positions = [(min_pos, max_pos)]
    
    return column_positions

def preprocess_image_for_ocr(img):
    """Prétraite l'image pour améliorer la reconnaissance OCR."""
    try:
        # Convertir en niveaux de gris
        if img.mode != 'L':
            img = img.convert('L')
        
        # Améliorer le contraste
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        
        # Améliorer la netteté
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        
        return img
    except Exception as e:
        current_app.logger.warning(f"Erreur prétraitement image: {e}")
        return img


def detect_column_positions(sorted_lines, min_column_width=50):
    """Détecte les positions des colonnes basées sur les données."""
    column_positions = []
    
    # Collecter toutes les positions X des mots
    all_left_positions = []
    for _, words in sorted_lines:
        for left, _ in words:
            all_left_positions.append(left)
    
    if not all_left_positions:
        return [(0, 1000)]  # Par défaut
    
    # Trier et regrouper les positions
    all_left_positions.sort()
    
    # Détecter les clusters de positions (colonnes)
    current_column = None
    min_gap = min_column_width  # Espace minimum entre colonnes
    
    for pos in all_left_positions:
        if current_column is None:
            current_column = [pos, pos]
        elif pos - current_column[1] < min_gap:
            # Dans la même colonne
            current_column[1] = max(current_column[1], pos)
        else:
            # Nouvelle colonne
            column_positions.append((current_column[0], current_column[1]))
            current_column = [pos, pos]
    
    if current_column is not None:
        column_positions.append((current_column[0], current_column[1]))
    
    # Si aucune colonne détectée, retourner une colonne par défaut
    if not column_positions:
        min_pos = min(all_left_positions)
        max_pos = max(all_left_positions)
        column_positions = [(min_pos, max_pos)]
    
    return column_positions

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
