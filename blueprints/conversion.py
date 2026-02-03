#!/usr/bin/env python3
"""
Blueprint pour les conversions de fichiers
"""

from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import shutil

from config import AppConfig
from utils.file_validation import validate_file
from managers.conversion_manager import ConversionManager

conversion_bp = Blueprint('conversion', __name__, 
                         template_folder='../templates/conversion',
                         static_folder='../static/conversion')

# Initialiser le manager de conversion
conversion_manager = ConversionManager()


@conversion_bp.route('/conversion')
def index():
    """Page principale des conversions."""
    return render_template('conversion/index.html', 
                          title="Conversion de fichiers",
                          supported_formats=AppConfig.SUPPORTED_IMAGE_FORMATS,
                          max_files=AppConfig.MAX_IMAGES_PER_CONVERSION,
                          max_size_mb=AppConfig.MAX_IMAGE_SIZE // (1024 * 1024))


@conversion_bp.route('/conversion/image-vers-pdf', methods=['GET', 'POST'])
def image_to_pdf():
    """Conversion d'images en PDF."""
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
            if validate_file(file, AppConfig.SUPPORTED_IMAGE_FORMATS['pdf']):
                valid_files.append(file)
            else:
                flash(f'Format non supporté: {file.filename}', 'warning')
        
        if not valid_files:
            flash('Aucun fichier valide pour la conversion', 'error')
            return redirect(request.url)
        
        # Convertir les images en PDF
        try:
            pdf_path = conversion_manager.images_to_pdf(
                valid_files, 
                orientation=orientation,
                margin=margin,
                quality=quality
            )
            
            # Enregistrer la statistique
            from managers.stats_manager import stats_manager
            stats_manager.record_conversion('image_to_pdf', len(valid_files))
            
            # Retourner le PDF
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mimetype='application/pdf'
            )
            
        except Exception as e:
            flash(f'Erreur lors de la conversion: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('conversion/image_to_pdf.html',
                          title="Image vers PDF",
                          max_files=AppConfig.MAX_IMAGES_PER_CONVERSION)


@conversion_bp.route('/conversion/image-vers-word', methods=['GET', 'POST'])
def image_to_word():
    """Conversion d'images en document Word."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        ocr_enabled = request.form.get('ocr', 'false') == 'true'
        language = request.form.get('language', 'fra')
        
        if file.filename == '':
            flash('Veuillez sélectionner un fichier', 'error')
            return redirect(request.url)
        
        # Valider le fichier
        if not validate_file(file, AppConfig.SUPPORTED_IMAGE_FORMATS['word']):
            flash('Format de fichier non supporté', 'error')
            return redirect(request.url)
        
        # Convertir en Word
        try:
            docx_path = conversion_manager.to_word(
                file,
                ocr_enabled=ocr_enabled,
                language=language
            )
            
            # Enregistrer la statistique
            from managers.stats_manager import stats_manager
            stats_manager.record_conversion('image_to_word', 1)
            
            # Retourner le document Word
            return send_file(
                docx_path,
                as_attachment=True,
                download_name=f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
        except Exception as e:
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
                          ])


@conversion_bp.route('/conversion/image-vers-excel', methods=['GET', 'POST'])
def image_to_excel():
    """Conversion d'images ou PDF en Excel (avec OCR pour les tableaux)."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        detect_tables = request.form.get('detect_tables', 'true') == 'true'
        language = request.form.get('language', 'fra')
        
        if file.filename == '':
            flash('Veuillez sélectionner un fichier', 'error')
            return redirect(request.url)
        
        # Valider le fichier
        if not validate_file(file, AppConfig.SUPPORTED_IMAGE_FORMATS['excel']):
            flash('Format de fichier non supporté', 'error')
            return redirect(request.url)
        
        # Convertir en Excel
        try:
            excel_path = conversion_manager.to_excel(
                file,
                detect_tables=detect_tables,
                language=language
            )
            
            # Enregistrer la statistique
            from managers.stats_manager import stats_manager
            stats_manager.record_conversion('image_to_excel', 1)
            
            # Retourner le fichier Excel
            return send_file(
                excel_path,
                as_attachment=True,
                download_name=f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            flash(f'Erreur lors de la conversion: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('conversion/image_to_excel.html',
                          title="Image vers Excel")


@conversion_bp.route('/api/conversion/supported-formats', methods=['GET'])
def get_supported_formats():
    """API pour récupérer les formats supportés."""
    return jsonify({
        'status': 'success',
        'formats': AppConfig.SUPPORTED_IMAGE_FORMATS,
        'max_files': AppConfig.MAX_IMAGES_PER_CONVERSION,
        'max_size_mb': AppConfig.MAX_IMAGE_SIZE // (1024 * 1024)
    })


@conversion_bp.route('/api/conversion/convert', methods=['POST'])
def api_convert():
    """API pour les conversions programmatiques."""
    data = request.json
    
    if not data or 'files' not in data:
        return jsonify({'status': 'error', 'message': 'Aucun fichier fourni'}), 400
    
    # Implémenter la logique de conversion API
    # (similaire aux routes normales mais avec réponse JSON)
    
    return jsonify({'status': 'success', 'message': 'Conversion API'})
