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

from flask_babel import _, lazy_gettext as _l

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

    # ==================== NOUVEAUX OUTILS PDF ====================
    'redact-pdf': {
        'template': 'redact_pdf.html',
        'title': 'Caviarder PDF',
        'description': 'Supprimez définitivement et en toute sécurité le contenu sensible de votre PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'mask',
        'color': '#e67e22',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow']
    },
    
    'edit-pdf': {
        'template': 'edit_pdf.html',
        'title': 'Éditer PDF',
        'description': 'Modifiez ou ajoutez du texte, des images et des pages à votre PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'edit',
        'color': '#3498db',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow', 'reportlab']
    },
    
    'sign-pdf': {
        'template': 'sign_pdf.html',
        'title': 'Signer PDF',
        'description': 'Ajoutez votre signature électronique à votre PDF',
        'from_format': 'PDF',
        'to_format': 'PDF',
        'icon': 'pen',
        'color': '#27ae60',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow', 'reportlab']
    },
    
    'prepare-form': {
        'template': 'prepare_form.html',
        'title': 'Préparer formulaire PDF',
        'description': 'Transformez vos documents Word, Excel ou numérisés en formulaires PDF interactifs',
        'from_format': 'Document',
        'to_format': 'PDF Formulaire',
        'icon': 'file-signature',
        'color': '#9b59b6',
        'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow', 'reportlab', 'python-docx', 'pandas']
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
        # Outils PDF (mettre à jour cette section)
        for conv_key in ['proteger-pdf', 'deverrouiller-pdf', 'redact-pdf', 
                         'edit-pdf', 'sign-pdf', 'prepare-form']:
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

        # Nouveaux outils PDF
        'redact-pdf': redact_pdf if HAS_PYPDF else None,
        'edit-pdf': edit_pdf if HAS_PYPDF and HAS_REPORTLAB else None,
        'sign-pdf': sign_pdf if HAS_PYPDF and HAS_PILLOW else None,
        'prepare-form': prepare_form if HAS_PYPDF and HAS_REPORTLAB else None,
        
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
        
        # Récupérer les options du formulaire
        page_format = form_data.get('page_format', 'A4') if form_data else 'A4'
        orientation = form_data.get('orientation', 'portrait') if form_data else 'portrait'
        margins = form_data.get('margins', 'normal') if form_data else 'normal'
        quality = form_data.get('quality', 'standard') if form_data else 'standard'
        
        # Définir la taille de page
        if page_format == 'A4':
            pagesize = A4
        elif page_format == 'Letter':
            pagesize = letter
        else:
            pagesize = A4
        
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
        c = canvas.Canvas(output, pagesize=pagesize)
        width, height = pagesize
        
        # Ajuster les marges
        margin_size = 50  # Normal
        if margins == 'narrow':
            margin_size = 25
        elif margins == 'wide':
            margin_size = 100
        
        # Lire le contenu du fichier Word (simplifié)
        if file.filename.endswith('.docx') and HAS_DOCX:
            doc = Document(input_path)
            y = height - margin_size
            for para in doc.paragraphs:
                if y < margin_size:
                    c.showPage()
                    y = height - margin_size
                c.setFont("Helvetica", 11)
                c.drawString(margin_size, y, para.text[:80])
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
    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}
    
    try:
        # Sauvegarder le fichier temporairement
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Récupérer les options
        include_notes = form_data.get('include_notes', 'true') if form_data else 'true'
        include_comments = form_data.get('include_comments', 'false') if form_data else 'false'
        quality = form_data.get('quality', 'medium') if form_data else 'medium'
        merge = form_data.get('merge', 'false') if form_data else 'false'
        
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
        
        return {'error': 'Conversion PowerPoint->PDF non disponible sans LibreOffice'}
        
    except Exception as e:
        logger.error(f"Erreur PowerPoint->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_images_to_pdf(files, form_data=None):
    """Convertit des images en PDF."""
    if not HAS_PILLOW or not HAS_REPORTLAB:
        return {'error': 'Pillow ou reportlab non installé'}
    
    try:
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        # Récupérer les options
        orientation = form_data.get('orientation', 'auto') if form_data else 'auto'
        quality = form_data.get('quality', 'medium') if form_data else 'medium'
        page_size = form_data.get('pageSize', 'A4') if form_data else 'A4'
        merge_files = form_data.get('merge', 'true') if form_data else 'true'
        
        # Ajuster l'orientation si nécessaire
        if orientation == 'landscape':
            width, height = height, width
        
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
            img.save(temp_img.name, 'JPEG', quality=90 if quality == 'high' else 75)
            
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
        
        # Récupérer les options
        mode = form_data.get('mode', 'layout') if form_data else 'layout'
        language = form_data.get('language', 'fra') if form_data else 'fra'
        detect_tables = form_data.get('detect_tables', 'true') if form_data else 'true'
        preserve_formatting = form_data.get('preserve_formatting', 'true') if form_data else 'true'
        
        # Créer un document Word
        doc = Document()
        
        # Ajouter un titre
        doc.add_heading(f'Conversion de {Path(file.filename).stem}', 0)
        
        # Extraire le texte de chaque page
        for page_num, page in enumerate(pdf_reader.pages):
            if page_num > 0:
                doc.add_page_break()
            
            doc.add_heading(f'Page {page_num + 1}', 1)
            
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
        
        # Récupérer les options
        mode = form_data.get('mode', 'tables') if form_data else 'tables'
        language = form_data.get('language', 'fra') if form_data else 'fra'
        ocr_enabled = form_data.get('ocr_enabled', 'true') if form_data else 'true'
        preserve_formatting = form_data.get('preserve_formatting', 'true') if form_data else 'true'
        
        # Convertir PDF en images
        images = convert_from_path(pdf_path)
        
        # Langue pour l'OCR
        lang_map = {
            'fra': 'fra',
            'eng': 'eng',
            'deu': 'deu',
            'spa': 'spa',
            'ita': 'ita'
        }
        ocr_lang = lang_map.get(language, 'fra+eng')
        
        # Extraire le texte de chaque image avec OCR
        all_data = []
        for i, img in enumerate(images):
            if ocr_enabled == 'true':
                # OCR avec détection de tableaux
                data = pytesseract.image_to_data(img, lang=ocr_lang, output_type=Output.DICT)
                
                # Organiser les données en lignes
                rows = []
                current_row = []
                last_top = 0
                
                for j, text in enumerate(data['text']):
                    if text.strip():
                        top = data['top'][j]
                        if abs(top - last_top) > 20:  # Nouvelle ligne
                            if current_row:
                                rows.append(current_row)
                                current_row = []
                            last_top = top
                        current_row.append(text.strip())
                
                if current_row:
                    rows.append(current_row)
                
                # Ajouter au DataFrame
                if rows:
                    df_page = pd.DataFrame(rows)
                    df_page.insert(0, 'Page', i+1)
                    all_data.append(df_page)
            else:
                # Texte simple sans mise en page
                text = pytesseract.image_to_string(img, lang=ocr_lang)
                df_page = pd.DataFrame({'Page': [i+1], 'Contenu': [text]})
                all_data.append(df_page)
        
        # Combiner toutes les pages
        if all_data:
            df = pd.concat(all_data, ignore_index=True)
        else:
            df = pd.DataFrame({'Page': range(1, len(images)+1), 'Contenu': [''] * len(images)})
        
        # Sauvegarder en Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='PDF_Extraction')
            
            # Ajouter une feuille de résumé
            summary_df = pd.DataFrame({
                'Propriété': ['Fichier source', 'Pages totales', 'OCR activé', 'Langue', 'Date'],
                'Valeur': [
                    Path(file_storage.filename).name,
                    len(images),
                    'Oui' if ocr_enabled == 'true' else 'Non',
                    language.upper(),
                    datetime.now().strftime('%d/%m/%Y %H:%M')
                ]
            })
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
        
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
        
        # Récupérer les options
        layout = form_data.get('layout', 'single') if form_data else 'single'
        slide_size = form_data.get('slide_size', 'widescreen') if form_data else 'widescreen'
        include_images = form_data.get('include_images', 'true') if form_data else 'true'
        editable_text = form_data.get('editable_text', 'true') if form_data else 'true'
        
        # Convertir PDF en images
        images = convert_from_path(input_path)
        
        # Créer une présentation PowerPoint
        prs = Presentation()
        
        # Définir la taille des diapositives
        if slide_size == 'widescreen':
            prs.slide_width = 9144000  # 10 pouces en EMU
            prs.slide_height = 5143500  # 5.625 pouces
        elif slide_size == 'standard':
            prs.slide_width = 9144000
            prs.slide_height = 6858000
        elif slide_size == 'a4':
            prs.slide_width = 8268000
            prs.slide_height = 11693000
        elif slide_size == 'letter':
            prs.slide_width = 9144000
            prs.slide_height = 11811000
        
        # Ajouter une diapositive par image
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
            
            # Ajouter le numéro de page
            txBox = slide.shapes.add_textbox(Inches(0.5), prs.slide_height - Inches(1), Inches(1), Inches(0.5))
            tf = txBox.text_frame
            tf.text = f"Page {i+1}"
        
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
        
        # Récupérer les options
        image_format = form_data.get('format', 'png') if form_data else 'png'
        quality = form_data.get('quality', 'medium') if form_data else 'medium'
        dpi = int(form_data.get('dpi', '150')) if form_data else 150
        pages = form_data.get('pages', 'all') if form_data else 'all'
        merge_single = form_data.get('merge_single', 'true') if form_data else 'true'
        
        # Convertir en images avec la résolution spécifiée
        if pages == 'all':
            images = convert_from_path(pdf_path, dpi=dpi)
        else:
            # Parser la sélection de pages (ex: "1,3-5")
            # Version simplifiée - à améliorer selon les besoins
            images = convert_from_path(pdf_path, dpi=dpi, first_page=1, last_page=5)
        
        # Créer un fichier ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, img in enumerate(images):
                img_buffer = BytesIO()
                if image_format == 'png':
                    img.save(img_buffer, format='PNG', optimize=True)
                else:
                    # JPG avec qualité ajustée
                    quality_val = 95 if quality == 'high' else 75 if quality == 'medium' else 50
                    img.save(img_buffer, format='JPEG', quality=quality_val, optimize=True)
                
                img_buffer.seek(0)
                zip_file.writestr(f"page_{i+1}.{image_format}", img_buffer.getvalue())
        
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
        
        # Récupérer la version PDF/A
        version = form_data.get('version', '2b') if form_data else '2b'
        
        # Copier toutes les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Mapper les versions PDF/A
        version_map = {
            '1a': 'PDF/A-1a:2005',
            '1b': 'PDF/A-1b:2005',
            '2a': 'PDF/A-2a:2011',
            '2b': 'PDF/A-2b:2011',
            '2u': 'PDF/A-2u:2011',
            '3a': 'PDF/A-3a:2012',
            '3b': 'PDF/A-3b:2012',
            '3u': 'PDF/A-3u:2012'
        }
        
        pdfa_version = version_map.get(version, 'PDF/A-2b:2011')
        
        # Ajouter des métadonnées PDF/A
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': Path(file.filename).stem,
            '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S'),
            '/GTS_PDFA1Version': pdfa_version,
            '/PDFA_ID': f'PDF/A-{version}',
            '/ModDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
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
        
        # Récupérer les options
        output_format = form_data.get('outputFormat', 'single') if form_data else 'single'
        encoding = form_data.get('encoding', 'utf-8') if form_data else 'utf-8'
        include_styles = form_data.get('includeStyles', 'true') if form_data else 'true'
        preserve_images = form_data.get('preserveImages', 'true') if form_data else 'true'
        
        # Créer le HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="{encoding}">
    <title>PDF vers HTML - {Path(file.filename).stem}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .page {{ margin-bottom: 30px; page-break-after: always; }}
        .page-number {{ color: #666; font-size: 12px; margin-top: 10px; text-align: center; }}
        .content {{ line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Conversion de {Path(file.filename).name}</h1>
    <p><em>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</em></p>
    <hr>
"""
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            html_content += f'<div class="page">\n'
            html_content += f'<h2>Page {page_num}</h2>\n'
            html_content += f'<div class="content">\n'
            
            text = page.extract_text()
            if text:
                # Échapper le texte pour HTML
                text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                # Convertir les retours à la ligne en <br>
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        html_content += f'<p>{para.replace(chr(10), "<br>")}</p>\n'
            
            html_content += f'</div>\n'
            html_content += f'<div class="page-number">Page {page_num}</div>\n'
            html_content += f'</div>\n'
        
        html_content += "</body>\n</html>"
        
        # Créer le fichier HTML ou ZIP selon le format demandé
        if output_format == 'single' or output_format == 'multiple':
            output = BytesIO()
            output.write(html_content.encode(encoding))
            output.seek(0)
            
            mimetype = 'text/html'
            download_name = f"{Path(file.filename).stem}.html"
        else:
            # Créer un ZIP
            output = BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f"{Path(file.filename).stem}.html", html_content.encode(encoding))
            
            output.seek(0)
            mimetype = 'application/zip'
            download_name = f"{Path(file.filename).stem}_html.zip"
        
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
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
        
        # Récupérer les options
        encoding = form_data.get('encoding', 'utf-8') if form_data else 'utf-8'
        preserve_layout = form_data.get('preserveLayout', 'false') if form_data else 'false'
        add_page_markers = form_data.get('addPageMarkers', 'true') if form_data else 'true'
        extract_all_pages = form_data.get('extractAllPages', 'true') if form_data else 'true'
        
        # Extraire le texte
        text_content = ""
        
        if add_page_markers == 'true':
            text_content += f"=== EXTRACTION DU PDF : {Path(file.filename).name} ===\n"
            text_content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            text_content += "=" * 60 + "\n\n"
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            if add_page_markers == 'true':
                text_content += f"\n--- Page {page_num} ---\n\n"
            
            page_text = page.extract_text()
            if page_text:
                text_content += page_text
            else:
                text_content += "[Aucun texte trouvé sur cette page]"
            
            text_content += "\n\n"
        
        if add_page_markers == 'true':
            text_content += "=" * 60 + "\n"
            text_content += f"Fin du document - {page_num} pages\n"
        
        # Créer le fichier texte
        output = BytesIO()
        output.write(text_content.encode(encoding))
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
        
        # Récupérer les options
        page_size = form_data.get('pageSize', 'A4') if form_data else 'A4'
        orientation = form_data.get('orientation', 'portrait') if form_data else 'portrait'
        margin = int(form_data.get('margin', '20')) if form_data else 20
        include_images = form_data.get('includeImages', 'true') if form_data else 'true'
        enable_javascript = form_data.get('enableJavascript', 'false') if form_data else 'false'
        
        # Options pour pdfkit
        options = {
            'page-size': page_size,
            'orientation': orientation,
            'margin-top': f'{margin}mm',
            'margin-right': f'{margin}mm',
            'margin-bottom': f'{margin}mm',
            'margin-left': f'{margin}mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }
        
        if enable_javascript == 'true':
            options['enable-javascript'] = None
        
        if include_images == 'false':
            options['no-images'] = None
        
        # Utiliser pdfkit (wkhtmltopdf) si disponible
        if HAS_PDFKIT:
            try:
                pdf = pdfkit.from_string(html_content, False, options=options)
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
        
        # Récupérer les options
        page_size = form_data.get('pageSize', 'A4') if form_data else 'A4'
        font_family = form_data.get('fontFamily', 'Helvetica') if form_data else 'Helvetica'
        font_size = int(form_data.get('fontSize', '12')) if form_data else 12
        line_spacing = float(form_data.get('lineSpacing', '1.5')) if form_data else 1.5
        add_page_numbers = form_data.get('addPageNumbers', 'true') if form_data else 'true'
        
        # Définir la taille de page
        if page_size == 'A4':
            pagesize = A4
        elif page_size == 'letter':
            pagesize = letter
        else:
            pagesize = A4
        
        # Créer le PDF
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=pagesize)
        width, height = pagesize
        
        # Paramètres
        margin = 50
        y = height - margin
        line_height = font_size * line_spacing
        page_num = 1
        
        # Écrire le texte
        lines = text_content.split('\n')
        for line in lines:
            # Vérifier si besoin d'une nouvelle page
            if y < margin:
                if add_page_numbers == 'true':
                    c.setFont("Helvetica", 8)
                    c.drawString(width - 50, 30, f"Page {page_num}")
                c.showPage()
                y = height - margin
                page_num += 1
                c.setFont(font_family, font_size)
            
            c.setFont(font_family, font_size)
            # Gérer les lignes trop longues
            while len(line) > 80:
                c.drawString(margin, y, line[:80])
                line = line[80:]
                y -= line_height
                if y < margin:
                    if add_page_numbers == 'true':
                        c.setFont("Helvetica", 8)
                        c.drawString(width - 50, 30, f"Page {page_num}")
                    c.showPage()
                    y = height - margin
                    page_num += 1
                    c.setFont(font_family, font_size)
            
            c.drawString(margin, y, line)
            y -= line_height
        
        # Ajouter le numéro de la dernière page
        if add_page_numbers == 'true':
            c.setFont("Helvetica", 8)
            c.drawString(width - 50, 30, f"Page {page_num}")
        
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
        
        # Ajouter des métadonnées
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': f"{Path(file.filename).stem} (déverrouillé)",
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
        
        if len(user_password) < 6:
            return {'error': 'Le mot de passe doit contenir au moins 6 caractères'}
        
        # Récupérer les permissions
        permissions = form_data.get('permissions', 'view') if form_data else 'view'
        
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        # Créer un nouveau PDF avec protection
        pdf_writer = pypdf.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Ajouter des métadonnées
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': f"{Path(file.filename).stem} (protégé)",
            '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
        })
        
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
        
        # Récupérer les options
        language = form_data.get('language', 'fra') if form_data else 'fra'
        
        # Langue pour l'OCR
        lang_map = {
            'fra': 'fra',
            'eng': 'eng',
            'deu': 'deu',
            'spa': 'spa',
            'ita': 'ita'
        }
        ocr_lang = lang_map.get(language, 'fra+eng')
        
        # OCR
        text = pytesseract.image_to_string(img, lang=ocr_lang)
        
        # Créer un document Word
        doc = Document()
        doc.add_heading('Texte extrait de l\'image', 0)
        doc.add_paragraph(text)
        
        # Ajouter l'image originale
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        doc.add_picture(img_buffer, width=Inches(6))
        
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
        
        # Récupérer les options
        language = form_data.get('language', 'fra') if form_data else 'fra'
        detect_tables = form_data.get('detect_tables', 'true') if form_data else 'true'
        
        # Langue pour l'OCR
        lang_map = {
            'fra': 'fra',
            'eng': 'eng',
            'deu': 'deu',
            'spa': 'spa',
            'ita': 'ita'
        }
        ocr_lang = lang_map.get(language, 'fra+eng')
        
        if detect_tables == 'true':
            # OCR avec détection de tableaux
            data = pytesseract.image_to_data(img, lang=ocr_lang, output_type=Output.DICT)
            
            # Organiser les données en lignes
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
        else:
            # Texte simple
            text = pytesseract.image_to_string(img, lang=ocr_lang)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            df = pd.DataFrame({'Texte extrait': lines})
        
        # Sauvegarder en Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Image_OCR')
            
            # Ajouter l'image (comme commentaire)
            summary_df = pd.DataFrame({
                'Information': ['Fichier source', 'Langue OCR', 'Détection tableaux', 'Date'],
                'Valeur': [
                    Path(file_storage.filename).name,
                    language.upper(),
                    'Oui' if detect_tables == 'true' else 'Non',
                    datetime.now().strftime('%d/%m/%Y %H:%M')
                ]
            })
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
        
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
        # Récupérer les options
        delimiter = form_data.get('delimiter', 'auto') if form_data else 'auto'
        encoding = form_data.get('encoding', 'utf-8') if form_data else 'utf-8'
        has_header = form_data.get('has_header', 'true') if form_data else 'true'
        
        # Si plusieurs fichiers, créer un classeur avec plusieurs feuilles
        if len(files) > 1:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for file in files:
                    # Déterminer le délimiteur
                    sep = ','
                    if delimiter == 'auto':
                        # Détection basique
                        sample = file.read(1024).decode(encoding)
                        file.seek(0)
                        if ';' in sample:
                            sep = ';'
                        elif '\t' in sample:
                            sep = '\t'
                    
                    # Lire le CSV
                    header = 0 if has_header == 'true' else None
                    df = pd.read_csv(file.stream, sep=sep, encoding=encoding, header=header)
                    
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
            
            # Déterminer le délimiteur
            sep = ','
            if delimiter == 'auto':
                sample = file.read(1024).decode(encoding)
                file.seek(0)
                if ';' in sample:
                    sep = ';'
                elif '\t' in sample:
                    sep = '\t'
            
            header = 0 if has_header == 'true' else None
            df = pd.read_csv(file.stream, sep=sep, encoding=encoding, header=header)
            
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
        # Récupérer les options
        delimiter = form_data.get('delimiter', ',') if form_data else ','
        encoding = form_data.get('encoding', 'utf-8') if form_data else 'utf-8'
        sheet_name = form_data.get('sheet_name', '0') if form_data else '0'
        include_header = form_data.get('include_header', 'true') if form_data else 'true'
        
        if len(files) > 1:
            # Plusieurs fichiers -> ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    # Lire l'Excel
                    if sheet_name == '0':
                        df = pd.read_excel(file.stream, sheet_name=0)
                    else:
                        try:
                            df = pd.read_excel(file.stream, sheet_name=sheet_name)
                        except:
                            df = pd.read_excel(file.stream, sheet_name=0)
                    
                    # Convertir en CSV
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, sep=delimiter, index=False, 
                            encoding=encoding, header=include_header == 'true')
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
            
            # Lire l'Excel
            if sheet_name == '0':
                df = pd.read_excel(file.stream, sheet_name=0)
            else:
                try:
                    df = pd.read_excel(file.stream, sheet_name=sheet_name)
                except:
                    df = pd.read_excel(file.stream, sheet_name=0)
            
            output = BytesIO()
            df.to_csv(output, sep=delimiter, index=False, 
                     encoding=encoding, header=include_header == 'true')
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

def redact_pdf(file, form_data=None):
    """
    Caviarde (supprime définitivement) le contenu sensible d'un PDF.
    Version améliorée avec pdfplumber pour la détection précise du texte.
    """
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Créer un dossier temporaire
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Récupérer les options
        redact_type = form_data.get('redact_type', 'text') if form_data else 'text'
        search_texts = form_data.get('search_text', '').split(',') if form_data.get('search_text') else []
        search_texts = [t.strip() for t in search_texts if t.strip()]
        
        redact_color = form_data.get('redact_color', '#000000') if form_data else '#000000'
        pages_option = form_data.get('pages', 'all') if form_data else 'all'
        page_range = form_data.get('page_range', '') if form_data else ''
        
        # Convertir la couleur hex en RGB
        if redact_color.startswith('#'):
            redact_color = redact_color[1:]
            rgb = tuple(int(redact_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb = (0, 0, 0)  # Noir par défaut
        
        # Déterminer les pages à traiter
        pages_to_process = []
        try:
            if pages_option == 'all':
                # On déterminera le nombre de pages plus tard
                pages_to_process = None  # Toutes les pages
            elif pages_option == 'range' and page_range:
                for part in page_range.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages_to_process.extend(range(start-1, end))
                    else:
                        pages_to_process.append(int(part)-1)
            elif pages_option == 'first':
                pages_to_process = [0]
            elif pages_option == 'last':
                # Sera déterminé après ouverture du PDF
                pages_to_process = [-1]
        except:
            pages_to_process = None
        
        # Ouvrir le PDF avec pypdf pour la manipulation
        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PdfWriter()
        
        total_pages = len(pdf_reader.pages)
        
        # Si "last page" est sélectionné
        if pages_to_process == [-1]:
            pages_to_process = [total_pages - 1]
        elif pages_to_process is None:
            pages_to_process = range(total_pages)
        
        # Essayer d'utiliser pdfplumber pour une détection précise (si disponible)
        try:
            import pdfplumber
            HAS_PDFPLUMBER = True
        except ImportError:
            HAS_PDFPLUMBER = False
            logger.warning("pdfplumber non disponible, utilisation de la méthode basique")
        
        # Essayer d'utiliser pymupdf (alternative plus puissante)
        try:
            import fitz  # PyMuPDF
            HAS_FITZ = True
        except ImportError:
            HAS_FITZ = False
        
        # Choisir la meilleure méthode disponible
        if HAS_FITZ:
            # Méthode avec PyMuPDF (la plus fiable)
            return redact_pdf_with_fitz(input_path, file.filename, search_texts, rgb, pages_to_process, redact_type)
        
        elif HAS_PDFPLUMBER:
            # Méthode avec pdfplumber
            return redact_pdf_with_pdfplumber(input_path, file.filename, search_texts, rgb, pages_to_process, redact_type)
        
        else:
            # Méthode basique avec pypdf seulement
            logger.warning("Utilisation de la méthode basique de caviardage")
            return redact_pdf_basic(input_path, file.filename, search_texts, pages_to_process, redact_type)
        
    except Exception as e:
        logger.error(f"Erreur caviardage PDF: {str(e)}")
        return {'error': f'Erreur lors du caviardage: {str(e)}'}
    finally:
        # Nettoyer le dossier temporaire après un délai
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


def redact_pdf_with_fitz(input_path, filename, search_texts, rgb, pages_to_process, redact_type):
    """Caviardage avancé avec PyMuPDF (fitz) - La meilleure méthode"""
    try:
        import fitz
        from PIL import Image
        
        # Ouvrir le document
        doc = fitz.open(input_path)
        
        # Créer un document temporaire pour le résultat
        output = BytesIO()
        
        # Traiter chaque page
        for page_num in range(len(doc)):
            if pages_to_process is not None and page_num not in pages_to_process:
                continue
            
            page = doc[page_num]
            
            if redact_type == 'text' and search_texts:
                # Rechercher chaque texte à caviarder
                for search_text in search_texts:
                    if not search_text:
                        continue
                    
                    # Rechercher toutes les occurrences du texte
                    text_instances = page.search_for(search_text)
                    
                    # Ajouter des annotations de caviardage pour chaque occurrence
                    for inst in text_instances:
                        # Créer une zone de caviardage
                        redact_annot = page.add_redact_annot(inst)
                        
                        # Définir la couleur de remplissage (noir par défaut)
                        redact_annot.set_colors(fill=rgb)
                        redact_annot.update()
            
            elif redact_type == 'area':
                # Caviardage par zone (sera implémenté séparément)
                pass
            
            elif redact_type == 'pattern':
                # Caviardage par motif (emails, téléphones...)
                if search_texts:
                    for pattern in search_texts:
                        if pattern == 'email':
                            # Rechercher des emails avec regex
                            text = page.get_text()
                            import re
                            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                            for email in emails:
                                areas = page.search_for(email)
                                for area in areas:
                                    redact_annot = page.add_redact_annot(area)
                                    redact_annot.set_colors(fill=rgb)
                                    redact_annot.update()
                        
                        elif pattern == 'phone':
                            # Rechercher des numéros de téléphone
                            text = page.get_text()
                            import re
                            phones = re.findall(r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b', text)
                            for phone in phones:
                                areas = page.search_for(phone)
                                for area in areas:
                                    redact_annot = page.add_redact_annot(area)
                                    redact_annot.set_colors(fill=rgb)
                                    redact_annot.update()
                        
                        elif pattern == 'creditcard':
                            # Rechercher des numéros de carte bancaire
                            text = page.get_text()
                            import re
                            cards = re.findall(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b', text)
                            for card in cards:
                                areas = page.search_for(card)
                                for area in areas:
                                    redact_annot = page.add_redact_annot(area)
                                    redact_annot.set_colors(fill=rgb)
                                    redact_annot.update()
                        
                        elif pattern == 'ssn':
                            # Rechercher des numéros de sécurité sociale (format français)
                            text = page.get_text()
                            import re
                            ssn = re.findall(r'\b\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\b', text)
                            for num in ssn:
                                areas = page.search_for(num)
                                for area in areas:
                                    redact_annot = page.add_redact_annot(area)
                                    redact_annot.set_colors(fill=rgb)
                                    redact_annot.update()
        
        # Appliquer tous les caviardages
        for page_num in range(len(doc)):
            if pages_to_process is not None and page_num not in pages_to_process:
                continue
            doc[page_num].apply_redactions()
        
        # Sauvegarder le document modifié
        doc.save(output)
        doc.close()
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(filename).stem}_redacted.pdf"
        )
        
    except ImportError:
        return {'error': 'PyMuPDF (fitz) non disponible pour le caviardage avancé'}
    except Exception as e:
        logger.error(f"Erreur dans redact_pdf_with_fitz: {str(e)}")
        raise


def redact_pdf_with_pdfplumber(input_path, filename, search_texts, rgb, pages_to_process, redact_type):
    """Caviardage avec pdfplumber (bonne méthode)"""
    try:
        import pdfplumber
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import Color
        
        # Ouvrir le PDF avec pdfplumber pour extraire les positions
        pdf = pdfplumber.open(input_path)
        
        # Ouvrir avec pypdf pour la manipulation
        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PdfWriter()
        
        # Convertir RGB en couleur ReportLab
        r, g, b = [x/255 for x in rgb]
        
        for page_num, page in enumerate(pdf.pages):
            if pages_to_process is not None and page_num not in pages_to_process:
                # Ajouter la page sans modification
                pdf_writer.add_page(pdf_reader.pages[page_num])
                continue
            
            # Extraire les mots avec leurs positions
            words = page.extract_words()
            
            # Créer un overlay pour caviarder
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.width, page.height))
            can.setFillColorRGB(r, g, b)
            
            redaction_applied = False
            
            if redact_type == 'text' and search_texts:
                for search_text in search_texts:
                    if not search_text:
                        continue
                    
                    # Chercher le texte dans les mots
                    search_lower = search_text.lower()
                    
                    # Recherche par mots consécutifs
                    for i in range(len(words) - len(search_text.split()) + 1):
                        candidate = ' '.join(words[j]['text'] for j in range(i, i + len(search_text.split())))
                        if candidate.lower() == search_lower:
                            # Caviarder chaque mot
                            for j in range(i, i + len(search_text.split())):
                                word = words[j]
                                x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
                                # Ajouter un rectangle noir
                                can.rect(x0, page.height - y1, x1 - x0, y1 - y0, fill=1, stroke=0)
                                redaction_applied = True
            
            elif redact_type == 'pattern':
                import re
                text = page.extract_text()
                
                if 'email' in search_texts:
                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                    for email in emails:
                        # Rechercher les positions de chaque email
                        for word in words:
                            if email in word['text']:
                                x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
                                can.rect(x0, page.height - y1, x1 - x0, y1 - y0, fill=1, stroke=0)
                                redaction_applied = True
                
                if 'phone' in search_texts:
                    phones = re.findall(r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b', text)
                    for phone in phones:
                        for word in words:
                            if phone in word['text']:
                                x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
                                can.rect(x0, page.height - y1, x1 - x0, y1 - y0, fill=1, stroke=0)
                                redaction_applied = True
            
            can.save()
            
            if redaction_applied:
                # Fusionner l'overlay avec la page originale
                packet.seek(0)
                overlay_pdf = pypdf.PdfReader(packet)
                
                original_page = pdf_reader.pages[page_num]
                original_page.merge_page(overlay_pdf.pages[0])
                pdf_writer.add_page(original_page)
            else:
                pdf_writer.add_page(pdf_reader.pages[page_num])
        
        pdf.close()
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(filename).stem}_redacted.pdf"
        )
        
    except ImportError:
        return {'error': 'pdfplumber non disponible pour le caviardage'}
    except Exception as e:
        logger.error(f"Erreur dans redact_pdf_with_pdfplumber: {str(e)}")
        raise


def redact_pdf_basic(input_path, filename, search_texts, pages_to_process, redact_type):
    """Méthode basique de caviardage avec pypdf uniquement"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PdfWriter()
        
        for page_num, page in enumerate(pdf_reader.pages):
            if pages_to_process is not None and page_num not in pages_to_process:
                pdf_writer.add_page(page)
                continue
            
            if redact_type == 'text' and search_texts:
                # Extraire le texte pour avoir une idée des positions approximatives
                text = page.extract_text()
                
                # Créer un overlay avec des rectangles noirs
                # Note: Cette méthode est approximative car on n'a pas les positions exactes
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                
                # Ajouter des rectangles aux positions approximatives
                # (C'est une simplification - dans la réalité, on aurait besoin des coordonnées)
                y_position = 700
                for line in text.split('\n'):
                    for search_text in search_texts:
                        if search_text and search_text in line:
                            # Ajouter un rectangle noir approximatif
                            can.setFillColorRGB(0, 0, 0)
                            can.rect(50, y_position - 15, 500, 20, fill=1, stroke=0)
                    y_position -= 20
                
                can.save()
                packet.seek(0)
                overlay_pdf = pypdf.PdfReader(packet)
                page.merge_page(overlay_pdf.pages[0])
            
            pdf_writer.add_page(page)
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(filename).stem}_redacted.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur dans redact_pdf_basic: {str(e)}")
        raise


def redact_area_in_page(page, x, y, width, height, color):
    """
    Caviarde une zone rectangulaire spécifique dans une page.
    Version améliorée avec PyMuPDF.
    """
    try:
        # Convertir la page pypdf en objet PyMuPDF si disponible
        import fitz
        
        # Créer un document temporaire avec la page
        doc = fitz.open()
        page_rect = fitz.Rect(x, y, x + width, y + height)
        
        # Ajouter une annotation de caviardage
        annot = page.add_redact_annot(page_rect)
        
        # Définir la couleur
        if isinstance(color, str) and color.startswith('#'):
            color = color[1:]
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            rgb = [c/255 for c in rgb]
        else:
            rgb = (0, 0, 0)
        
        annot.set_colors(fill=rgb)
        annot.update()
        
        # Appliquer le caviardage
        page.apply_redactions()
        
        return page
        
    except ImportError:
        # Fallback avec pypdf et reportlab
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.colors import Color
            
            # Créer un overlay avec un rectangle
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
            
            if isinstance(color, str) and color.startswith('#'):
                color = color[1:]
                r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                can.setFillColorRGB(r/255, g/255, b/255)
            else:
                can.setFillColorRGB(0, 0, 0)
            
            can.rect(x, page.mediabox.height - y - height, width, height, fill=1, stroke=0)
            can.save()
            
            packet.seek(0)
            overlay_pdf = pypdf.PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])
            
            return page
            
        except Exception as e:
            logger.error(f"Erreur dans redact_area_in_page: {str(e)}")
            return page
    except Exception as e:
        logger.error(f"Erreur dans redact_area_in_page: {str(e)}")
        return page


def redact_pattern_in_page(page, patterns, color):
    """
    Caviarde les motifs (emails, téléphones, etc.) dans une page.
    """
    try:
        import fitz
        import re
        
        text = page.get_text()
        
        # Définir les patterns regex
        pattern_dict = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b',
            'creditcard': r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
            'ssn': r'\b\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\b',
            'name': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Noms propres simples
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        }
        
        # Convertir la couleur
        if isinstance(color, str) and color.startswith('#'):
            color = color[1:]
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            rgb = [c/255 for c in rgb]
        else:
            rgb = (0, 0, 0)
        
        # Rechercher et caviarder chaque pattern
        for pattern_name in patterns:
            if pattern_name in pattern_dict:
                regex = pattern_dict[pattern_name]
                matches = re.findall(regex, text)
                
                for match in matches:
                    # Rechercher la position du texte dans la page
                    areas = page.search_for(match)
                    for area in areas:
                        annot = page.add_redact_annot(area)
                        annot.set_colors(fill=rgb)
                        annot.update()
        
        # Appliquer les caviardages
        page.apply_redactions()
        
        return page
        
    except ImportError:
        logger.warning("PyMuPDF non disponible pour le caviardage par motif")
        return page
    except Exception as e:
        logger.error(f"Erreur dans redact_pattern_in_page: {str(e)}")
        return page


