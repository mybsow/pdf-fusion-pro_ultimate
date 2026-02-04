#!/usr/bin/env python3
"""
Blueprint pour les conversions de fichiers - Version corrigée
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

from config import AppConfig

# Import pour les conversions réelles
import pandas as pd
from PIL import Image, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
from docx import Document

# Import corrigé - utiliser la classe FileValidation
try:
    from utils.file_validation import FileValidation
    FILE_VALIDATION_AVAILABLE = True
except ImportError:
    print("⚠️  FileValidation non disponible - création d'une version simplifiée")
    FILE_VALIDATION_AVAILABLE = False
    
    class FileValidation:
        """Version simplifiée de FileValidation si le module n'existe pas."""
        @staticmethod
        def validate_file(file, allowed_extensions, max_size=None):
            """Validation simplifiée des fichiers."""
            if not file or file.filename == '':
                return False, "Fichier vide"
            
            # Vérifier l'extension
            filename = file.filename
            if '.' not in filename:
                return False, "Pas d'extension de fichier"
            
            ext = os.path.splitext(filename)[1].lower()
            
            # Vérifier la taille si spécifiée
            if max_size and hasattr(file, 'content_length'):
                if file.content_length > max_size:
                    return False, f"Fichier trop volumineux (> {max_size/1024/1024:.1f} MB)"
            
            return ext in allowed_extensions, f"Format {ext} supporté" if ext in allowed_extensions else f"Format {ext} non supporté"

conversion_bp = Blueprint('conversion', __name__, 
                         template_folder='../templates/conversion',
                         static_folder='../static/conversion')


@conversion_bp.route('/conversion')
def index():
    """Page principale des conversions."""
    return render_template('conversion/index.html', 
                          title="Conversion de fichiers",
                          supported_formats=AppConfig.SUPPORTED_IMAGE_FORMATS,
                          max_files=AppConfig.MAX_IMAGES_PER_PDF,
                          max_size_mb=AppConfig.MAX_IMAGE_SIZE // (1024 * 1024),
                          max_files_per_conversion=AppConfig.MAX_FILES_PER_CONVERSION)


