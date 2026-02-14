#!/usr/bin/env python3
"""
Blueprint pour les conversions de fichiers - Version universelle
"""
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import sys
import os
os.environ["OMP_THREAD_LIMIT"] = "1"
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
import shutil
import traceback
from io import BytesIO
import zipfile
import logging

# Configuration du logging
logger = logging.getLogger(__name__)

# Ajouter la racine du projet au sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import du manager de conversion
try:
    from managers.conversion_manager import ConversionManager
    conversion_manager = ConversionManager()  # Instance globale du manager de conversion
    HAS_CONVERSION_MANAGER = True
except ImportError:
    conversion_manager = None
    HAS_CONVERSION_MANAGER = False
    logger.warning("⚠️ ConversionManager non disponible")

# Import de la configuration
try:
    from config import AppConfig
except ImportError:
    # Fallback: définir une classe de config par défaut
    class AppConfig:
        OCR_ENABLED = True
        NAME = "PDF Fusion Pro"
        VERSION = "1.0.0"
        DEVELOPER_NAME = "Votre Nom"
        DEVELOPER_EMAIL = "contact@example.com"
        HOSTING = "Render"
        DOMAIN = "pdffusionpro.com"

# ============================
# IMPORTATIONS AVEC GESTION D'ERREURS
# ============================

# Import pour les conversions
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False
    logger.warning("[WARN] pandas non installé, conversions CSV/Excel désactivées")

try:
    from PIL import Image, ImageEnhance
    HAS_PILLOW = True
except ImportError:
    Image = ImageEnhance = None
    HAS_PILLOW = False
    logger.warning("[WARN] PIL/Pillow non installé, conversions images désactivées")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.utils import ImageReader
    HAS_REPORTLAB = True
except ImportError:
    canvas = None
    letter = A4 = None
    ImageReader = None
    HAS_REPORTLAB = False
    logger.warning("[WARN] reportlab non installé, génération PDF désactivée")

try:
    from docx import Document
    from docx.shared import Inches
    HAS_DOCX = True
except ImportError:
    Document = None
    Inches = None
    HAS_DOCX = False
    logger.warning("[WARN] python-docx non installé, conversions Word désactivées")

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    pypdf = None
    HAS_PYPDF = False
    logger.warning("[WARN] pypdf non installé, manipulations PDF désactivées")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
    logger.warning("[WARN] numpy non installé, certains traitements désactivés")

# OCR avec Tesseract
try:
    import pytesseract
    from pytesseract import Output
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    HAS_TESSERACT = True
except ImportError:
    pytesseract = None
    Output = None
    HAS_TESSERACT = False
    logger.warning("[WARN] pytesseract non installé, OCR désactivé")

# PDF -> images
try:
    from pdf2image import convert_from_bytes, convert_from_path
    from pdf2image.pdf2image import pdfinfo_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    convert_from_bytes = None
    convert_from_path = None
    pdfinfo_from_path = None
    HAS_PDF2IMAGE = False
    logger.warning("[WARN] pdf2image non installé, conversion PDF impossible")

# HTML to PDF
try:
    import pdfkit
    HAS_PDFKIT = True
except ImportError:
    pdfkit = None
    HAS_PDFKIT = False
    logger.warning("[WARN] pdfkit non installé, conversions HTML->PDF désactivées")

try:
    import weasyprint
    HAS_WEASYPRINT = True
except ImportError:
    weasyprint = None
    HAS_WEASYPRINT = False
    logger.warning("[WARN] weasyprint non installé, conversions HTML->PDF désactivées")

# PowerPoint
try:
    from pptx import Presentation
    from pptx.util import Inches
    HAS_PPTX = True
except ImportError:
    Presentation = None
    Inches = None
    HAS_PPTX = False
    logger.warning("[WARN] python-pptx non installé, conversions PowerPoint désactivées")

# Word / Excel / PPT -> PDF via LibreOffice
import subprocess

# État des dépendances
DEPS_STATUS = {
    'pandas': HAS_PANDAS,
    'Pillow': HAS_PILLOW,
    'reportlab': HAS_REPORTLAB,
    'python-docx': HAS_DOCX,
    'pypdf': HAS_PYPDF,
    'numpy': HAS_NUMPY,
    'tesseract': HAS_TESSERACT,
    'pdf2image': HAS_PDF2IMAGE,
    'pdfkit': HAS_PDFKIT,
    'weasyprint': HAS_WEASYPRINT,
    'python-pptx': HAS_PPTX,
    'conversion_manager': HAS_CONVERSION_MANAGER
}

print(f"📊 État des dépendances: {DEPS_STATUS}")

# Chemin absolu vers le dossier templates
TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))