def edit_pdf(file, form_data=None):
    """
    Édite un PDF : ajoute/modifie du texte, des images, réorganise les pages.
    """
    if not HAS_PYPDF or not HAS_REPORTLAB:
        return {'error': 'pypdf ou reportlab non installé'}
    
    try:
        # Créer un dossier temporaire
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PyPdfWriter()
        
        # Récupérer les options d'édition
        edit_type = form_data.get('edit_type', 'add_text') if form_data else 'add_text'
        page_number = int(form_data.get('page_number', '1')) - 1 if form_data else 0
        position_x = float(form_data.get('position_x', '50')) if form_data else 50
        position_y = float(form_data.get('position_y', '50')) if form_data else 50
        text_content = form_data.get('text_content', '') if form_data else ''
        font_size = int(form_data.get('font_size', '12')) if form_data else 12
        font_color = form_data.get('font_color', '#000000') if form_data else '#000000'
        
        # Créer un nouveau PDF avec les modifications
        if edit_type == 'add_text' and text_content:
            # Créer une superposition avec le texte
            overlay_pdf = create_text_overlay(text_content, position_x, position_y, 
                                            font_size, font_color)
            
            # Fusionner avec la page existante
            for i, page in enumerate(pdf_reader.pages):
                if i == page_number:
                    # Fusionner la page avec l'overlay
                    page.merge_page(overlay_pdf.pages[0])
                pdf_writer.add_page(page)
        
        elif edit_type == 'add_image':
            # Ajouter une image
            if 'image_file' in request.files:
                image_file = request.files['image_file']
                overlay_pdf = create_image_overlay(image_file, position_x, position_y)
                
                for i, page in enumerate(pdf_reader.pages):
                    if i == page_number:
                        page.merge_page(overlay_pdf.pages[0])
                    pdf_writer.add_page(page)
        
        elif edit_type == 'reorder':
            # Réorganiser les pages
            page_order = form_data.get('page_order', '') if form_data else ''
            if page_order:
                order = [int(p.strip())-1 for p in page_order.split(',') if p.strip()]
                for page_num in order:
                    if 0 <= page_num < len(pdf_reader.pages):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
            else:
                # Ajouter toutes les pages dans l'ordre
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
        
        elif edit_type == 'delete':
            # Supprimer des pages
            pages_to_delete = form_data.get('pages_to_delete', '') if form_data else ''
            if pages_to_delete:
                delete_set = set()
                for part in pages_to_delete.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        delete_set.update(range(start-1, end))
                    else:
                        delete_set.add(int(part)-1)
                
                for i, page in enumerate(pdf_reader.pages):
                    if i not in delete_set:
                        pdf_writer.add_page(page)
            else:
                # Ajouter toutes les pages
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
        
        else:
            # Aucune modification, copier toutes les pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
        
        # Ajouter des métadonnées
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': f"{Path(file.filename).stem} (édité)",
            '/ModDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
        })
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_edited.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur édition PDF: {str(e)}")
        return {'error': f'Erreur lors de l\'édition: {str(e)}'}