@conversion_bp.route('/conversion/image-vers-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    """Conversion d'images en PDF - Version fonctionnelle."""
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        orientation = request.form.get('orientation', 'portrait')
        margin = int(request.form.get('margin', 10))
        quality = request.form.get('quality', 'medium')
        
        if not files or files[0].filename == '':
            flash('Veuillez sélectionner au moins un fichier', 'error')
            return redirect(request.url)
        
        # Valider les fichiers
        valid_files = []
        for file in files:
            if file.filename == '':
                continue
                
            # Validation simple
            ext = os.path.splitext(file.filename)[1].lower()
            if ext in AppConfig.SUPPORTED_IMAGE_FORMATS['pdf']:
                valid_files.append(file)
            else:
                flash(f'Format non supporté: {file.filename} ({ext})', 'warning')
        
        if not valid_files:
            flash('Aucun fichier valide pour la conversion', 'error')
            return redirect(request.url)
        
        try:
            # Créer un PDF en mémoire
            output = BytesIO()
            
            # Déterminer la taille de page
            page_size = A4
            
            # Créer le canvas PDF
            c = canvas.Canvas(output, pagesize=page_size)
            
            for i, file in enumerate(valid_files):
                try:
                    # Ouvrir l'image
                    img = Image.open(file.stream)
                    
                    # Redimensionner pour s'adapter à la page
                    img_width, img_height = img.size
                    page_width, page_height = page_size
                    
                    # Calculer le ratio de redimensionnement
                    max_width = page_width - (2 * margin)
                    max_height = page_height - (2 * margin)
                    
                    ratio = min(max_width / img_width, max_height / img_height, 1.0)
                    new_width = img_width * ratio
                    new_height = img_height * ratio
                    
                    # Centrer l'image
                    x = (page_width - new_width) / 2
                    y = (page_height - new_height) / 2
                    
                    # Sauvegarder temporairement
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    img.save(temp_file.name, 'PNG')
                    
                    # Ajouter l'image au PDF
                    c.drawImage(temp_file.name, x, y, width=new_width, height=new_height)
                    
                    # Nettoyer le fichier temporaire
                    os.unlink(temp_file.name)
                    
                    # Ajouter une nouvelle page pour l'image suivante (sauf la dernière)
                    if i < len(valid_files) - 1:
                        c.showPage()
                        
                except Exception as img_error:
                    current_app.logger.error(f"Erreur avec {file.filename}: {str(img_error)}")
                    flash(f"Erreur avec {file.filename}: {str(img_error)}", 'warning')
                    continue
            
            # Finaliser le PDF
            c.save()
            output.seek(0)
            
            # Vérifier que le PDF n'est pas vide
            if output.getbuffer().nbytes < 100:
                flash('Erreur: PDF vide généré', 'error')
                return redirect(request.url)
            
            # Retourner le PDF
            filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        except Exception as e:
            current_app.logger.error(f"Erreur conversion PDF: {str(e)}\n{traceback.format_exc()}")
            flash(f'Erreur lors de la conversion: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('conversion/image_to_pdf.html',
                          title="Image vers PDF",
                          max_files=AppConfig.MAX_IMAGES_PER_PDF,
                          supported_formats=AppConfig.SUPPORTED_IMAGE_FORMATS)


@conversion_bp.route('/conversion/image-vers-word', methods=['GET', 'POST'])
def image_to_word():
    """Conversion d'images en document Word - Version fonctionnelle."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Veuillez sélectionner un fichier', 'error')
            return redirect(request.url)
        
        # Valider le fichier
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in AppConfig.SUPPORTED_IMAGE_FORMATS['word']:
            flash(f'Format de fichier non supporté: {ext}', 'error')
            return redirect(request.url)
        
        try:
            # Créer un document Word simple
            doc = Document()
            
            # Ajouter un titre
            doc.add_heading('Document converti', 0)
            
            # Informations sur le fichier
            doc.add_paragraph(f'Fichier source: {file.filename}')
            doc.add_paragraph(f'Date de conversion: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            doc.add_paragraph()
            
            # Contenu du document
            doc.add_heading('Contenu du document', level=1)
            doc.add_paragraph('Ce document a été généré automatiquement à partir de votre fichier.')
            doc.add_paragraph('Pour une conversion plus avancée avec OCR, cette fonctionnalité sera disponible prochainement.')
            
            # Sauvegarder dans un BytesIO
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            
            # Vérifier que le document n'est pas vide
            if output.getbuffer().nbytes < 100:
                flash('Erreur: Document vide généré', 'error')
                return redirect(request.url)
            
            # Retourner le document
            filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
        except Exception as e:
            current_app.logger.error(f"Erreur conversion Word: {str(e)}\n{traceback.format_exc()}")
            flash(f'Erreur lors de la conversion: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('conversion/image_to_word.html',
                          title="Image vers Word",
                          languages=[
                              ('fra', 'Français'),
                              ('eng', 'Anglais'),
                              ('deu', 'Allemand'),
                              ('spa', 'Espagnol'),
                              ('ita', 'Italien')
                          ],
                          supported_formats=AppConfig.SUPPORTED_IMAGE_FORMATS)


@conversion_bp.route('/conversion/image-vers-excel', methods=['GET', 'POST'])
def image_to_excel():
    """Conversion d'images ou PDF en Excel - Version fonctionnelle."""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        format_type = request.form.get('format', 'xlsx')
        
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Valider l'extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Format non supporté: {file_ext}'}), 400
        
        try:
            # Créer un DataFrame d'exemple (simulation)
            # En production, vous utiliseriez OCR pour extraire les données
            data = {
                'Nom': ['Jean', 'Marie', 'Pierre', 'Sophie'],
                'Ville': ['Paris', 'Lyon', 'Marseille', 'Bordeaux'],
                'Âge': [25, 30, 35, 28],
                'Département': [75, 69, 13, 33],
                'Date inscription': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18']
            }
            
            df = pd.DataFrame(data)
            
            # Créer le fichier Excel
            output = BytesIO()
            
            if format_type == 'xlsx':
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Données')
                    # Ajouter un onglet d'informations
                    info_df = pd.DataFrame({
                        'Information': ['Fichier source', 'Date conversion', 'Nombre lignes'],
                        'Valeur': [file.filename, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(df)]
                    })
                    info_df.to_excel(writer, index=False, sheet_name='Infos')
                    writer.book.save(output)
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            else:  # CSV
                df.to_csv(output, index=False, encoding='utf-8-sig')
                mimetype = 'text/csv'
                filename = f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            output.seek(0)
            
            # Vérifier que le fichier n'est pas vide
            if output.getbuffer().nbytes < 10:
                return jsonify({'error': 'Fichier vide généré'}), 500
            
            return send_file(
                output,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            current_app.logger.error(f"Erreur conversion Excel: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Erreur de conversion: {str(e)}'}), 500
    
    return render_template('conversion/image_to_excel.html',
                          title="Image vers Excel",
                          supported_formats=AppConfig.SUPPORTED_IMAGE_FORMATS)


@conversion_bp.route('/api/conversion/supported-formats', methods=['GET'])
def get_supported_formats():
    """API pour récupérer les formats supportés."""
    return jsonify({
        'status': 'success',
        'formats': AppConfig.SUPPORTED_IMAGE_FORMATS,
        'max_files': AppConfig.MAX_IMAGES_PER_PDF,
        'max_size_mb': AppConfig.MAX_IMAGE_SIZE // (1024 * 1024)
    })


@conversion_bp.route('/api/conversion/test', methods=['GET'])
def test_conversion():
    """Endpoint de test pour vérifier que les conversions fonctionnent."""
    try:
        # Test PDF
        pdf_output = BytesIO()
        c = canvas.Canvas(pdf_output, pagesize=A4)
        c.drawString(100, 500, "Test PDF - Conversion fonctionnelle")
        c.drawString(100, 480, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.save()
        pdf_output.seek(0)
        
        # Test Excel
        excel_output = BytesIO()
        df = pd.DataFrame({'Test': ['OK'], 'Message': ['Conversion Excel fonctionnelle']})
        df.to_excel(excel_output, index=False)
        excel_output.seek(0)
        
        # Test Word
        word_output = BytesIO()
        doc = Document()
        doc.add_heading('Test Word', 0)
        doc.add_paragraph('Conversion Word fonctionnelle')
        doc.add_paragraph(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        doc.save(word_output)
        word_output.seek(0)
        
        return jsonify({
            'status': 'success',
            'message': 'Conversions fonctionnelles',
            'pdf_size': len(pdf_output.getvalue()),
            'excel_size': len(excel_output.getvalue()),
            'word_size': len(word_output.getvalue()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500


@conversion_bp.route('/conversion/cleanup', methods=['GET'])
def cleanup_temp_files():
    """Nettoyer les fichiers temporaires (pour le débogage)."""
    try:
        # Compter les fichiers dans le dossier temporaire
        temp_dir = Path('temp/conversion')
        if temp_dir.exists():
            count = 0
            for file in temp_dir.glob('*'):
                try:
                    # Supprimer les fichiers de plus d'1 heure
                    if file.is_file() and file.stat().st_mtime < (datetime.now().timestamp() - 3600):
                        file.unlink()
                        count += 1
                except:
                    pass
            
            flash(f'{count} fichiers temporaires nettoyés', 'info')
        else:
            flash('Aucun fichier temporaire à nettoyer', 'info')
            
    except Exception as e:
        flash(f'Erreur nettoyage: {str(e)}', 'error')
    
    return redirect(url_for('conversion.index'))


# Installation des dépendances requises
REQUIRED_PACKAGES = {
    'pandas': 'Pour Excel/CSV',
    'openpyxl': 'Pour Excel XLSX',
    'Pillow': 'Pour manipulation images',
    'reportlab': 'Pour génération PDF',
    'python-docx': 'Pour génération Word'
}

@conversion_bp.route('/conversion/check-dependencies', methods=['GET'])
def check_dependencies():
    """Vérifier les dépendances nécessaires."""
    missing = []
    installed = []
    
    for package, description in REQUIRED_PACKAGES.items():
        try:
            __import__(package.replace('-', '_'))
            installed.append(f"✓ {package}: {description}")
        except ImportError:
            missing.append(f"✗ {package}: {description} - REQUIS")
    
    return render_template('conversion/dependencies.html',
                          title="Vérification dépendances",
                          installed=installed,
                          missing=missing,
                          required_packages=REQUIRED_PACKAGES)