conversion_bp = Blueprint('conversion', __name__,
                          template_folder=TEMPLATES_DIR,
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
        'max_files': 5,
        'deps': ['reportlab', 'libreoffice']
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
        'max_files': 5,
        'deps': ['reportlab', 'libreoffice']
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
        'max_files': 5,
        'deps': ['reportlab', 'libreoffice']
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
        'max_files': 20,
        'deps': ['Pillow', 'reportlab']
    },
    
    'jpg-en-pdf': {
        'template': 'image_to_pdf.html',
        'title': 'JPG vers PDF',
        'description': 'Convertissez vos images JPG en PDF',
        'from_format': 'JPG',
        'to_format': 'PDF',
        'icon': 'file-image',
        'color': '#e74c3c',
        'accept': '.jpg,.jpeg',
        'max_files': 20,
        'deps': ['Pillow', 'reportlab']
    },
    
    'png-en-pdf': {
        'template': 'image_to_pdf.html',
        'title': 'PNG vers PDF',
        'description': 'Convertissez vos images PNG en PDF',
        'from_format': 'PNG',
        'to_format': 'PDF',
        'icon': 'file-image',
        'color': '#e74c3c',
        'accept': '.png',
        'max_files': 20,
        'deps': ['Pillow', 'reportlab']
    },
    
    'html-en-pdf': {
        'template': 'html_to_pdf.html',
        'title': 'HTML vers PDF',
        'description': 'Convertissez vos pages HTML en PDF',
        'from_format': 'HTML',
        'to_format': 'PDF',
        'icon': 'code',
        'color': '#f16529',
        'accept': '.html,.htm',
        'max_files': 1,
        'deps': ['weasyprint', 'pdfkit']
    },
    
    'txt-en-pdf': {
        'template': 'txt_to_pdf.html',
        'title': 'TXT vers PDF',
        'description': 'Convertissez vos fichiers texte en PDF',
        'from_format': 'TXT',
        'to_format': 'PDF',
        'icon': 'file-alt',
        'color': '#3498db',
        'accept': '.txt',
        'max_files': 1,
        'deps': ['reportlab']
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
        'max_files': 1,
        'deps': ['pypdf', 'python-docx']
    },
    
    'pdf-en-doc': {
        'template': 'pdf_to_doc.html',
        'title': 'PDF vers DOC',
        'description': 'Convertissez vos PDF en documents Word (format DOC)',
        'from_format': 'PDF',
        'to_format': 'DOC',
        'icon': 'file-word',
        'color': '#2b579a',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'python-docx']
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
        'max_files': 1,
        'deps': ['pypdf', 'pdf2image', 'pytesseract', 'pandas', 'openpyxl']
    },
    
    'pdf-en-ppt': {
        'template': 'pdf_to_ppt.html',
        'title': 'PDF vers PowerPoint',
        'description': 'Convertissez vos PDF en présentations PowerPoint modifiables',
        'from_format': 'PDF',
        'to_format': 'PowerPoint',
        'icon': 'file-powerpoint',
        'color': '#d24726',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pdf2image', 'Pillow', 'python-pptx']
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
        'max_files': 1,
        'deps': ['pdf2image']
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
        'max_files': 1,
        'deps': ['pypdf']
    },
    
    'pdf-en-html': {
        'template': 'pdf_to_html.html',
        'title': 'PDF vers HTML',
        'description': 'Convertissez vos PDF en pages HTML',
        'from_format': 'PDF',
        'to_format': 'HTML',
        'icon': 'code',
        'color': '#f16529',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },
    
    'pdf-en-txt': {
        'template': 'pdf_to_txt.html',
        'title': 'PDF vers TXT',
        'description': 'Extrayez le texte de vos PDF en fichiers texte',
        'from_format': 'PDF',
        'to_format': 'TXT',
        'icon': 'file-alt',
        'color': '#3498db',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },
    
    # ==================== OUTILS PDF ====================
    'proteger-pdf': {
        'template': 'protect_pdf.html',
        'title': 'Protéger PDF',
        'description': 'Ajoutez un mot de passe pour protéger vos PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'lock',
        'color': '#e67e22',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
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
        'max_files': 1,
        'deps': ['pypdf']
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
        'max_files': 1,
        'deps': ['Pillow', 'pytesseract', 'python-docx']
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
        'max_files': 1,
        'deps': ['Pillow', 'pytesseract', 'pandas', 'openpyxl']
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
        'max_files': 5,
        'deps': ['pandas', 'openpyxl']
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
        'max_files': 5,
        'deps': ['pandas']
    }
}