def create_text_overlay(text, x, y, font_size=12, color='#000000'):
    """Crée un PDF overlay avec du texte."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor
    
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", font_size)
    can.setFillColor(HexColor(color))
    can.drawString(x, letter[1] - y, text)  # Inverser y car PDF origin from bottom
    can.save()
    
    packet.seek(0)
    overlay_pdf = pypdf.PdfReader(packet)
    return overlay_pdf


def create_image_overlay(image_file, x, y):
    """Crée un PDF overlay avec une image."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    
    # Sauvegarder l'image temporairement
    temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    image_file.save(temp_img.name)
    
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Ajouter l'image
    img = ImageReader(temp_img.name)
    img_width, img_height = img.getSize()
    can.drawImage(img, x, letter[1] - y - img_height, width=img_width, height=img_height)
    can.save()
    
    packet.seek(0)
    overlay_pdf = pypdf.PdfReader(packet)
    
    # Nettoyer
    os.unlink(temp_img.name)
    
    return overlay_pdf


def sign_pdf(file, form_data=None):
    """
    Ajoute une signature électronique à un PDF.
    """
    if not HAS_PYPDF or not HAS_PILLOW:
        return {'error': 'pypdf ou Pillow non installé'}
    
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        pdf_writer = pypdf.PyPdfWriter()
        
        # Récupérer les options
        signature_type = form_data.get('signature_type', 'draw') if form_data else 'draw'
        page_number = int(form_data.get('page_number', '1')) - 1 if form_data else 0
        position_x = float(form_data.get('position_x', '50')) if form_data else 50
        position_y = float(form_data.get('position_y', '50')) if form_data else 50
        signature_text = form_data.get('signature_text', '') if form_data else ''
        
        # Créer l'overlay de signature
        overlay_pdf = None
        
        if signature_type == 'draw' and 'signature_image' in request.files:
            # Signature dessinée (image)
            sig_file = request.files['signature_image']
            overlay_pdf = create_signature_overlay(sig_file, position_x, position_y)
        
        elif signature_type == 'type' and signature_text:
            # Signature tapée
            font_size = int(form_data.get('font_size', '24')) if form_data else 24
            font_family = form_data.get('font_family', 'Courier') if form_data else 'Courier'
            overlay_pdf = create_text_signature(signature_text, position_x, position_y, 
                                               font_size, font_family)
        
        elif signature_type == 'certificate':
            # Signature numérique avec certificat
            # À implémenter avec des bibliothèques comme pyHanko ou endesive
            overlay_pdf = None
            return {'error': 'Signature numérique avec certificat non encore implémentée'}
        
        # Appliquer la signature
        for i, page in enumerate(pdf_reader.pages):
            if i == page_number and overlay_pdf:
                page.merge_page(overlay_pdf.pages[0])
            pdf_writer.add_page(page)
        
        # Ajouter des métadonnées de signature
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': f"{Path(file.filename).stem} (signé)",
            '/ModDate': datetime.now().strftime('D:%Y%m%d%H%M%S'),
            '/Signed': 'true'
        })
        
        # Sauvegarder
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_signed.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur signature PDF: {str(e)}")
        return {'error': f'Erreur lors de la signature: {str(e)}'}


def create_signature_overlay(signature_file, x, y):
    """Crée un overlay avec une signature image."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    
    # Sauvegarder l'image temporairement
    temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    signature_file.save(temp_img.name)
    
    # Redimensionner si nécessaire
    img = Image.open(temp_img.name)
    max_width = 200
    max_height = 100
    
    if img.width > max_width or img.height > max_height:
        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(temp_img.name, 'PNG')
    
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Ajouter l'image
    img_reader = ImageReader(temp_img.name)
    img_width, img_height = img_reader.getSize()
    can.drawImage(img_reader, x, letter[1] - y - img_height, 
                  width=img_width, height=img_height)
    can.save()
    
    packet.seek(0)
    overlay_pdf = pypdf.PdfReader(packet)
    
    # Nettoyer
    os.unlink(temp_img.name)
    
    return overlay_pdf


def create_text_signature(text, x, y, font_size=24, font_family='Courier'):
    """Crée un overlay avec une signature textuelle."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont(font_family, font_size)
    
    # Ajouter un style de signature manuscrite
    if font_family == 'Courier':
        # Style manuscrit approximatif
        can.setFont('Helvetica-Oblique', font_size)
        can.setFillColorRGB(0, 0, 0.8)  # Bleu
    
    can.drawString(x, letter[1] - y, text)
    
    # Ajouter une ligne sous la signature
    can.line(x, letter[1] - y - 5, x + len(text) * font_size * 0.6, letter[1] - y - 5)
    
    can.save()
    
    packet.seek(0)
    overlay_pdf = pypdf.PdfReader(packet)
    return overlay_pdf