def check_dependencies(deps_list):
    """Vérifie si les dépendances requises sont disponibles."""
    if not deps_list:
        return True, []
    
    missing = []
    for dep in deps_list:
        if dep == 'reportlab' and not HAS_REPORTLAB:
            missing.append(dep)
        elif dep == 'Pillow' and not HAS_PILLOW:
            missing.append(dep)
        elif dep == 'pypdf' and not HAS_PYPDF:
            missing.append(dep)
        elif dep == 'python-docx' and not HAS_DOCX:
            missing.append(dep)
        elif dep == 'pytesseract' and not HAS_TESSERACT:
            missing.append(dep)
        elif dep == 'pdf2image' and not HAS_PDF2IMAGE:
            missing.append(dep)
        elif dep == 'pandas' and not HAS_PANDAS:
            missing.append(dep)
        elif dep == 'python-pptx' and not HAS_PPTX:
            missing.append(dep)
        elif dep == 'pdfkit' and not HAS_PDFKIT:
            missing.append(dep)
        elif dep == 'weasyprint' and not HAS_WEASYPRINT:
            missing.append(dep)
        elif dep == 'openpyxl':
            try:
                import openpyxl
            except ImportError:
                missing.append(dep)
        elif dep == 'libreoffice':
            try:
                result = subprocess.run(['which', 'libreoffice'], capture_output=True, text=True)
                if result.returncode != 0:
                    missing.append(dep)
            except:
                missing.append(dep)
    
    return len(missing) == 0, missing

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================

@conversion_bp.route('/')
def index():
    """Page d'accueil des conversions."""
    try:
        # Organiser les conversions par catégorie
        categories = {
            'convert_to_pdf': {
                'title': 'Convertir en PDF',
                'icon': 'file-pdf',
                'color': '#e74c3c',
                'conversions': []
            },
            'convert_from_pdf': {
                'title': 'Convertir depuis PDF',
                'icon': 'file-pdf',
                'color': '#3498db',
                'conversions': []
            },
            'pdf_tools': {
                'title': 'Outils PDF',
                'icon': 'tools',
                'color': '#2ecc71',
                'conversions': []
            },
            'other_conversions': {
                'title': 'Autres conversions',
                'icon': 'exchange-alt',
                'color': '#9b59b6',
                'conversions': []
            }
        }
        
        # Convertir en PDF
        for conv_key in ['word-en-pdf', 'excel-en-pdf', 'powerpoint-en-pdf', 'image-en-pdf', 
                         'jpg-en-pdf', 'png-en-pdf', 'html-en-pdf', 'txt-en-pdf']:
            if conv_key in CONVERSION_MAP:
                conv = CONVERSION_MAP[conv_key].copy()
                conv['type'] = conv_key
                available, missing = check_dependencies(conv.get('deps', []))
                conv['available'] = available
                conv['missing_deps'] = missing
                categories['convert_to_pdf']['conversions'].append(conv)
        
        # Convertir depuis PDF
        for conv_key in ['pdf-en-word', 'pdf-en-doc', 'pdf-en-excel', 'pdf-en-ppt', 
                         'pdf-en-image', 'pdf-en-pdfa', 'pdf-en-html', 'pdf-en-txt']:
            if conv_key in CONVERSION_MAP:
                conv = CONVERSION_MAP[conv_key].copy()
                conv['type'] = conv_key
                available, missing = check_dependencies(conv.get('deps', []))
                conv['available'] = available
                conv['missing_deps'] = missing
                categories['convert_from_pdf']['conversions'].append(conv)
        
        # Outils PDF
        for conv_key in ['proteger-pdf', 'deverrouiller-pdf']:
            if conv_key in CONVERSION_MAP:
                conv = CONVERSION_MAP[conv_key].copy()
                conv['type'] = conv_key
                available, missing = check_dependencies(conv.get('deps', []))
                conv['available'] = available
                conv['missing_deps'] = missing
                categories['pdf_tools']['conversions'].append(conv)
        
        # Autres conversions
        for conv_key in ['image-en-word', 'image-en-excel', 'csv-en-excel', 'excel-en-csv']:
            if conv_key in CONVERSION_MAP:
                conv = CONVERSION_MAP[conv_key].copy()
                conv['type'] = conv_key
                available, missing = check_dependencies(conv.get('deps', []))
                conv['available'] = available
                conv['missing_deps'] = missing
                categories['other_conversions']['conversions'].append(conv)
        
        return render_template('conversion/index.html',
                              title="Convertisseur de fichiers universel",
                              categories=categories,
                              all_conversions=CONVERSION_MAP,
                              deps=DEPS_STATUS)
    
    except Exception as e:
        current_app.logger.error(f"❌ Erreur dans index(): {str(e)}")
        flash("Le service de conversion est temporairement indisponible. Veuillez réessayer plus tard.", "error")
        return render_template('conversion/index.html',
                              title="Convertisseur de fichiers",
                              categories={},
                              all_conversions={},
                              deps=DEPS_STATUS,
                              error=str(e))