def prepare_form(file, form_data=None):
    """
    Prépare un formulaire PDF à partir de divers documents.
    Transforme Word, Excel ou des images scannées en formulaires PDF interactifs.
    """
    if not HAS_PYPDF or not HAS_REPORTLAB:
        return {'error': 'pypdf ou reportlab non installé'}
    
    try:
        # Déterminer le type de fichier source
        filename = file.filename.lower()
        file_ext = Path(filename).suffix
        
        # Créer un dossier temporaire
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Convertir le fichier source en PDF si nécessaire
        pdf_path = input_path
        
        if file_ext in ['.doc', '.docx']:
            # Word vers PDF avec LibreOffice
            try:
                pdf_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
                subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, input_path
                ], check=True, capture_output=True)
            except:
                return {'error': 'Conversion Word->PDF impossible sans LibreOffice'}
        
        elif file_ext in ['.xls', '.xlsx']:
            # Excel vers PDF
            try:
                pdf_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
                subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, input_path
                ], check=True, capture_output=True)
            except:
                return {'error': 'Conversion Excel->PDF impossible sans LibreOffice'}
        
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            # Image vers PDF
            if HAS_PILLOW and HAS_REPORTLAB:
                pdf_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
                img = Image.open(input_path)
                
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                
                # Redimensionner l'image
                img_width, img_height = img.size
                ratio = min(width / img_width, height / img_height)
                new_width = img_width * ratio * 0.9
                new_height = img_height * ratio * 0.9
                
                # Centrer
                x = (width - new_width) / 2
                y = (height - new_height) / 2
                
                # Sauvegarder temporairement
                temp_img = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                img.save(temp_img.name, 'JPEG')
                
                c.drawImage(temp_img.name, x, y, width=new_width, height=new_height)
                c.save()
                
                os.unlink(temp_img.name)
            else:
                return {'error': 'Pillow ou reportlab non installé pour la conversion image->PDF'}
        
        # Maintenant, créer le formulaire PDF interactif
        form_pdf_reader = pypdf.PdfReader(pdf_path)
        form_pdf_writer = pypdf.PdfWriter()
        
        # Récupérer les options du formulaire
        form_type = form_data.get('form_type', 'interactive') if form_data else 'interactive'
        detect_fields = form_data.get('detect_fields', 'auto') if form_data else 'auto'
        
        # Détecter automatiquement les champs de formulaire potentiels
        form_fields = []
        
        if detect_fields == 'auto' or detect_fields == 'text':
            # Analyser le texte pour trouver des candidats de champs
            # (mots-clés comme "Nom:", "Prénom:", "Date:", etc.)
            keywords = ['nom', 'prénom', 'date', 'adresse', 'email', 'téléphone', 
                       'ville', 'code postal', 'signature', 'commentaire']
            
            for page_num, page in enumerate(form_pdf_reader.pages):
                text = page.extract_text()
                lines = text.split('\n')
                
                y_position = 800  # Position approximative
                for line in lines:
                    line_lower = line.lower().strip()
                    for keyword in keywords:
                        if keyword in line_lower:
                            form_fields.append({
                                'page': page_num,
                                'label': line.strip(),
                                'type': 'text' if keyword != 'signature' else 'signature',
                                'y': y_position,
                                'x': 50
                            })
                    y_position -= 20
        
        # Copier toutes les pages
        for page in form_pdf_reader.pages:
            form_pdf_writer.add_page(page)
        
        # Ajouter les champs de formulaire
        if form_type == 'interactive':
            # Créer des champs de formulaire AcroForm
            from pypdf.generic import NameObject, create_string_object, DictionaryObject, ArrayObject
            
            # Créer le dictionnaire AcroForm
            acroform = DictionaryObject()
            fields = ArrayObject()
            
            for i, field in enumerate(form_fields):
                # Créer un champ de texte
                field_dict = DictionaryObject({
                    NameObject("/FT"): NameObject("/Tx"),  # Field type: Text
                    NameObject("/T"): create_string_object(f"Field_{i}"),
                    NameObject("/TU"): create_string_object(field['label']),
                    NameObject("/Rect"): ArrayObject([
                        pypdf.generic.NumberObject(field['x']),
                        pypdf.generic.NumberObject(field['y'] - 15),
                        pypdf.generic.NumberObject(field['x'] + 200),
                        pypdf.generic.NumberObject(field['y'])
                    ]),
                    NameObject("/Ff"): pypdf.generic.NumberObject(2),  # Multiline
                    NameObject("/P"): form_pdf_writer.pages[field['page']].indirect_reference
                })
                
                fields.append(field_dict)
            
            if fields:
                acroform[NameObject("/Fields")] = fields
                form_pdf_writer._root_object[NameObject("/AcroForm")] = acroform
        
        elif form_type == 'printable':
            # Formulaire imprimable (lignes pour écrire)
            # À implémenter avec reportlab overlay
            pass
        
        # Ajouter des métadonnées
        form_pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': f"{Path(file.filename).stem} (formulaire préparé)",
            '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
        })
        
        # Sauvegarder
        output = BytesIO()
        form_pdf_writer.write(output)
        output.seek(0)
        
        # Nettoyer
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_form.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erreur préparation formulaire: {str(e)}")
        return {'error': f'Erreur lors de la préparation du formulaire: {str(e)}'}

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