@conversion_bp.route('/<string:conversion_type>', methods=['GET', 'POST'])
def universal_converter(conversion_type):
    """
    Route universelle pour toutes les conversions.
    """
    try:
        # Définir les outils PDF qui doivent rediriger vers le blueprint pdf
        pdf_tools = ['fusionner-pdf', 'diviser-pdf', 'compresser-pdf', 'rotation-pdf']
        
        # Si c'est un outil PDF, rediriger vers le blueprint pdf
        if conversion_type in pdf_tools:
            pdf_endpoints = {
                'fusionner-pdf': 'pdf.merge',
                'diviser-pdf': 'pdf.split', 
                'compresser-pdf': 'pdf.compress',
                'rotation-pdf': 'pdf.rotate'
            }
            endpoint = pdf_endpoints.get(conversion_type, 'pdf.index')
            return redirect(url_for(endpoint))
        
        # Vérifier si la conversion existe dans CONVERSION_MAP
        if conversion_type not in CONVERSION_MAP:
            flash(f'Type de conversion non supporté: {conversion_type}', 'error')
            return redirect(url_for('conversion.index'))
        
        config = CONVERSION_MAP[conversion_type].copy()
        config['type'] = conversion_type
        
        # Vérifier les dépendances
        available, missing = check_dependencies(config.get('deps', []))
        if not available:
            flash(f"Cette conversion nécessite les dépendances suivantes: {', '.join(missing)}", "warning")
        
        if request.method == 'POST':
            if not available:
                flash("Conversion non disponible - dépendances manquantes", "error")
                return redirect(url_for('conversion.universal_converter', conversion_type=conversion_type))
            return handle_conversion_request(conversion_type, request, config)
        
        # GET request - afficher le formulaire
        template_name = f"conversion/{config['template']}"
        
        try:
            return render_template(template_name,
                                  title=config['title'],
                                  description=config['description'],
                                  from_format=config['from_format'],
                                  to_format=config['to_format'],
                                  icon=config['icon'],
                                  color=config['color'],
                                  accept=config['accept'],
                                  max_files=config['max_files'],
                                  conversion_type=conversion_type,
                                  available=available,
                                  missing_deps=missing)
        except Exception as e:
            current_app.logger.error(f"Template non trouvé: {template_name} - {str(e)}")
            flash(f'Template non trouvé pour {conversion_type}', 'error')
            return redirect(url_for('conversion.index'))
        
    except Exception as e:
        current_app.logger.error(f"Erreur dans universal_converter: {str(e)}")
        flash(f"Erreur: {str(e)}", "error")
        return redirect(url_for('conversion.index'))


# -----------------------------
# Redirections vers outils PDF
# -----------------------------

@conversion_bp.route('/fusion-pdf')
@conversion_bp.route('/fusionner-pdf')
def fusion_redirect():
    return redirect(url_for('pdf.merge'), code=301)


@conversion_bp.route('/division-pdf')
@conversion_bp.route('/diviser-pdf')
def division_redirect():
    return redirect(url_for('pdf.split'), code=301)


@conversion_bp.route('/rotation-pdf')
@conversion_bp.route('/tourner-pdf')
def rotation_redirect():
    return redirect(url_for('pdf.rotate'), code=301)


@conversion_bp.route('/compression-pdf')
@conversion_bp.route('/compresser-pdf')
def compression_redirect():
    return redirect(url_for('pdf.compress'), code=301)


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
        
        if isinstance(result, dict) and 'error' in result:
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
        'word-en-pdf': convert_word_to_pdf if HAS_REPORTLAB else None,
        'excel-en-pdf': convert_excel_to_pdf if HAS_REPORTLAB else None,
        'powerpoint-en-pdf': convert_powerpoint_to_pdf if HAS_REPORTLAB else None,
        'image-en-pdf': convert_images_to_pdf if HAS_PILLOW and HAS_REPORTLAB else None,
        'jpg-en-pdf': convert_images_to_pdf if HAS_PILLOW and HAS_REPORTLAB else None,
        'png-en-pdf': convert_images_to_pdf if HAS_PILLOW and HAS_REPORTLAB else None,
        'html-en-pdf': convert_html_to_pdf if HAS_PDFKIT or HAS_WEASYPRINT else None,
        'txt-en-pdf': convert_txt_to_pdf if HAS_REPORTLAB else None,
        
        # Conversion depuis PDF
        'pdf-en-word': convert_pdf_to_word if HAS_PYPDF and HAS_DOCX else None,
        'pdf-en-doc': convert_pdf_to_doc if HAS_PYPDF and HAS_DOCX else None,
        'pdf-en-excel': convert_pdf_to_excel if HAS_PDF2IMAGE and HAS_TESSERACT and HAS_PANDAS else None,
        'pdf-en-ppt': convert_pdf_to_ppt if HAS_PDF2IMAGE and HAS_PILLOW and HAS_PPTX else None,
        'pdf-en-image': convert_pdf_to_images if HAS_PDF2IMAGE else None,
        'pdf-en-pdfa': convert_pdf_to_pdfa if HAS_PYPDF else None,
        'pdf-en-html': convert_pdf_to_html if HAS_PYPDF else None,
        'pdf-en-txt': convert_pdf_to_txt if HAS_PYPDF else None,
        
        # Outils PDF
        'deverrouiller-pdf': unlock_pdf if HAS_PYPDF else None,
        'proteger-pdf': protect_pdf if HAS_PYPDF else None,
        
        # Autres conversions
        'image-en-word': convert_image_to_word if HAS_PILLOW and HAS_TESSERACT and HAS_DOCX else None,
        'image-en-excel': convert_image_to_excel if HAS_PILLOW and HAS_TESSERACT and HAS_PANDAS else None,
        'csv-en-excel': convert_csv_to_excel if HAS_PANDAS else None,
        'excel-en-csv': convert_excel_to_csv if HAS_PANDAS else None,
    }
    
    if conversion_type not in conversion_functions:
        return {'error': 'Type de conversion non implémenté'}
    
    func = conversion_functions[conversion_type]
    if func is None:
        return {'error': 'Cette conversion nécessite des dépendances manquantes'}
    
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

def smart_ocr(img):
    """Retourne une liste de mots détectés dans l'image via Tesseract OCR"""
    if not HAS_TESSERACT or pytesseract is None:
        return []
    try:
        data = pytesseract.image_to_data(img, lang="fra+eng", output_type=Output.DICT)
        words = []
        for text in data.get("text", []):
            text = str(text).strip()
            if text:
                words.append(text)
        return words
    except Exception as e:
        print(f"[WARN] OCR échoué: {e}")
        return []


def convert_word_to_pdf(file, form_data=None):
    """Convertit Word en PDF."""
    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}
    
    try:
        # Sauvegarder le fichier temporairement
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Utiliser LibreOffice pour la conversion si disponible
        try:
            output_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', temp_dir, input_path
            ], check=True, capture_output=True)
            
            if os.path.exists(output_path):
                return send_file(
                    output_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}.pdf"
                )
        except:
            pass
        
        # Fallback: création basique avec reportlab
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        # Lire le contenu du fichier Word (simplifié)
        if file.filename.endswith('.docx') and HAS_DOCX:
            doc = Document(input_path)
            y = height - 50
            for para in doc.paragraphs:
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.setFont("Helvetica", 11)
                c.drawString(50, y, para.text[:80])
                y -= 15
        
        c.save()
        output.seek(0)
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur Word->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_excel_to_pdf(file, form_data=None):
    """Convertit Excel en PDF."""
    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}
    
    try:
        # Sauvegarder le fichier temporairement
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Utiliser LibreOffice pour la conversion
        try:
            output_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', temp_dir, input_path
            ], check=True, capture_output=True)
            
            if os.path.exists(output_path):
                return send_file(
                    output_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}.pdf"
                )
        except:
            pass
        
        return {'error': 'Conversion Excel->PDF non disponible sans LibreOffice'}
        
    except Exception as e:
        logger.error(f"Erreur Excel->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_powerpoint_to_pdf(file, form_data=None):
    """Convertit PowerPoint en PDF."""
    return convert_excel_to_pdf(file, form_data)


def convert_images_to_pdf(files, form_data=None):
    """Convertit des images en PDF."""
    if not HAS_PILLOW or not HAS_REPORTLAB:
        return {'error': 'Pillow ou reportlab non installé'}
    
    try:
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        for file in files:
            # Ouvrir l'image
            img = Image.open(file.stream)
            
            # Redimensionner pour tenir sur la page
            img_width, img_height = img.size
            ratio = min(width / img_width, height / img_height)
            new_width = img_width * ratio * 0.9
            new_height = img_height * ratio * 0.9
            
            # Centrer l'image
            x = (width - new_width) / 2
            y = (height - new_height) / 2
            
            # Sauvegarder temporairement
            temp_img = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            img.save(temp_img.name, 'JPEG')
            
            # Ajouter au PDF
            c.drawImage(temp_img.name, x, y, width=new_width, height=new_height)
            c.showPage()
            
            # Nettoyer
            os.unlink(temp_img.name)
        
        c.save()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name="images_converted.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur Images->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_word(file, form_data=None):
    """Convertit PDF en Word."""
    if not HAS_PYPDF or not HAS_DOCX:
        return {'error': 'pypdf ou python-docx non installé'}
    
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        # Créer un document Word
        doc = Document()
        
        # Extraire le texte de chaque page
        for page_num, page in enumerate(pdf_reader.pages):
            if page_num > 0:
                doc.add_page_break()
            
            text = page.extract_text()
            if text.strip():
                doc.add_paragraph(text)
        
        # Sauvegarder
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.docx"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->Word: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_doc(file, form_data=None):
    """Convertit PDF en DOC (Word)."""
    return convert_pdf_to_word(file, form_data)


def convert_pdf_to_excel(file_storage, form_data=None):
    """Convertit un PDF en Excel avec OCR."""
    if not HAS_PDF2IMAGE or not HAS_TESSERACT or not HAS_PANDAS:
        return {'error': 'Dépendances manquantes pour PDF->Excel'}
    
    try:
        # Sauvegarder le PDF temporairement
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, secure_filename(file_storage.filename))
        file_storage.save(pdf_path)
        
        # Convertir PDF en images
        images = convert_from_path(pdf_path)
        
        # Extraire le texte de chaque image avec OCR
        all_text = []
        for img in images:
            text = pytesseract.image_to_string(img, lang='fra+eng')
            all_text.append(text)
        
        # Créer un DataFrame
        df = pd.DataFrame({'Page': range(1, len(all_text) + 1),
                          'Contenu': all_text})
        
        # Sauvegarder en Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='PDF_Extrait')
        
        output.seek(0)
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{Path(file_storage.filename).stem}.xlsx"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->Excel: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_ppt(file, form_data=None):
    """Convertit PDF en PowerPoint."""
    if not HAS_PDF2IMAGE or not HAS_PILLOW or not HAS_PPTX:
        return {'error': 'Dépendances manquantes pour PDF->PowerPoint'}
    
    try:
        # Créer un dossier temporaire
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Convertir PDF en images
        images = convert_from_path(input_path)
        
        # Créer une présentation PowerPoint
        prs = Presentation()
        
        for i, image in enumerate(images):
            # Ajouter une diapositive
            slide_layout = prs.slide_layouts[6]  # Layout vierge
            slide = prs.slides.add_slide(slide_layout)
            
            # Sauvegarder l'image temporairement
            img_path = os.path.join(temp_dir, f"slide_{i}.png")
            image.save(img_path, 'PNG')
            
            # Ajouter l'image à la diapositive
            left = top = Inches(0.5)
            slide.shapes.add_picture(img_path, left, top, 
                                    height=prs.slide_height - Inches(1))
        
        # Sauvegarder la présentation
        output = BytesIO()
        prs.save(output)
        output.seek(0)
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pptx"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->PPT: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_images(file, form_data=None):
    """Convertit PDF en images."""
    if not HAS_PDF2IMAGE:
        return {'error': 'pdf2image non installé'}
    
    try:
        # Sauvegarder le PDF temporairement
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(pdf_path)
        
        # Convertir en images
        images = convert_from_path(pdf_path)
        
        # Créer un fichier ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, img in enumerate(images):
                img_buffer = BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                zip_file.writestr(f"page_{i+1}.png", img_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_images.zip"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->Images: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_pdfa(file, form_data=None):
    """Convertit PDF en PDF/A."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        pdf_writer = pypdf.PdfWriter()
        
        # Copier toutes les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Ajouter des métadonnées PDF/A (simplifié)
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': Path(file.filename).stem,
            '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
        })
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_pdfa.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->PDF/A: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_html(file, form_data=None):
    """Convertit PDF en HTML."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        # Créer le HTML
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF vers HTML</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .page { margin-bottom: 30px; page-break-after: always; }
        .page-number { color: #666; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
"""
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            html_content += f'<div class="page">\n'
            html_content += f'<h2>Page {page_num}</h2>\n'
            html_content += f'<div class="content">\n'
            
            text = page.extract_text()
            if text:
                # Échapper le texte pour HTML
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_content += f'<p>{text.replace(chr(10), "<br>")}</p>\n'
            
            html_content += f'</div>\n'
            html_content += f'<div class="page-number">Page {page_num}</div>\n'
            html_content += f'</div>\n'
        
        html_content += "</body>\n</html>"
        
        # Créer le fichier ZIP
        output = BytesIO()
        output.write(html_content.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/html',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.html"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->HTML: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_txt(file, form_data=None):
    """Convertit PDF en TXT."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        # Extraire le texte
        text_content = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text_content += f"\n--- Page {page_num} ---\n\n"
            text_content += page.extract_text() or "[Aucun texte extrait]"
            text_content += "\n\n"
        
        # Créer le fichier texte
        output = BytesIO()
        output.write(text_content.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.txt"
        )
        
    except Exception as e:
        logger.error(f"Erreur PDF->TXT: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_html_to_pdf(file, form_data=None):
    """Convertit HTML en PDF."""
    if not HAS_PDFKIT and not HAS_WEASYPRINT:
        return {'error': 'Aucune librairie HTML->PDF disponible'}
    
    try:
        # Lire le contenu HTML
        html_content = file.read().decode('utf-8')
        
        # Utiliser pdfkit (wkhtmltopdf) si disponible
        if HAS_PDFKIT:
            try:
                pdf = pdfkit.from_string(html_content, False)
                output = BytesIO(pdf)
            except Exception as e:
                logger.warning(f"pdfkit échoué, tentative avec weasyprint: {e}")
                if HAS_WEASYPRINT:
                    html_obj = weasyprint.HTML(string=html_content)
                    pdf = html_obj.write_pdf()
                    output = BytesIO(pdf)
                else:
                    raise
        else:
            html_obj = weasyprint.HTML(string=html_content)
            pdf = html_obj.write_pdf()
            output = BytesIO(pdf)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur HTML->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_txt_to_pdf(file, form_data=None):
    """Convertit TXT en PDF."""
    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}
    
    try:
        # Lire le contenu texte
        text_content = file.read().decode('utf-8')
        
        # Créer le PDF
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        # Paramètres
        margin = 50
        y = height - margin
        line_height = 14
        
        # Écrire le texte
        for line in text_content.split('\n'):
            if y < margin:
                c.showPage()
                y = height - margin
            
            c.setFont("Helvetica", 10)
            c.drawString(margin, y, line[:80])  # Limiter à 80 caractères
            y -= line_height
        
        c.save()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur TXT->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def unlock_pdf(file, form_data=None):
    """Déverrouille un PDF."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Lire le PDF avec mot de passe si fourni
        pdf_reader = pypdf.PdfReader(file.stream)
        password = form_data.get('password', '') if form_data else ''
        
        if pdf_reader.is_encrypted:
            if password:
                try:
                    pdf_reader.decrypt(password)
                except:
                    return {'error': 'Mot de passe incorrect'}
            else:
                return {'error': 'Ce PDF est protégé par mot de passe'}
        
        # Créer un nouveau PDF sans protection
        pdf_writer = pypdf.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_deverrouille.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur déverrouillage PDF: {str(e)}")
        return {'error': f'Erreur lors du déverrouillage: {str(e)}'}


def protect_pdf(file, form_data=None):
    """Protège un PDF avec un mot de passe."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Récupérer les mots de passe
        user_password = form_data.get('user_password', '') if form_data else ''
        owner_password = form_data.get('owner_password', user_password) if form_data else ''
        
        if not user_password:
            return {'error': 'Mot de passe requis'}
        
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        # Créer un nouveau PDF avec protection
        pdf_writer = pypdf.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Ajouter la protection
        pdf_writer.encrypt(user_password, owner_password)
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_protege.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur protection PDF: {str(e)}")
        return {'error': f'Erreur lors de la protection: {str(e)}'}


def convert_image_to_word(file, form_data=None):
    """Convertit une image en Word avec OCR."""
    if not HAS_PILLOW or not HAS_TESSERACT or not HAS_DOCX:
        return {'error': 'Dépendances manquantes pour Image->Word'}
    
    try:
        # Ouvrir l'image
        img = Image.open(file.stream)
        
        # OCR
        text = pytesseract.image_to_string(img, lang='fra+eng')
        
        # Créer un document Word
        doc = Document()
        doc.add_heading('Texte extrait de l\'image', 0)
        doc.add_paragraph(text)
        
        # Sauvegarder
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.docx"
        )
        
    except Exception as e:
        logger.error(f"Erreur Image->Word: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_image_to_excel(file_storage, form_data=None):
    """Convertit une image en Excel avec OCR."""
    if not HAS_PILLOW or not HAS_TESSERACT or not HAS_PANDAS:
        return {'error': 'Dépendances manquantes pour Image->Excel'}
    
    try:
        # Ouvrir l'image
        img = Image.open(file_storage.stream)
        
        # OCR pour obtenir des lignes de texte
        data = pytesseract.image_to_data(img, lang='fra+eng', output_type=Output.DICT)
        
        # Organiser les données
        rows = []
        current_row = []
        last_top = 0
        
        for i, text in enumerate(data['text']):
            if text.strip():
                top = data['top'][i]
                if abs(top - last_top) > 20:  # Nouvelle ligne
                    if current_row:
                        rows.append(current_row)
                        current_row = []
                    last_top = top
                current_row.append(text.strip())
        
        if current_row:
            rows.append(current_row)
        
        # Créer un DataFrame
        df = pd.DataFrame(rows)
        
        # Sauvegarder en Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Image_OCR')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{Path(file_storage.filename).stem}.xlsx"
        )
        
    except Exception as e:
        logger.error(f"Erreur Image->Excel: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_csv_to_excel(files, form_data=None):
    """Convertit CSV en Excel."""
    if not HAS_PANDAS:
        return {'error': 'pandas non installé'}
    
    try:
        # Si plusieurs fichiers, créer un classeur avec plusieurs feuilles
        if len(files) > 1:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for file in files:
                    # Lire le CSV
                    df = pd.read_csv(file.stream)
                    # Écrire dans une feuille
                    sheet_name = Path(file.filename).stem[:31]  # Max 31 caractères
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name="csv_converted.xlsx"
            )
        else:
            # Un seul fichier
            file = files[0]
            df = pd.read_csv(file.stream)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='CSV_Data')
            
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f"{Path(file.filename).stem}.xlsx"
            )
        
    except Exception as e:
        logger.error(f"Erreur CSV->Excel: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_excel_to_csv(files, form_data=None):
    """Convertit Excel en CSV."""
    if not HAS_PANDAS:
        return {'error': 'pandas non installé'}
    
    try:
        if len(files) > 1:
            # Plusieurs fichiers -> ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    # Lire l'Excel
                    df = pd.read_excel(file.stream)
                    # Convertir en CSV
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, index=False, encoding='utf-8')
                    csv_buffer.seek(0)
                    zip_file.writestr(f"{Path(file.filename).stem}.csv", csv_buffer.getvalue())
            
            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name="excel_converted.zip"
            )
        else:
            # Un seul fichier
            file = files[0]
            df = pd.read_excel(file.stream)
            
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"{Path(file.filename).stem}.csv"
            )
        
    except Exception as e:
        logger.error(f"Erreur Excel->CSV: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


# ============================================================================
# ROUTES API ET UTILITAIRES
# ============================================================================

@conversion_bp.context_processor
def utility_processor():
    """Fonctions utilitaires disponibles dans les templates."""
    def conversion_id_for_url(conversion_config):
        for key, config in CONVERSION_MAP.items():
            if config == conversion_config:
                return key
        return None
    return {
        'conversion_id_for_url': conversion_id_for_url,
        'now': datetime.now,
        'deps': DEPS_STATUS
    }


@conversion_bp.route('/api/supported-formats')
def api_supported_formats():
    """API pour récupérer les formats supportés."""
    available_conversions = {}
    for key, config in CONVERSION_MAP.items():
        available, missing = check_dependencies(config.get('deps', []))
        if available:
            available_conversions[key] = config
    
    return jsonify({
        'status': 'success',
        'conversions': list(available_conversions.keys()),
        'details': available_conversions,
        'dependencies': DEPS_STATUS
    })


@conversion_bp.route('/api/health')
def api_health():
    """Vérifie l'état des dépendances."""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'dependencies': DEPS_STATUS
    })


@conversion_bp.route('/dependencies')
def dependencies_page():
    """Page d'information sur les dépendances."""
    dependencies = []
    required = {
        'pandas': 'Manipulation de données',
        'pypdf': 'Traitement PDF',
        'Pillow': 'Manipulation d\'images',
        'pytesseract': 'OCR (reconnaissance de texte)',
        'pdf2image': 'Conversion PDF vers images',
        'openpyxl': 'Manipulation Excel',
        'python-docx': 'Manipulation Word',
        'python-pptx': 'Manipulation PowerPoint',
        'reportlab': 'Génération PDF',
        'pdfkit': 'Conversion HTML->PDF',
        'weasyprint': 'Conversion HTML->PDF',
        'libreoffice': 'Conversion Office vers PDF (système)',
        'poppler': 'Conversion PDF vers images (système)'
    }
    
    for package, description in required.items():
        if package in ['libreoffice', 'poppler']:
            installed = check_system_command(package)
        elif package == 'openpyxl':
            try:
                import openpyxl
                installed = True
            except ImportError:
                installed = False
        else:
            installed = DEPS_STATUS.get(package, False)
        
        dependencies.append({
            'name': package,
            'description': description,
            'installed': installed
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
        result = subprocess.run(['which', command], capture_output=True, text=True)
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