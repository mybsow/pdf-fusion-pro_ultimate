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
import subprocess
import logging
import importlib

from flask_babel import _, lazy_gettext as _l

# =========================
# LOGGING
# =========================
logger = logging.getLogger(__name__)

# =========================
# AJOUT RACINE PROJET AU PATH
# =========================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =========================
# CONFIGURATION
# =========================
try:
    from config import AppConfig
except ImportError:
    class AppConfig:
        OCR_ENABLED = True
        NAME = "PDF Fusion Pro"
        VERSION = "1.0.0"
        DEVELOPER_NAME = "Votre Nom"
        DEVELOPER_EMAIL = "contact@example.com"
        HOSTING = "Render"
        DOMAIN = "pdffusionpro.com"

# =========================
# IMPORT DEPENDANCES
# =========================
# Pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False
    logger.warning("[WARN] pandas non installé, conversions CSV/Excel désactivées")

# Pillow
try:
    from PIL import Image, ImageEnhance
    HAS_PILLOW = True
except ImportError:
    Image = ImageEnhance = None
    HAS_PILLOW = False
    logger.warning("[WARN] PIL/Pillow non installé, conversions images désactivées")

# Reportlab
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.utils import ImageReader
    HAS_REPORTLAB = True
except ImportError:
    canvas = letter = A4 = ImageReader = None
    HAS_REPORTLAB = False
    logger.warning("[WARN] reportlab non installé, génération PDF désactivée")

# python-docx
try:
    from docx import Document
    from docx.shared import Inches as DocxInches
    HAS_DOCX = True
except ImportError:
    Document = DocxInches = None
    HAS_DOCX = False
    logger.warning("[WARN] python-docx non installé, conversions Word désactivées")

# pypdf
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    pypdf = None
    HAS_PYPDF = False
    logger.warning("[WARN] pypdf non installé, manipulations PDF désactivées")

# numpy
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False
    logger.warning("[WARN] numpy non installé, certains traitements désactivés")

# pytesseract
try:
    import pytesseract
    from pytesseract import Output
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    HAS_TESSERACT = True
except ImportError:
    pytesseract = Output = None
    HAS_TESSERACT = False
    logger.warning("[WARN] pytesseract non installé, OCR désactivé")

# pdf2image
try:
    from pdf2image import convert_from_bytes, convert_from_path
    from pdf2image.pdf2image import pdfinfo_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    convert_from_bytes = convert_from_path = pdfinfo_from_path = None
    HAS_PDF2IMAGE = False
    logger.warning("[WARN] pdf2image non installé, conversion PDF impossible")

# pdfkit
try:
    import pdfkit
    HAS_PDFKIT = True
except ImportError:
    pdfkit = None
    HAS_PDFKIT = False
    logger.warning("[WARN] pdfkit non installé, conversions HTML->PDF désactivées")

# weasyprint
try:
    import weasyprint
    HAS_WEASYPRINT = True
except ImportError:
    weasyprint = None
    HAS_WEASYPRINT = False
    logger.warning("[WARN] weasyprint non installé, conversions HTML->PDF désactivées")

# python-pptx
try:
    from pptx import Presentation
    from pptx.util import Inches as PptxInches
    HAS_PPTX = True
except ImportError:
    Presentation = PptxInches = None
    HAS_PPTX = False
    logger.warning("[WARN] python-pptx non installé, conversions PowerPoint désactivées")

# LibreOffice
import subprocess

# =========================
# DEPENDENCY STATUS
# =========================
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
    'python-pptx': HAS_PPTX
}

# =========================
# BLUEPRINT
# =========================
conversion_bp = Blueprint(
    'conversion', __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'conversion'),
    static_folder='static/conversion',
    url_prefix='/conversion'
)

# =========================
# CHECK DEPENDENCIES
# =========================
DEP_FLAGS = {
    'reportlab': HAS_REPORTLAB,
    'Pillow': HAS_PILLOW,
    'pypdf': HAS_PYPDF,
    'python-docx': HAS_DOCX,
    'pytesseract': HAS_TESSERACT,
    'pdf2image': HAS_PDF2IMAGE,
    'pandas': HAS_PANDAS,
    'python-pptx': HAS_PPTX,
    'pdfkit': HAS_PDFKIT,
    'weasyprint': HAS_WEASYPRINT,
    'openpyxl': lambda: importlib.util.find_spec('openpyxl') is not None,
    'libreoffice': lambda: shutil.which('libreoffice') is not None
}

def check_dependencies(deps_list):
    missing = []
    for dep in deps_list or []:
        flag = DEP_FLAGS.get(dep)
        if callable(flag):
            if not flag():
                missing.append(dep)
        elif not flag:
            missing.append(dep)
    return len(missing) == 0, missing

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

# =========================
# ROUTES
# =========================

@conversion_bp.route('/')
def index():
    """Page d'accueil des conversions."""
    try:
        from collections import OrderedDict
        categories = OrderedDict({
            'convert_to_pdf': {'title': 'Convertir en PDF', 'icon': 'file-pdf', 'color': '#e74c3c', 'conversions': []},
            'convert_from_pdf': {'title': 'Convertir depuis PDF', 'icon': 'file-pdf', 'color': '#3498db', 'conversions': []},
            'pdf_tools': {'title': 'Outils PDF', 'icon': 'tools', 'color': '#2ecc71', 'conversions': []},
            'other_conversions': {'title': 'Autres conversions', 'icon': 'exchange-alt', 'color': '#9b59b6', 'conversions': []}
        })

        for cat, keys in {
            'convert_to_pdf': ['word-en-pdf','excel-en-pdf','powerpoint-en-pdf','image-en-pdf','jpg-en-pdf','png-en-pdf','html-en-pdf','txt-en-pdf'],
            'convert_from_pdf': ['pdf-en-word','pdf-en-doc','pdf-en-excel','pdf-en-ppt','pdf-en-image','pdf-en-pdfa','pdf-en-html','pdf-en-txt'],
            'pdf_tools': ['proteger-pdf','deverrouiller-pdf','redact-pdf','edit-pdf','sign-pdf','prepare-form'],
            'other_conversions': ['image-en-word','image-en-excel','csv-en-excel','excel-en-csv']
        }.items():
            for conv_key in keys:
                conv = CONVERSION_MAP.get(conv_key, {}).copy()
                if conv:
                    conv['type'] = conv_key
                    available, missing = check_dependencies(conv.get('deps', []))
                    conv['available'] = available
                    conv['missing_deps'] = missing
                    categories[cat]['conversions'].append(conv)

        return render_template('conversion/index.html', title="Convertisseur de fichiers universel",
                               categories=categories, all_conversions=CONVERSION_MAP, deps=DEPS_STATUS)
    except Exception as e:
        current_app.logger.error(f"❌ Erreur index(): {str(e)}\n{traceback.format_exc()}")
        flash("Service de conversion temporairement indisponible", "error")
        return render_template('conversion/index.html', title="Convertisseur", categories={}, all_conversions={}, deps=DEPS_STATUS, error=str(e))

# =========================
# UTILITAIRES
# =========================

def generate_fallback_pdf(filename, file_type):
    """PDF minimal si conversion échoue."""
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height-50, f"Conversion de fichier {file_type}")
    c.setFont("Helvetica", 14)
    c.drawString(50, height-100, f"Fichier: {filename}")
    c.drawString(50, height-130, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(50, height-180, "La conversion automatique n'a pas pu être effectuée.")
    c.drawString(50, height-210, "Veuillez réessayer avec un fichier différent.")
    c.save()
    output.seek(0)
    logger.warning(f"⚠️ PDF fallback généré pour {filename}")
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=f"{Path(filename).stem}_fallback.pdf")


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
        template_name = config['template']  # Juste le nom du fichier, sans dossier
        
        try:
            return render_template(template_name,
                                  title=config['title'],  # OK, pas de _() ici
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
            flash('Template non trouvé pour {}'.format(conversion_type), 'error')
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


# =========================
# PROCESS CONVERSION
# =========================

def handle_conversion_request(conversion_type, request, config):
    """Gère la requête POST/GET pour une conversion universelle."""
    try:
        # Vérifier si des fichiers sont présents
        if 'file' not in request.files and 'files' not in request.files:
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)

        # Plusieurs fichiers autorisés
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
    """Exécute la conversion appropriée selon le type."""
    # Dictionnaire des fonctions de conversion
    conversion_functions = {
        # === CONVERSIONS EN PDF ===
        'word-en-pdf': globals().get('convert_word_to_pdf') if HAS_REPORTLAB else None,
        'excel-en-pdf': globals().get('convert_excel_to_pdf') if HAS_REPORTLAB else None,
        'powerpoint-en-pdf': globals().get('convert_powerpoint_to_pdf') if HAS_REPORTLAB else None,
        'image-en-pdf': globals().get('convert_images_to_pdf') if HAS_PILLOW and HAS_REPORTLAB else None,
        'jpg-en-pdf': globals().get('convert_images_to_pdf') if HAS_PILLOW and HAS_REPORTLAB else None,
        'png-en-pdf': globals().get('convert_images_to_pdf') if HAS_PILLOW and HAS_REPORTLAB else None,
        'html-en-pdf': globals().get('convert_html_to_pdf') if HAS_PDFKIT or HAS_WEASYPRINT else None,
        'txt-en-pdf': globals().get('convert_txt_to_pdf') if HAS_REPORTLAB else None,

        # === CONVERSIONS DEPUIS PDF ===
        'pdf-en-word': globals().get('convert_pdf_to_word') if HAS_PYPDF and HAS_DOCX else None,
        'pdf-en-doc': globals().get('convert_pdf_to_doc') if HAS_PYPDF and HAS_DOCX else None,
        'pdf-en-excel': globals().get('convert_pdf_to_excel') if HAS_PDF2IMAGE and HAS_TESSERACT and HAS_PANDAS else None,
        'pdf-en-ppt': globals().get('convert_pdf_to_ppt') if HAS_PDF2IMAGE and HAS_PILLOW and HAS_PPTX else None,
        'pdf-en-image': globals().get('convert_pdf_to_images') if HAS_PDF2IMAGE else None,
        'pdf-en-pdfa': globals().get('convert_pdf_to_pdfa') if HAS_PYPDF else None,
        'pdf-en-html': globals().get('convert_pdf_to_html') if HAS_PYPDF else None,
        'pdf-en-txt': globals().get('convert_pdf_to_txt') if HAS_PYPDF else None,

        # === OUTILS PDF ===
        'proteger-pdf': globals().get('protect_pdf') if HAS_PYPDF else None,
        'deverrouiller-pdf': globals().get('unlock_pdf') if HAS_PYPDF else None,
        'redact-pdf': globals().get('redact_pdf') if HAS_PYPDF else None,
        'edit-pdf': globals().get('edit_pdf') if HAS_PYPDF and HAS_REPORTLAB else None,
        'sign-pdf': globals().get('sign_pdf') if HAS_PYPDF and HAS_PILLOW else None,
        'prepare-form': globals().get('prepare_form') if HAS_PYPDF and HAS_REPORTLAB else None,

        # === AUTRES CONVERSIONS ===
        'image-en-word': globals().get('convert_image_to_word') if HAS_PILLOW and HAS_TESSERACT and HAS_DOCX else None,
        'image-en-excel': globals().get('convert_image_to_excel') if HAS_PILLOW and HAS_TESSERACT and HAS_PANDAS else None,
        'csv-en-excel': globals().get('convert_csv_to_excel') if HAS_PANDAS else None,
        'excel-en-csv': globals().get('convert_excel_to_csv') if HAS_PANDAS else None
    }

    # Vérification type de conversion
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
        current_app.logger.error(f"Exception dans {conversion_type}: {str(e)}\n{traceback.format_exc()}")
        try:
            # Fallback PDF si possible
            if hasattr(file, 'filename'):
                return generate_fallback_pdf(file.filename, conversion_type)
        except Exception as fallback_e:
            current_app.logger.error(f"Erreur fallback PDF: {str(fallback_e)}")
        return {'error': f'Erreur interne: {str(e)}'}

# ============================================================================
# FONCTIONS DE CONVERSION
# ============================================================================

def smart_ocr(img, min_confidence=40, max_words=10000):
    """
    Extrait les mots détectés via Tesseract OCR.
    
    - Filtre par niveau de confiance
    - Protège contre images invalides
    - Limite le nombre de mots (sécurité mémoire)
    - Nettoie les artefacts OCR
    """

    if not HAS_TESSERACT or pytesseract is None:
        return []

    if img is None:
        return []

    try:
        # Sécurité : conversion RGB si nécessaire
        try:
            if img.mode != "RGB":
                img = img.convert("RGB")
        except Exception:
            return []

        data = pytesseract.image_to_data(
            img,
            lang="fra+eng",
            output_type=Output.DICT,
            config="--oem 3 --psm 6"
        )

        words = []
        texts = data.get("text", [])
        confidences = data.get("conf", [])

        for text, conf in zip(texts, confidences):
            if len(words) >= max_words:
                break

            try:
                conf = float(conf)
            except (ValueError, TypeError):
                continue

            if conf < min_confidence:
                continue

            text = str(text).strip()

            # Nettoyage basique bruit OCR
            if not text:
                continue
            if len(text) == 1 and not text.isalnum():
                continue

            words.append(text)

        return words

    except RuntimeError as e:
        # Erreur Tesseract typique (timeout / crash)
        print(f"[OCR_RUNTIME_ERROR] {e}")
        return []

    except Exception as e:
        print(f"[OCR_UNKNOWN_ERROR] {e}")
        return []


def convert_word_to_pdf(file, form_data=None):
    """Convertit un fichier Word en PDF avec fallback robuste."""
    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}
    
    temp_dir = None
    try:
        # Créer un dossier temporaire
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        # Options page
        page_format = form_data.get('page_format', 'A4') if form_data else 'A4'
        orientation = form_data.get('orientation', 'portrait') if form_data else 'portrait'
        
        pagesize = A4 if page_format == 'A4' else letter
        if orientation == 'landscape':
            pagesize = (pagesize[1], pagesize[0])
        width, height = pagesize
        
        output_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
        
        # ===== Conversion LibreOffice si disponible =====
        try:
            libreoffice_path = shutil.which('libreoffice')
            if libreoffice_path:
                cmd = [
                    libreoffice_path, '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, input_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    with open(output_path, 'rb') as f:
                        if f.read(4) == b'%PDF':
                            return send_file(
                                output_path,
                                mimetype='application/pdf',
                                as_attachment=True,
                                download_name=f"{Path(file.filename).stem}.pdf"
                            )
                        else:
                            logger.warning("LibreOffice a généré un PDF invalide, fallback activé")
                else:
                    logger.warning(f"LibreOffice failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"LibreOffice conversion failed: {e}")
        
        # ===== Fallback: extraire texte avec python-docx =====
        text_content = ""
        if file.filename.endswith('.docx') and HAS_DOCX:
            try:
                doc = Document(input_path)
                paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
                text_content = "\n\n".join(paragraphs)
            except Exception as e:
                logger.warning(f"python-docx extraction failed: {e}")
                text_content = f"Document: {file.filename}\n\nContenu non extractible."
        else:
            text_content = f"Document: {file.filename}\n\nContenu non extractible."
        
        # ===== Créer PDF fallback =====
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=pagesize)
        
        # Titre
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Document: {file.filename}")
        
        # Texte
        y = height - 100
        c.setFont("Helvetica", 11)
        
        for para in text_content.split("\n"):
            lines = []
            # Split smart lignes trop longues sans couper mots
            while len(para) > 0:
                if len(para) <= 95:
                    lines.append(para)
                    break
                split_pos = para.rfind(" ", 0, 95)
                if split_pos == -1:
                    split_pos = 95
                lines.append(para[:split_pos])
                para = para[split_pos:].lstrip()
            
            for line in lines:
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - 50
                c.drawString(50, y, line)
                y -= 15
        
        c.save()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )
    
    except Exception as e:
        logger.error(f"Erreur Word->PDF: {e}")
        return {'error': f'Erreur lors de la conversion: {e}'}
    
    finally:
        # Nettoyage sûr
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Erreur nettoyage temp_dir: {e}")

def convert_excel_to_pdf(file, form_data=None):
    """Convertit un fichier Excel en PDF avec fallback robuste."""
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            return {'error': 'Fichier Excel vide ou non sauvegardé'}
        
        logger.info(f"📁 Fichier Excel sauvegardé: {input_path} ({os.path.getsize(input_path)} octets)")
        output_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
        
        # ===== MÉTHODE 1: LibreOffice =====
        try:
            libreoffice_path = shutil.which('libreoffice')
            if libreoffice_path:
                logger.info("🔄 Tentative de conversion avec LibreOffice...")
                cmd = [
                    libreoffice_path, '--headless', '--invisible', '--nologo', '--nodefault',
                    '--nofirststartwizard', '--convert-to', 'pdf', '--outdir', temp_dir, input_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    with open(output_path, 'rb') as f:
                        if f.read(4) == b'%PDF':
                            logger.info("✅ PDF valide généré avec LibreOffice")
                            return send_file(
                                output_path,
                                mimetype='application/pdf',
                                as_attachment=True,
                                download_name=f"{Path(file.filename).stem}.pdf"
                            )
                        else:
                            logger.warning("LibreOffice a généré un PDF invalide, fallback activé")
                else:
                    logger.warning(f"LibreOffice conversion failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"⚠️ LibreOffice échoué: {e}")
        
        # ===== MÉTHODE 2: Fallback avec pandas =====
        if HAS_PANDAS:
            try:
                import pandas as pd
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                
                logger.info("🔄 Tentative de conversion avec pandas (fallback)...")
                sheets = pd.read_excel(input_path, sheet_name=None)
                
                output = BytesIO()
                c = canvas.Canvas(output, pagesize=A4)
                width, height = A4
                
                y = height - 50
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, y, f"Export de: {file.filename}")
                y -= 30
                
                for sheet_name, df in sheets.items():
                    if y < 100:
                        c.showPage()
                        y = height - 50
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(50, y, f"Feuille: {sheet_name}")
                    y -= 20
                    
                    c.setFont("Helvetica", 10)
                    for i, row in df.head(20).iterrows():
                        if y < 50:
                            c.showPage()
                            y = height - 50
                        row_text = ' | '.join([str(val)[:20] for val in row.values])
                        row_text = row_text[:100]  # Limite à 100 caractères par ligne
                        c.drawString(60, y, row_text)
                        y -= 15
                    y -= 20
                
                c.save()
                output.seek(0)
                
                logger.info("✅ PDF généré avec pandas (fallback)")
                return send_file(
                    output,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}.pdf"
                )
            except Exception as e:
                logger.error(f"❌ Fallback pandas échoué: {e}")
        
        # ===== MÉTHODE 3: Fallback minimal =====
        return generate_fallback_pdf(file.filename, "Excel")
    
    except Exception as e:
        logger.error(f"❌ Erreur Excel->PDF: {e}")
        return {'error': f'Erreur lors de la conversion: {e}'}
    
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Erreur nettoyage temp_dir: {e}")


def convert_powerpoint_to_pdf(file, form_data=None):
    """Convertit un fichier PowerPoint en PDF avec fallback robuste."""
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)
        
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            return {'error': 'Fichier PowerPoint vide ou non sauvegardé'}
        
        logger.info(f"📁 Fichier PowerPoint sauvegardé: {input_path} ({os.path.getsize(input_path)} octets)")
        output_path = os.path.join(temp_dir, f"{Path(file.filename).stem}.pdf")
        
        # ===== MÉTHODE 1: LibreOffice =====
        try:
            libreoffice_path = shutil.which('libreoffice')
            if libreoffice_path:
                logger.info(f"🔄 Tentative de conversion avec LibreOffice: {libreoffice_path}")
                cmd = [
                    libreoffice_path, '--headless', '--invisible', '--nologo', '--nodefault',
                    '--nofirststartwizard', '--convert-to', 'pdf', '--outdir', temp_dir, input_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    with open(output_path, 'rb') as f:
                        if f.read(4) == b'%PDF':
                            logger.info("✅ PDF valide généré avec LibreOffice")
                            return send_file(
                                output_path,
                                mimetype='application/pdf',
                                as_attachment=True,
                                download_name=f"{Path(file.filename).stem}.pdf"
                            )
                        else:
                            logger.warning("LibreOffice a généré un PDF invalide, fallback activé")
                else:
                    logger.warning(f"LibreOffice conversion failed: {result.stderr}")
            else:
                logger.warning("⚠️ LibreOffice non trouvé dans le PATH")
        except subprocess.TimeoutExpired:
            logger.error("⏱️ Timeout LibreOffice")
        except Exception as e:
            logger.error(f"❌ Exception LibreOffice: {e}")
        
        # ===== MÉTHODE 2: Fallback python-pptx =====
        if HAS_PPTX:
            try:
                logger.info("🔄 Tentative de conversion avec python-pptx (fallback)")
                from pptx import Presentation
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from io import BytesIO
                
                prs = Presentation(input_path)
                output = BytesIO()
                c = canvas.Canvas(output, pagesize=A4)
                width, height = A4
                
                for i, slide in enumerate(prs.slides):
                    y_position = height - 50
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(50, y_position, f"Diapositive {i+1}")
                    y_position -= 30
                    
                    text_found = False
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text:
                            text_found = True
                            for line in shape.text.split('\n'):
                                if y_position < 50:
                                    c.showPage()
                                    y_position = height - 50
                                    c.setFont("Helvetica", 10)
                                
                                if len(line) > 80:
                                    line = line[:80] + "..."
                                c.drawString(50, y_position, line)
                                y_position -= 15
                    
                    if not text_found:
                        c.drawString(50, y_position, "[Aucun texte trouvé sur cette diapositive]")
                    
                    c.showPage()
                
                c.save()
                output.seek(0)
                
                logger.info("✅ PDF généré avec python-pptx (fallback)")
                return send_file(
                    output,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}.pdf"
                )
            except Exception as e:
                logger.error(f"❌ Fallback python-pptx échoué: {e}")
                logger.error(traceback.format_exc())
        
        # ===== MÉTHODE 3: Fallback minimal =====
        logger.warning("⚠️ Utilisation du fallback minimal")
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from io import BytesIO
        
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Conversion de: {file.filename}")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, "Le fichier PowerPoint n'a pas pu être converti correctement.")
        c.drawString(50, height - 120, "Veuillez réessayer ou utiliser un autre fichier.")
        c.drawString(50, height - 140, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        c.save()
        output.seek(0)
        
        logger.warning("⚠️ PDF minimal généré (fallback)")
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )
    
    except Exception as e:
        logger.error(f"❌ Erreur PowerPoint->PDF: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {e}'}
    
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"🧹 Nettoyage du dossier temporaire: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage: {e}")


def convert_images_to_pdf(files, form_data=None):
    """Convertit une liste d'images en un PDF unique."""
    if not HAS_PILLOW or not HAS_REPORTLAB:
        return {'error': 'Pillow ou reportlab non installé'}
    
    temp_files = []
    try:
        output = BytesIO()
        
        # Options de conversion
        page_size = form_data.get('pageSize', 'A4') if form_data else 'A4'
        orientation = form_data.get('orientation', 'portrait') if form_data else 'portrait'
        quality = form_data.get('quality', 'medium') if form_data else 'medium'
        
        # Définir la taille de page
        if page_size == 'A4':
            pagesize = A4
        elif page_size == 'Letter':
            pagesize = letter
        else:
            pagesize = A4
        
        # Ajuster l'orientation
        if orientation == 'landscape':
            pagesize = (pagesize[1], pagesize[0])
        
        c = canvas.Canvas(output, pagesize=pagesize)
        width, height = pagesize
        
        # Qualité JPEG
        quality_val = 95 if quality == 'high' else 75 if quality == 'medium' else 50
        
        for file in files:
            try:
                # Sauvegarder l'image temporairement
                temp_input = tempfile.NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=False)
                file.save(temp_input.name)
                temp_files.append(temp_input.name)
                
                # Ouvrir l'image
                img = Image.open(temp_input.name)
                
                # Conversion RGB si nécessaire
                if img.mode in ('RGBA', 'LA', 'P'):
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    mask = img.split()[-1] if img.mode in ('RGBA', 'LA') else None
                    bg.paste(img, mask=mask)
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculer le ratio pour tenir sur la page
                img_width, img_height = img.size
                ratio = min((width * 0.9) / img_width, (height * 0.9) / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                
                # Centrer l'image
                x = (width - new_width) / 2
                y = (height - new_height) / 2
                
                # Sauvegarder temporairement l'image redimensionnée
                temp_img = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_files.append(temp_img.name)
                if ratio < 1:
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img.save(temp_img.name, 'JPEG', quality=quality_val, optimize=True)
                
                # Ajouter l'image au PDF
                c.drawImage(temp_img.name, x, y, width=new_width, height=new_height)
                c.showPage()
                
            except Exception as e:
                logger.error(f"Erreur traitement image {getattr(file, 'filename', 'inconnu')}: {e}")
                continue
        
        c.save()
        output.seek(0)
        
        # Vérifier le PDF
        if output.getvalue()[:4] != b'%PDF':
            return {'error': 'PDF généré invalide'}
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name="images_converted.pdf"
        )
    
    except Exception as e:
        logger.error(f"Erreur Images->PDF: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}
    
    finally:
        # Nettoyage des fichiers temporaires
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"⚠️ Erreur suppression fichier temporaire {temp_file}: {e}")


def convert_pdf_to_word(file, form_data=None):
    """Convertit un PDF en document Word (.docx)"""
    if not HAS_PYPDF or not HAS_DOCX:
        return {'error': 'pypdf ou python-docx non installé'}
    
    try:
        # Vérifier que c'est un PDF
        if not file.filename.lower().endswith('.pdf'):
            return {'error': 'Le fichier fourni n’est pas un PDF'}
        
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        # Vérifier que le PDF contient des pages
        if len(pdf_reader.pages) == 0:
            return {'error': 'PDF vide ou invalide'}
        
        logger.info(f"📄 Conversion PDF->Word: {file.filename} ({len(pdf_reader.pages)} pages)")
        
        # Créer le document Word
        doc = Document()
        doc.add_heading(f'Extraction de: {Path(file.filename).stem}', 0)
        doc.add_paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        doc.add_paragraph(f"Nombre de pages: {len(pdf_reader.pages)}")
        doc.add_paragraph()
        
        # Extraire le texte page par page
        for page_num, page in enumerate(pdf_reader.pages):
            if page_num > 0:
                doc.add_page_break()
            
            doc.add_heading(f'Page {page_num + 1}', 1)
            
            try:
                text = page.extract_text()
                if text and text.strip():
                    doc.add_paragraph(text)
                else:
                    doc.add_paragraph("[Aucun texte trouvé sur cette page]")
            except Exception as e_page:
                logger.warning(f"⚠️ Impossible d’extraire texte page {page_num + 1}: {e_page}")
                doc.add_paragraph("[Erreur extraction texte]")
        
        # Sauvegarder dans un flux mémoire
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        logger.info(f"✅ Conversion terminée: {file.filename} -> {Path(file.filename).stem}.docx")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.docx"
        )
    
    except Exception as e:
        logger.error(f"❌ Erreur PDF->Word: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_doc(file, form_data=None):
    """Convertit un PDF en document Word au format .doc en utilisant la conversion PDF->.docx puis adaptation."""
    try:
        # Appel à la fonction principale PDF->DOCX
        response = convert_pdf_to_word(file, form_data)
        
        # Vérifier que c'est un BytesIO / send_file, sinon c'est une erreur
        if isinstance(response, dict) and 'error' in response:
            return response
        
        # Si nécessaire, on pourrait ajouter une conversion DOCX -> DOC ici
        # Mais la plupart des applications modernes lisent DOCX nativement.
        # On renvoie simplement le fichier avec extension .doc pour compatibilité.
        if hasattr(response, 'headers'):
            response.headers["Content-Disposition"] = response.headers["Content-Disposition"].replace(".docx", ".doc")
        return response
    
    except Exception as e:
        logger.error(f"❌ Erreur PDF->DOC: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_pdf_to_excel(file_storage, form_data=None):
    """Convertit un PDF en Excel avec OCR multilingue complet."""
    if not HAS_PDF2IMAGE or not HAS_TESSERACT or not HAS_PANDAS:
        return {'error': 'Dépendances manquantes pour PDF->Excel'}

    temp_dir = None
    try:
        # Sauvegarde temporaire du PDF
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, secure_filename(file_storage.filename))
        file_storage.save(pdf_path)

        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            return {'error': 'Fichier PDF vide ou non sauvegardé'}

        # Options du formulaire
        mode = form_data.get('mode', 'tables') if form_data else 'tables'
        language = form_data.get('language', 'fra') if form_data else 'fra'
        ocr_enabled = str(form_data.get('ocr_enabled', 'true')).lower() if form_data else 'true'

        # Gestion des langues multiples pour Tesseract
        selected_languages = language.split('+') if '+' in language else [language]
        lang_map = {
            'fra': 'fra', 'en': 'eng', 'es': 'spa', 'de': 'deu', 'it': 'ita',
            'pt': 'por', 'ru': 'rus', 'ar': 'ara', 'zh': 'chi_sim', 'ja': 'jpn', 'nl': 'nld'
        }
        ocr_langs = [lang_map.get(l, 'fra') for l in selected_languages]
        ocr_lang = '+'.join(ocr_langs)
        logger.info(f"🔤 Langues OCR: {ocr_lang}")

        # Conversion PDF -> images
        images = convert_from_path(pdf_path, dpi=200)
        if not images:
            return {'error': 'Aucune page trouvée dans le PDF'}
        logger.info(f"🖼️ {len(images)} pages converties en images")

        all_data = []
        pages_with_content = 0

        for i, img in enumerate(images):
            try:
                logger.info(f"📄 Traitement page {i+1}/{len(images)}")
                if ocr_enabled == 'true':
                    # OCR avec mise en page
                    data = pytesseract.image_to_data(
                        img,
                        lang=ocr_lang,
                        output_type=Output.DICT,
                        config='--oem 3 --psm 6'
                    )

                    rows = []
                    current_row = []
                    last_top = -1
                    row_threshold = 15
                    for j, text in enumerate(data['text']):
                        if text.strip() and int(data['conf'][j]) >= 30:
                            top = data['top'][j]
                            if last_top == -1 or abs(top - last_top) > row_threshold:
                                if current_row:
                                    rows.append(current_row)
                                current_row = []
                                last_top = top
                            current_row.append({'text': text.strip(), 'left': data['left'][j]})
                    if current_row:
                        rows.append(current_row)

                    # Convertir en DataFrame
                    text_rows = [' '.join([w['text'] for w in sorted(row, key=lambda x: x['left'])]) for row in rows]
                    if text_rows:
                        df_page = pd.DataFrame({'Page': i+1, 'Ligne': range(1, len(text_rows)+1), 'Contenu': text_rows})
                        all_data.append(df_page)
                        pages_with_content += 1
                else:
                    # OCR simple
                    text = pytesseract.image_to_string(img, lang=ocr_lang)
                    if text.strip():
                        lines = [line for line in text.split('\n') if line.strip()]
                        df_page = pd.DataFrame({'Page': i+1, 'Ligne': range(1, len(lines)+1), 'Contenu': lines})
                        all_data.append(df_page)
                        pages_with_content += 1
            except Exception as e:
                logger.error(f"❌ Erreur OCR page {i+1}: {e}")
                continue

        # Fusionner toutes les pages
        df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame({
            'Page': range(1, len(images)+1),
            'Ligne': [1]*len(images),
            'Contenu': ['[Aucun texte détecté]']*len(images)
        })

        # Sauvegarde Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='PDF_Extraction')
            worksheet = writer.sheets['PDF_Extraction']
            for column in worksheet.columns:
                max_len = max(len(str(cell.value)) if cell.value else 0 for cell in column)
                worksheet.column_dimensions[column[0].column_letter].width = min(max_len+2, 50)

            # Feuille résumé
            summary_df = pd.DataFrame({
                'Propriété': [
                    'Fichier source', 'Pages totales', 'Pages avec contenu',
                    'OCR activé', 'Langues sélectionnées', 'Langues OCR utilisées',
                    'Mode d\'extraction', 'Date de conversion', 'Taille du fichier source'
                ],
                'Valeur': [
                    Path(file_storage.filename).name, len(images), pages_with_content,
                    'Oui' if ocr_enabled == 'true' else 'Non',
                    ', '.join(selected_languages), ocr_lang, mode,
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    f"{os.path.getsize(pdf_path)/1024:.1f} KB"
                ]
            })
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
            summary_sheet = writer.sheets['Résumé']
            summary_sheet.column_dimensions['A'].width = 25
            summary_sheet.column_dimensions['B'].width = 40

        output.seek(0)
        logger.info(f"✅ Excel généré: {output.getbuffer().nbytes} octets")

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{Path(file_storage.filename).stem}.xlsx"
        )

    except Exception as e:
        logger.error(f"❌ Erreur PDF->Excel: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"🧹 Nettoyage du dossier temporaire: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage: {e}")


def convert_pdf_to_ppt(file, form_data=None):
    """Convertit un PDF en présentation PowerPoint."""
    if not HAS_PDF2IMAGE or not HAS_PILLOW or not HAS_PPTX:
        return {'error': 'Dépendances manquantes pour PDF->PowerPoint'}

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)

        slide_size = (9144000, 6858000)  # Par défaut 4:3
        if form_data:
            size_opt = form_data.get('slide_size', 'widescreen')
            if size_opt == 'widescreen':
                slide_size = (9144000, 5143500)  # 16:9
            elif size_opt == 'standard':
                slide_size = (9144000, 6858000)  # 4:3

        # Conversion PDF -> images
        try:
            images = convert_from_path(input_path, dpi=150)
        except Exception as e:
            logger.error(f"Erreur conversion PDF->images: {e}")
            return {'error': f'Impossible de convertir le PDF en images: {e}'}

        if not images:
            return {'error': 'Aucune page trouvée dans le PDF'}

        prs = Presentation()
        prs.slide_width, prs.slide_height = slide_size

        for i, img in enumerate(images):
            slide_layout = prs.slide_layouts[6]  # Diapositive vierge
            slide = prs.slides.add_slide(slide_layout)

            # Sauvegarde temporaire de l'image
            img_path = os.path.join(temp_dir, f"slide_{i}.png")
            img.save(img_path, 'PNG')

            # Calculer la taille et la position pour centrer l'image
            slide_w, slide_h = prs.slide_width, prs.slide_height
            img_w, img_h = img.size
            scale = min(slide_w / img_w, slide_h / img_h) * 0.95  # 5% de marge
            width = img_w * scale
            height = img_h * scale
            left = int((slide_w - width) / 2)
            top = int((slide_h - height) / 2)

            slide.shapes.add_picture(img_path, left, top, width=width, height=height)

            # Ajouter le numéro de page en bas à gauche
            txBox = slide.shapes.add_textbox(left=Inches(0.2), top=slide_h - Inches(0.4), width=Inches(2), height=Inches(0.3))
            tf = txBox.text_frame
            tf.text = f"Page {i+1}"

        # Sauvegarde de la présentation
        output = BytesIO()
        prs.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pptx"
        )

    except Exception as e:
        logger.error(f"Erreur PDF->PPT: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}

    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"🧹 Nettoyage du dossier temporaire: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage: {e}")


def convert_pdf_to_images(file, form_data=None):
    """Convertit un PDF en images et les renvoie dans un ZIP."""
    if not HAS_PDF2IMAGE:
        return {'error': 'pdf2image non installé'}

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(pdf_path)

        # Options utilisateur
        image_format = (form_data.get('format', 'png') if form_data else 'png').lower()
        quality_opt = form_data.get('quality', 'medium') if form_data else 'medium'
        dpi = int(form_data.get('dpi', '150')) if form_data else 150

        logger.info(f"🔄 Conversion PDF->Images: {pdf_path}, format={image_format}, dpi={dpi}, quality={quality_opt}")

        # Convertir PDF en images
        try:
            images = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            logger.error(f"❌ Erreur conversion PDF->images: {e}")
            return {'error': f'Impossible de convertir le PDF en images: {e}'}

        if not images:
            return {'error': 'Aucune page trouvée dans le PDF'}

        # Créer ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, img in enumerate(images):
                try:
                    img_buffer = BytesIO()

                    if image_format == 'png':
                        img.save(img_buffer, format='PNG', optimize=True)
                    else:  # JPG
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        quality_val = 95 if quality_opt == 'high' else 75 if quality_opt == 'medium' else 50
                        img.save(img_buffer, format='JPEG', quality=quality_val, optimize=True)

                    img_buffer.seek(0)
                    filename = f"page_{i+1}.{image_format}"
                    zip_file.writestr(filename, img_buffer.getvalue())
                    logger.info(f"✅ Page {i+1} ajoutée au ZIP: {filename}")

                except Exception as e:
                    logger.warning(f"⚠️ Erreur traitement page {i+1}: {e}")
                    continue

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_images.zip"
        )

    except Exception as e:
        logger.error(f"❌ Erreur PDF->Images: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {e}'}

    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"🧹 Nettoyage du dossier temporaire: {temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage: {e}")


def convert_pdf_to_pdfa(file, form_data=None):
    """Convertit un PDF en PDF/A."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}

    temp_dir = None
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        pdf_writer = pypdf.PdfWriter()

        if len(pdf_reader.pages) == 0:
            return {'error': 'PDF vide ou invalide'}

        # Récupérer la version PDF/A
        version = (form_data.get('version', '2b') if form_data else '2b').lower()
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
        logger.info(f"🔤 Conversion PDF->PDF/A version: {pdfa_version}")

        # Copier les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        # Ajouter métadonnées PDF/A
        creation_date = datetime.now().strftime('D:%Y%m%d%H%M%S')
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro',
            '/Creator': 'PDF Fusion Pro',
            '/Title': Path(file.filename).stem,
            '/CreationDate': creation_date,
            '/ModDate': creation_date,
            '/GTS_PDFA1Version': pdfa_version,
            '/PDFA_ID': f'PDF/A-{version}'
        })

        # Sauvegarder dans BytesIO
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)

        logger.info(f"✅ PDF/A généré avec succès: {Path(file.filename).name}")

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_pdfa.pdf"
        )

    except Exception as e:
        logger.error(f"❌ Erreur PDF->PDF/A: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {e}'}


def convert_pdf_to_html(file, form_data=None):
    """Convertit un PDF en HTML."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}

    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)

        if len(pdf_reader.pages) == 0:
            return {'error': 'PDF vide ou invalide'}

        # Options
        encoding = (form_data.get('encoding', 'utf-8') if form_data else 'utf-8')
        logger.info(f"🔤 Conversion PDF->HTML avec encodage: {encoding}")

        # Début HTML
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="{encoding}">
    <title>PDF vers HTML - {Path(file.filename).stem}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .page {{ margin-bottom: 40px; page-break-after: always; }}
        .page-number {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
        .content {{ max-width: 800px; margin: 0 auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        pre {{ white-space: pre-wrap; font-family: inherit; }}
    </style>
</head>
<body>
    <h1>Extraction de: {Path(file.filename).name}</h1>
    <p><em>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</em></p>
    <p><em>Pages: {len(pdf_reader.pages)}</em></p>
    <hr>
"""

        # Parcourir chaque page
        for page_num, page in enumerate(pdf_reader.pages, 1):
            html_content += f'<div class="page">\n<h2>Page {page_num}</h2>\n<div class="content">\n'

            text = page.extract_text()
            if text and text.strip():
                # Échapper caractères HTML
                text = (text.replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('"', '&quot;'))
                # Transformer en paragraphes
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        para_html = para.replace('\n', '<br>')
                        html_content += f'<p>{para_html}</p>\n'
            else:
                html_content += '<p><em>[Aucun texte trouvé sur cette page]</em></p>\n'

            html_content += f'</div>\n<div class="page-number">Page {page_num} / {len(pdf_reader.pages)}</div>\n</div>\n'

        html_content += "</body>\n</html>"

        # Sauvegarder dans BytesIO
        output = BytesIO()
        output.write(html_content.encode(encoding))
        output.seek(0)

        logger.info(f"✅ PDF converti en HTML: {Path(file.filename).name}")
        return send_file(
            output,
            mimetype='text/html',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.html"
        )

    except Exception as e:
        logger.error(f"❌ Erreur PDF->HTML: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {e}'}


def convert_pdf_to_txt(file, form_data=None):
    """Convertit un PDF en TXT."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}

    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        num_pages = len(pdf_reader.pages)

        if num_pages == 0:
            return {'error': 'PDF vide ou invalide'}

        # Options
        encoding = (form_data.get('encoding', 'utf-8') if form_data else 'utf-8')
        add_page_markers = (form_data.get('addPageMarkers', 'true') if form_data else 'true')
        logger.info(f"🔤 Conversion PDF->TXT avec encodage {encoding}, marqueurs de page: {add_page_markers}")

        # Début du texte
        text_content = ""
        if add_page_markers == 'true':
            text_content += "=" * 80 + "\n"
            text_content += f"EXTRACTION DU PDF : {Path(file.filename).name}\n"
            text_content += f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            text_content += f"Pages : {num_pages}\n"
            text_content += "=" * 80 + "\n\n"

        # Parcourir les pages
        for page_num, page in enumerate(pdf_reader.pages, 1):
            if add_page_markers == 'true':
                text_content += f"\n--- Page {page_num} ---\n\n"

            page_text = page.extract_text()
            if page_text and page_text.strip():
                text_content += page_text
            else:
                text_content += "[Aucun texte trouvé sur cette page]"

            text_content += "\n\n"

        if add_page_markers == 'true':
            text_content += "=" * 80 + "\n"
            text_content += f"Fin du document - {num_pages} pages\n"
            text_content += "=" * 80 + "\n"

        # Créer le fichier TXT
        output = BytesIO()
        output.write(text_content.encode(encoding))
        output.seek(0)

        logger.info(f"✅ PDF converti en TXT: {Path(file.filename).name}")
        return send_file(
            output,
            mimetype='text/plain',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.txt"
        )

    except Exception as e:
        logger.error(f"❌ Erreur PDF->TXT: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_html_to_pdf(file, form_data=None):
    """Convertit HTML en PDF avec fallback WeasyPrint/PDFKit."""
    if not HAS_WEASYPRINT and not HAS_PDFKIT:
        return {'error': 'Aucune librairie HTML->PDF disponible'}

    try:
        # Lire le contenu HTML
        html_content = file.read().decode('utf-8', errors='ignore')

        # Options
        page_size = form_data.get('pageSize', 'A4') if form_data else 'A4'
        orientation = form_data.get('orientation', 'portrait') if form_data else 'portrait'
        logger.info(f"🔤 Conversion HTML->PDF: page_size={page_size}, orientation={orientation}")

        output = None

        # ===== Méthode 1: WeasyPrint =====
        if HAS_WEASYPRINT:
            try:
                html_obj = weasyprint.HTML(string=html_content)
                pdf_bytes = html_obj.write_pdf(stylesheets=None)
                if pdf_bytes[:4] == b'%PDF':
                    output = BytesIO(pdf_bytes)
                    output.seek(0)
                    logger.info("✅ PDF généré avec WeasyPrint")
            except Exception as e:
                logger.warning(f"WeasyPrint échoué: {e}")

        # ===== Méthode 2: PDFKit =====
        if output is None and HAS_PDFKIT:
            try:
                options = {
                    'page-size': page_size,
                    'orientation': orientation,
                    'margin-top': '20mm',
                    'margin-right': '20mm',
                    'margin-bottom': '20mm',
                    'margin-left': '20mm',
                    'encoding': 'UTF-8',
                    'no-outline': None,
                    'enable-local-file-access': None
                }
                pdf_bytes = pdfkit.from_string(html_content, False, options=options)
                if pdf_bytes[:4] == b'%PDF':
                    output = BytesIO(pdf_bytes)
                    output.seek(0)
                    logger.info("✅ PDF généré avec PDFKit")
            except Exception as e:
                logger.warning(f"PDFKit échoué: {e}")

        # Vérifier que le PDF est généré
        if output is None:
            logger.error("❌ Impossible de générer un PDF valide depuis le HTML")
            return {'error': 'Impossible de générer un PDF valide'}

        # Envoyer le PDF
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )

    except Exception as e:
        logger.error(f"❌ Erreur HTML->PDF: {e}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_txt_to_pdf(file, form_data=None):
    """Convertit un fichier TXT en PDF."""
    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}

    try:
        # Lire le contenu TXT
        text_content = file.read().decode('utf-8', errors='ignore')

        # Options
        page_size = form_data.get('pageSize', 'A4') if form_data else 'A4'
        font_size = int(form_data.get('fontSize', '12')) if form_data else 12
        logger.info(f"🔤 Conversion TXT->PDF: page_size={page_size}, font_size={font_size}")

        # Taille de page
        pagesize = A4 if page_size == 'A4' else letter
        width, height = pagesize

        # Création du PDF
        output = BytesIO()
        c = canvas.Canvas(output, pagesize=pagesize)
        margin = 50
        y = height - margin
        line_height = font_size * 1.5
        c.setFont("Helvetica", font_size)

        # Écriture du texte
        for line in text_content.split('\n'):
            while len(line) > 80:
                c.drawString(margin, y, line[:80])
                line = line[80:]
                y -= line_height
                if y < margin:
                    c.showPage()
                    y = height - margin
                    c.setFont("Helvetica", font_size)

            c.drawString(margin, y, line)
            y -= line_height
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", font_size)

        c.save()
        output.seek(0)

        # Validation PDF
        if output.getvalue()[:4] != b'%PDF':
            logger.error("❌ PDF généré invalide")
            return {'error': 'PDF généré invalide'}

        logger.info(f"✅ PDF généré avec succès: {Path(file.filename).name}")
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )

    except Exception as e:
        logger.error(f"❌ Erreur TXT->PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def unlock_pdf(file, form_data=None):
    """Déverrouille un PDF."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        password = form_data.get('password', '') if form_data else ''
        
        # Vérifier si le PDF est protégé
        if pdf_reader.is_encrypted:
            if password:
                try:
                    success = pdf_reader.decrypt(password)
                    if not success:
                        logger.warning(f"Mot de passe incorrect pour {file.filename}")
                        return {'error': 'Mot de passe incorrect'}
                    logger.info(f"✅ PDF déchiffré avec succès: {file.filename}")
                except Exception as e:
                    logger.error(f"Erreur de déchiffrement: {e}")
                    return {'error': f'Erreur de déchiffrement: {e}'}
            else:
                return {'error': 'Ce PDF est protégé par mot de passe'}
        
        # Vérifier que le PDF est valide
        if len(pdf_reader.pages) == 0:
            return {'error': 'PDF vide ou invalide'}
        
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
        logger.error(f"❌ Erreur déverrouillage PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors du déverrouillage: {str(e)}'}


def protect_pdf(file, form_data=None):
    """Protège un PDF avec un mot de passe."""
    if not HAS_PYPDF:
        return {'error': 'pypdf non installé'}
    
    try:
        # Récupérer les mots de passe
        user_password = form_data.get('user_password', '') if form_data else ''
        owner_password = form_data.get('owner_password', user_password) if form_data else user_password
        
        # Vérifications
        if not user_password:
            return {'error': 'Mot de passe utilisateur requis'}
        if len(user_password) < 6:
            return {'error': 'Le mot de passe doit contenir au moins 6 caractères'}
        
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        
        if len(pdf_reader.pages) == 0:
            return {'error': 'PDF vide ou invalide'}
        
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
        
        # Appliquer la protection
        pdf_writer.encrypt(user_password, owner_password)
        logger.info(f"✅ PDF protégé avec succès: {file.filename}")
        
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
        logger.error(f"❌ Erreur protection PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la protection: {str(e)}'}


def convert_image_to_word(file, form_data=None):
    """Convertit une image en Word avec OCR - Support multilingue complet"""
    if not HAS_PILLOW or not HAS_TESSERACT or not HAS_DOCX:
        return {'error': 'Dépendances manquantes pour Image->Word'}
    
    temp_files = []
    try:
        # Sauvegarder l'image temporairement
        temp_input = tempfile.NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=False)
        file.save(temp_input.name)
        temp_files.append(temp_input.name)
        logger.info(f"📁 Image sauvegardée: {temp_input.name}")
        
        # Ouvrir l'image avec PIL
        try:
            img = Image.open(temp_input.name)
            logger.info(f"🖼️ Image ouverte: {img.format} {img.size} {img.mode}")
        except Exception as e:
            return {'error': f'Impossible d\'ouvrir l\'image: {str(e)}'}
        
        # Récupérer les options
        language = form_data.get('language', 'fra') if form_data else 'fra'
        enhance_image = form_data.get('enhance_image', 'true') if form_data else 'true'
        preserve_layout = form_data.get('preserve_layout', 'true') if form_data else 'true'
        
        # Support des langues multiples (format: "fra+eng+spa")
        selected_languages = language.split('+') if '+' in language else [language]
        
        # CARTE COMPLÈTE DES LANGUES OCR - 11 langues supportées
        lang_map = {
            # Code interface -> Code Tesseract
            'fra': 'fra',      # Français
            'en': 'eng',       # Anglais
            'es': 'spa',       # Espagnol
            'de': 'deu',       # Allemand
            'it': 'ita',       # Italien
            'pt': 'por',       # Portugais
            'ru': 'rus',       # Russe
            'ar': 'ara',       # Arabe
            'zh': 'chi_sim',   # Chinois simplifié
            'ja': 'jpn',       # Japonais
            'nl': 'nld'        # Néerlandais
        }
        
        # Construire la chaîne de langues pour Tesseract
        ocr_langs = []
        for lang_code in selected_languages:
            if lang_code in lang_map:
                ocr_langs.append(lang_map[lang_code])
                logger.info(f"✅ Langue OCR ajoutée: {lang_code} -> {lang_map[lang_code]}")
            else:
                # Fallback vers français si langue non reconnue
                logger.warning(f"⚠️ Langue non reconnue: {lang_code}, fallback vers français")
                ocr_langs.append('fra')
        
        # Si aucune langue valide, utiliser français par défaut
        ocr_lang = '+'.join(ocr_langs) if ocr_langs else 'fra'
        logger.info(f"🔤 Langues OCR sélectionnées: {ocr_lang}")
        
        # Prétraitement de l'image pour améliorer l'OCR
        if enhance_image == 'true':
            try:
                # Convertir en niveaux de gris
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Améliorer le contraste
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)
                
                # Binarisation adaptative
                import numpy as np
                img_array = np.array(img)
                from PIL import ImageOps
                img = ImageOps.autocontrast(img)
                
                # Sauvegarder l'image améliorée
                temp_enhanced = tempfile.NamedTemporaryFile(suffix='_enhanced.png', delete=False)
                img.save(temp_enhanced.name, 'PNG')
                temp_files.append(temp_enhanced.name)
                logger.info("✨ Image améliorée pour OCR")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'amélioration de l'image: {e}")
        
        # Configuration Tesseract selon le mode de préservation
        if preserve_layout == 'true':
            # PSM 6: Assume a single uniform block of text
            custom_config = r'--oem 3 --psm 6'
        else:
            # PSM 3: Automatic page segmentation, but no OSD
            custom_config = r'--oem 3 --psm 3'
        
        # Exécuter l'OCR avec les langues sélectionnées
        try:
            logger.info(f"🔍 Exécution de l'OCR avec langues: {ocr_lang}")
            
            if preserve_layout == 'true':
                # OCR avec préservation de la mise en page
                data = pytesseract.image_to_data(
                    img, 
                    lang=ocr_lang, 
                    output_type=Output.DICT,
                    config=custom_config
                )
                
                # Organiser les données par paragraphes
                paragraphs = []
                current_para = []
                last_block_num = -1
                
                for i, text in enumerate(data['text']):
                    if text and text.strip():
                        block_num = data['block_num'][i]
                        par_num = data['par_num'][i]
                        conf = int(data['conf'][i])
                        
                        # Ignorer les détections de faible confiance
                        if conf < 30:
                            continue
                        
                        # Nouveau paragraphe si changement de block
                        if block_num != last_block_num and last_block_num != -1:
                            if current_para:
                                paragraphs.append(' '.join(current_para))
                                current_para = []
                        
                        current_para.append(text.strip())
                        last_block_num = block_num
                
                # Ajouter le dernier paragraphe
                if current_para:
                    paragraphs.append(' '.join(current_para))
                
                text_content = '\n\n'.join(paragraphs)
                
            else:
                # OCR simple sans préservation de mise en page
                text_content = pytesseract.image_to_string(
                    img, 
                    lang=ocr_lang,
                    config=custom_config
                )
            
            logger.info(f"✅ OCR terminé: {len(text_content)} caractères extraits")
            
        except Exception as e:
            logger.error(f"❌ Erreur OCR: {e}")
            return {'error': f'Erreur lors de l\'OCR: {str(e)}'}
        
        # Créer un document Word
        doc = Document()
        
        # Ajouter un titre
        doc.add_heading(f'Texte extrait de l\'image: {Path(file.filename).name}', 0)
        
        # Ajouter les informations
        doc.add_paragraph(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        doc.add_paragraph(f"Langues OCR: {ocr_lang}")
        doc.add_paragraph(f"Taille de l'image: {img.size[0]} x {img.size[1]} pixels")
        doc.add_paragraph()
        
        # Ajouter le texte extrait
        if text_content and text_content.strip():
            doc.add_heading('Texte extrait', 1)
            
            # Diviser en paragraphes et ajouter au document
            for para in text_content.split('\n\n'):
                if para.strip():
                    doc.add_paragraph(para.strip())
        else:
            doc.add_paragraph("[Aucun texte détecté dans l'image]")
        
        # Ajouter l'image originale
        doc.add_page_break()
        doc.add_heading('Image originale', 1)
        
        # Redimensionner l'image pour le document Word
        img_buffer = BytesIO()
        
        # Ouvrir à nouveau l'image originale
        original_img = Image.open(temp_input.name)
        
        # Redimensionner si trop grande
        max_width = 500
        if original_img.width > max_width:
            ratio = max_width / original_img.width
            new_size = (max_width, int(original_img.height * ratio))
            original_img = original_img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Sauvegarder dans le buffer
        original_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Ajouter l'image au document
        doc.add_picture(img_buffer, width=Inches(6))
        
        # Ajouter une légende
        doc.add_paragraph(f"Image originale: {file.filename}", style='Caption')
        
        # Sauvegarder le document
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        
        logger.info(f"✅ Document Word généré: {output.getbuffer().nbytes} octets")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.docx"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur Image->Word: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}
    
    finally:
        # Nettoyer les fichiers temporaires
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"🧹 Nettoyage: {temp_file}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage {temp_file}: {e}")


def convert_image_to_excel(file_storage, form_data=None):
    """Convertit une image en Excel avec OCR - Support multilingue complet et détection avancée des tableaux"""
    if not HAS_PILLOW or not HAS_TESSERACT or not HAS_PANDAS:
        return {'error': 'Dépendances manquantes pour Image->Excel'}
    
    temp_files = []
    try:
        # Sauvegarder l'image temporairement
        temp_input = tempfile.NamedTemporaryFile(suffix=Path(file_storage.filename).suffix, delete=False)
        file_storage.save(temp_input.name)
        temp_files.append(temp_input.name)
        logger.info(f"📁 Image sauvegardée: {temp_input.name}")
        
        # Ouvrir l'image avec PIL
        try:
            img = Image.open(temp_input.name)
            logger.info(f"🖼️ Image ouverte: {img.format} {img.size} {img.mode}")
        except Exception as e:
            return {'error': f'Impossible d\'ouvrir l\'image: {str(e)}'}
        
        # Récupérer les options
        language = form_data.get('language', 'fra') if form_data else 'fra'
        detect_tables = form_data.get('detect_tables', 'true') if form_data else 'true'
        enhance_image = form_data.get('enhance_image', 'true') if form_data else 'true'
        
        # Support des langues multiples (format: "fra+eng+spa")
        selected_languages = language.split('+') if '+' in language else [language]
        
        # CARTE COMPLÈTE DES LANGUES OCR - 11 langues supportées
        lang_map = {
            # Code interface -> Code Tesseract
            'fra': 'fra',      # Français
            'en': 'eng',       # Anglais
            'es': 'spa',       # Espagnol
            'de': 'deu',       # Allemand
            'it': 'ita',       # Italien
            'pt': 'por',       # Portugais
            'ru': 'rus',       # Russe
            'ar': 'ara',       # Arabe
            'zh': 'chi_sim',   # Chinois simplifié
            'ja': 'jpn',       # Japonais
            'nl': 'nld'        # Néerlandais
        }
        
        # Construire la chaîne de langues pour Tesseract
        ocr_langs = []
        for lang_code in selected_languages:
            if lang_code in lang_map:
                ocr_langs.append(lang_map[lang_code])
                logger.info(f"✅ Langue OCR ajoutée: {lang_code} -> {lang_map[lang_code]}")
            else:
                # Fallback vers français si langue non reconnue
                logger.warning(f"⚠️ Langue non reconnue: {lang_code}, fallback vers français")
                ocr_langs.append('fra')
        
        # Si aucune langue valide, utiliser français par défaut
        ocr_lang = '+'.join(ocr_langs) if ocr_langs else 'fra'
        logger.info(f"🔤 Langues OCR sélectionnées: {ocr_lang}")
        
        # Prétraitement de l'image pour améliorer l'OCR
        processed_img = img
        if enhance_image == 'true':
            try:
                # Convertir en niveaux de gris
                if processed_img.mode != 'L':
                    processed_img = processed_img.convert('L')
                
                # Améliorer le contraste
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(processed_img)
                processed_img = enhancer.enhance(2.0)
                
                # Binarisation adaptative pour meilleure détection des tableaux
                import numpy as np
                img_array = np.array(processed_img)
                
                # Seuillage adaptatif
                from PIL import ImageOps
                processed_img = ImageOps.autocontrast(processed_img)
                
                # Sauvegarder l'image améliorée
                temp_enhanced = tempfile.NamedTemporaryFile(suffix='_enhanced.png', delete=False)
                processed_img.save(temp_enhanced.name, 'PNG')
                temp_files.append(temp_enhanced.name)
                logger.info("✨ Image améliorée pour OCR")
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'amélioration de l'image: {e}")
                processed_img = img
        
        if detect_tables == 'true':
            # DÉTECTION AVANCÉE DES TABLEAUX
            logger.info("🔍 Détection avancée des tableaux...")
            
            # Configuration Tesseract optimisée pour les tableaux
            # --psm 6: Assume a single uniform block of text
            # --psm 11: Sparse text (finds text in no particular order)
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:!?()[]{}-+*/=@#$%& "'
            
            # Obtenir les données détaillées avec positions
            data = pytesseract.image_to_data(
                processed_img, 
                lang=ocr_lang, 
                output_type=Output.DICT,
                config=custom_config
            )
            
            # Organiser les données en tableau 2D
            rows_dict = {}
            row_threshold = 15  # Seuil pour considérer qu'on change de ligne
            col_threshold = 30  # Seuil pour grouper les colonnes
            
            # Première passe : collecter tous les mots avec leurs positions
            for i, text in enumerate(data['text']):
                if text and text.strip():
                    conf = int(data['conf'][i])
                    # Ignorer les détections de faible confiance
                    if conf < 30:
                        continue
                    
                    top = data['top'][i]
                    left = data['left'][i]
                    width = data['width'][i]
                    height = data['height'][i]
                    
                    # Trouver la ligne appropriée
                    row_found = False
                    for row_top in rows_dict.keys():
                        if abs(top - row_top) <= row_threshold:
                            # Ajouter à cette ligne
                            if row_top not in rows_dict:
                                rows_dict[row_top] = []
                            rows_dict[row_top].append({
                                'text': text.strip(),
                                'left': left,
                                'width': width,
                                'height': height,
                                'conf': conf
                            })
                            row_found = True
                            break
                    
                    if not row_found:
                        # Nouvelle ligne
                        rows_dict[top] = [{
                            'text': text.strip(),
                            'left': left,
                            'width': width,
                            'height': height,
                            'conf': conf
                        }]
            
            # Trier les lignes par position Y
            sorted_rows = sorted(rows_dict.items(), key=lambda x: x[0])
            
            # Construire le tableau 2D
            table_data = []
            headers_detected = False
            potential_headers = []
            
            for row_top, words in sorted_rows:
                # Trier les mots dans la ligne par position X
                sorted_words = sorted(words, key=lambda w: w['left'])
                
                # Extraire le texte de la ligne
                row_text = [word['text'] for word in sorted_words]
                
                # Vérifier si cette ligne pourrait être un en-tête
                if not headers_detected and len(row_text) > 1:
                    # Les en-têtes ont souvent des mots plus courts et en gras
                    avg_word_length = sum(len(w) for w in row_text) / len(row_text)
                    if avg_word_length < 10:  # Les en-têtes sont généralement courts
                        potential_headers = row_text
                        headers_detected = True
                        continue  # Ne pas ajouter comme ligne de données
                
                table_data.append(row_text)
            
            # Si des en-têtes ont été détectés, les utiliser
            if potential_headers:
                # S'assurer que toutes les lignes ont le même nombre de colonnes
                max_cols = len(potential_headers)
                for i in range(len(table_data)):
                    if len(table_data[i]) < max_cols:
                        table_data[i].extend([''] * (max_cols - len(table_data[i])))
                    elif len(table_data[i]) > max_cols:
                        table_data[i] = table_data[i][:max_cols]
                
                # Créer le DataFrame avec les en-têtes
                df = pd.DataFrame(table_data, columns=potential_headers)
            else:
                # Pas d'en-têtes détectés, utiliser des colonnes génériques
                if table_data:
                    max_cols = max(len(row) for row in table_data)
                    # Ajuster toutes les lignes pour avoir le même nombre de colonnes
                    padded_rows = []
                    for row in table_data:
                        padded_row = row + [''] * (max_cols - len(row))
                        padded_rows.append(padded_row)
                    
                    # Créer des noms de colonnes génériques
                    columns = [f'Colonne {i+1}' for i in range(max_cols)]
                    df = pd.DataFrame(padded_rows, columns=columns)
                else:
                    df = pd.DataFrame({'Avertissement': ['Aucune donnée détectée dans l\'image']})
            
            logger.info(f"✅ Tableau détecté: {df.shape[0]} lignes x {df.shape[1]} colonnes")
            
        else:
            # OCR SIMPLE SANS DÉTECTION DE TABLEAUX
            logger.info("📝 OCR simple sans détection de tableaux")
            
            # Configuration pour texte simple
            custom_config = r'--oem 3 --psm 3'
            text = pytesseract.image_to_string(
                processed_img, 
                lang=ocr_lang,
                config=custom_config
            )
            
            # Nettoyer le texte
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if lines:
                df = pd.DataFrame({'Texte extrait': lines})
                logger.info(f"✅ {len(lines)} lignes de texte extraites")
            else:
                df = pd.DataFrame({'Avertissement': ['Aucun texte détecté dans l\'image']})
        
        # Sauvegarder en Excel avec formatage amélioré
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille principale
            df.to_excel(writer, index=False, sheet_name='Image_OCR')
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Image_OCR']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Feuille de résumé détaillée
            summary_data = {
                'Information': [
                    'Fichier source',
                    'Dimensions image',
                    'Mode couleur',
                    'Langues sélectionnées',
                    'Langues OCR utilisées',
                    'Détection tableaux',
                    'Amélioration image',
                    'Lignes détectées',
                    'Colonnes détectées',
                    'Date de conversion',
                    'Taille du fichier'
                ],
                'Valeur': [
                    Path(file_storage.filename).name,
                    f"{img.size[0]} x {img.size[1]} pixels",
                    img.mode,
                    ', '.join(selected_languages),
                    ocr_lang,
                    'Oui' if detect_tables == 'true' else 'Non',
                    'Oui' if enhance_image == 'true' else 'Non',
                    str(df.shape[0]),
                    str(df.shape[1]) if df.shape[1] > 0 else 'N/A',
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    f"{os.path.getsize(temp_input.name) / 1024:.1f} KB"
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
            
            # Ajuster la largeur des colonnes du résumé
            summary_sheet = writer.sheets['Résumé']
            summary_sheet.column_dimensions['A'].width = 25
            summary_sheet.column_dimensions['B'].width = 40
        
        output.seek(0)
        logger.info(f"✅ Fichier Excel généré: {output.getbuffer().nbytes} octets")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{Path(file_storage.filename).stem}.xlsx"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur Image->Excel: {str(e)}")
        logger.error(traceback.format_exc())
        return {'error': f'Erreur lors de la conversion: {str(e)}'}
    
    finally:
        # Nettoyer les fichiers temporaires
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"🧹 Nettoyage: {temp_file}")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage {temp_file}: {e}")


def convert_csv_to_excel(files, form_data=None):
    """Convertit un ou plusieurs fichiers CSV en Excel avec résumé et colonnes ajustées."""
    if not HAS_PANDAS:
        return {'error': 'pandas non installé'}
    
    import pandas as pd
    import chardet

    try:
        delimiter_option = form_data.get('delimiter', 'auto') if form_data else 'auto'
        encoding_option = form_data.get('encoding', 'utf-8') if form_data else 'utf-8'
        has_header = form_data.get('has_header', 'true') if form_data else 'true'

        summary_rows = []

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for file in files:
                # Détection de l'encodage si auto
                raw_sample = file.read(1024)
                file.seek(0)
                if encoding_option == 'auto':
                    detected = chardet.detect(raw_sample)
                    encoding = detected.get('encoding', 'utf-8')
                else:
                    encoding = encoding_option

                # Détection du séparateur
                sep = ','
                if delimiter_option == 'auto':
                    sample_text = raw_sample.decode(encoding, errors='ignore')
                    if ';' in sample_text:
                        sep = ';'
                    elif '\t' in sample_text:
                        sep = '\t'

                # Lire CSV
                header_row = 0 if has_header == 'true' else None
                df = pd.read_csv(file.stream, sep=sep, encoding=encoding, header=header_row)

                # Nom de la feuille limité à 31 caractères
                sheet_name = Path(file.filename).stem[:31] or 'Sheet1'
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Ajuster largeur colonnes
                worksheet = writer.sheets[sheet_name]
                for col in worksheet.columns:
                    max_len = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        try:
                            if cell.value:
                                max_len = max(max_len, len(str(cell.value)))
                        except:
                            pass
                    worksheet.column_dimensions[col_letter].width = min(max_len + 2, 50)

                # Ajouter au résumé
                summary_rows.append({
                    'Fichier': file.filename,
                    'Lignes': df.shape[0],
                    'Colonnes': df.shape[1],
                    'Encodage utilisé': encoding,
                    'Séparateur': sep
                })

            # Ajouter une feuille Résumé
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)

            # Ajuster largeur colonnes résumé
            summary_ws = writer.sheets['Résumé']
            for col in summary_ws.columns:
                max_len = max(len(str(cell.value)) for cell in col)
                summary_ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 50)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name="csv_converted.xlsx"
        )

    except Exception as e:
        logger.error(f"Erreur CSV->Excel: {str(e)}")
        return {'error': f'Erreur lors de la conversion: {str(e)}'}


def convert_excel_to_csv(files, form_data=None):
    """Convertit un ou plusieurs fichiers Excel en CSV, avec ZIP si multi-fichiers."""
    if not HAS_PANDAS:
        return {'error': 'pandas non installé'}
    
    import pandas as pd
    import zipfile
    from io import BytesIO
    from pathlib import Path

    try:
        delimiter = form_data.get('delimiter', ',') if form_data else ','
        encoding = form_data.get('encoding', 'utf-8') if form_data else 'utf-8'
        sheet_name_option = form_data.get('sheet_name', '0') if form_data else '0'
        include_header = form_data.get('include_header', 'true') if form_data else 'true'

        # Plusieurs fichiers -> créer un ZIP
        if len(files) > 1:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files:
                    try:
                        # Lire la feuille
                        sheet_name = 0 if sheet_name_option == '0' else sheet_name_option
                        df = pd.read_excel(file.stream, sheet_name=sheet_name)

                        # CSV dans buffer
                        csv_buffer = BytesIO()
                        df.to_csv(csv_buffer, sep=delimiter, index=False, header=include_header=='true', encoding=encoding)
                        csv_buffer.seek(0)

                        # Ajouter au ZIP
                        zip_file.writestr(f"{Path(file.filename).stem}.csv", csv_buffer.getvalue())
                        logger.info(f"✅ Excel->CSV ajouté au ZIP: {file.filename}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur conversion {file.filename}: {e}")

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
            sheet_name = 0 if sheet_name_option == '0' else sheet_name_option
            try:
                df = pd.read_excel(file.stream, sheet_name=sheet_name)
            except Exception:
                df = pd.read_excel(file.stream, sheet_name=0)

            output = BytesIO()
            df.to_csv(output, sep=delimiter, index=False, header=include_header=='true', encoding=encoding)
            output.seek(0)

            logger.info(f"✅ Excel->CSV généré: {file.filename}")
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
    """Caviardage avancé avec PyMuPDF (fitz) - Optimisé"""
    try:
        import fitz
        import re

        # Ouvrir le document
        doc = fitz.open(input_path)

        output = BytesIO()
        
        # Parcourir les pages
        for page_num in range(len(doc)):
            if pages_to_process is not None and page_num not in pages_to_process:
                continue

            page = doc[page_num]
            page_text = page.get_text()  # Texte unique pour toutes les recherches
            total_redacted = 0

            if redact_type == 'text' and search_texts:
                for search_text in search_texts:
                    if not search_text:
                        continue
                    text_instances = page.search_for(search_text)
                    for inst in text_instances:
                        redact_annot = page.add_redact_annot(inst)
                        redact_annot.set_colors(fill=rgb)
                        redact_annot.update()
                        total_redacted += 1

            elif redact_type == 'pattern' and search_texts:
                for pattern in search_texts:
                    areas_to_redact = []

                    if pattern == 'email':
                        matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
                        for m in matches:
                            areas_to_redact.extend(page.search_for(m))

                    elif pattern == 'phone':
                        matches = re.findall(r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b', page_text)
                        for m in matches:
                            areas_to_redact.extend(page.search_for(m))

                    elif pattern == 'creditcard':
                        matches = re.findall(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', page_text)
                        for m in matches:
                            areas_to_redact.extend(page.search_for(m))

                    elif pattern == 'ssn':
                        matches = re.findall(r'\b\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\b', page_text)
                        for m in matches:
                            areas_to_redact.extend(page.search_for(m))

                    # Appliquer toutes les annotations trouvées
                    for area in areas_to_redact:
                        redact_annot = page.add_redact_annot(area)
                        redact_annot.set_colors(fill=rgb)
                        redact_annot.update()
                        total_redacted += 1

            elif redact_type == 'area':
                logger.warning("Caviardage par zone non implémenté")
                # Ici, tu pourrais gérer les zones via form_data['areas']

            logger.info(f"Page {page_num+1}: {total_redacted} occurrences caviardées")

            # Appliquer immédiatement les redactions pour cette page
            page.apply_redactions()

        # Sauvegarder le PDF caviardé
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
    """Caviardage avancé avec pdfplumber et reportlab"""
    try:
        import pdfplumber
        import re
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import Color
        import pypdf

        pdf = pdfplumber.open(input_path)
        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PdfWriter()
        r, g, b = [x/255 for x in rgb]

        for page_num, page in enumerate(pdf.pages):
            if pages_to_process is not None and page_num not in pages_to_process:
                pdf_writer.add_page(pdf_reader.pages[page_num])
                continue

            words = page.extract_words()
            text_page = page.extract_text() or ""
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.width, page.height))
            can.setFillColorRGB(r, g, b)
            redaction_applied = 0

            if redact_type == 'text' and search_texts:
                for search_text in search_texts:
                    search_lower = search_text.lower()
                    for i in range(len(words) - len(search_text.split()) + 1):
                        candidate = ' '.join(words[j]['text'] for j in range(i, i + len(search_text.split())))
                        if candidate.lower() == search_lower:
                            for j in range(i, i + len(search_text.split())):
                                word = words[j]
                                x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
                                can.rect(x0, page.height - y1, x1 - x0, y1 - y0, fill=1, stroke=0)
                                redaction_applied += 1

            elif redact_type == 'pattern' and search_texts:
                patterns = {
                    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'phone': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b',
                    'creditcard': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                    'ssn': r'\b\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\b'
                }
                for p in search_texts:
                    if p in patterns:
                        matches = re.findall(patterns[p], text_page)
                        for m in matches:
                            for word in words:
                                if m in word['text']:
                                    x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
                                    can.rect(x0, page.height - y1, x1 - x0, y1 - y0, fill=1, stroke=0)
                                    redaction_applied += 1

            can.save()

            if redaction_applied > 0:
                packet.seek(0)
                overlay_pdf = pypdf.PdfReader(packet)
                page_orig = pdf_reader.pages[page_num]
                page_orig.merge_page(overlay_pdf.pages[0])
                pdf_writer.add_page(page_orig)
            else:
                pdf_writer.add_page(pdf_reader.pages[page_num])

            logger.info(f"Page {page_num+1}: {redaction_applied} zones caviardées")

        pdf.close()
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
    """Méthode basique de caviardage avec pypdf uniquement (approximation)"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PdfWriter()

        for page_num, page in enumerate(pdf_reader.pages):
            if pages_to_process is not None and page_num not in pages_to_process:
                pdf_writer.add_page(page)
                continue

            if redact_type == 'text' and search_texts:
                text = page.extract_text() or ""  # protéger contre None

                # Taille de la page réelle
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                # Créer un overlay correspondant à la taille exacte
                packet = BytesIO()
                can = canvas.Canvas(packet, pagesize=(page_width, page_height))
                can.setFillColorRGB(0, 0, 0)  # noir par défaut

                # Approximatif : on répartit les lignes verticalement
                lines = text.split('\n')
                n_lines = len(lines) or 1
                line_height = page_height / max(n_lines, 1)

                for i, line in enumerate(lines):
                    y_position = page_height - (i + 1) * line_height
                    for search_text in search_texts:
                        if search_text and search_text in line:
                            # Rectangle approximatif couvrant la ligne
                            can.rect(0, y_position, page_width, line_height, fill=1, stroke=0)

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

def redact_area_in_page(page, x, y, width, height, color="#000000"):
    """
    Caviarde une zone rectangulaire spécifique dans une page.
    Utilise PyMuPDF si disponible, sinon fallback avec pypdf + reportlab.
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]

    try:
        # PyMuPDF si disponible
        import fitz
        if isinstance(color, str):
            rgb = hex_to_rgb(color)
        else:
            rgb = [0, 0, 0]

        rect = fitz.Rect(x, y, x + width, y + height)
        annot = page.add_redact_annot(rect)
        annot.set_colors(fill=rgb)
        annot.update()
        page.apply_redactions()
        return page

    except ImportError:
        # Fallback pypdf + reportlab
        try:
            from reportlab.pdfgen import canvas

            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))

            if isinstance(color, str):
                r, g, b = hex_to_rgb(color)
                can.setFillColorRGB(r, g, b)
            else:
                can.setFillColorRGB(0, 0, 0)

            # Conversion coordonnées bas‑gauche
            can.rect(x, page.mediabox.height - y - height, width, height, fill=1, stroke=0)
            can.save()

            packet.seek(0)
            overlay_pdf = pypdf.PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])
            return page

        except Exception as e:
            logger.error(f"Erreur dans redact_area_in_page (fallback): {str(e)}")
            return page

    except Exception as e:
        logger.error(f"Erreur dans redact_area_in_page: {str(e)}")
        return page

def redact_pattern_in_page(page, patterns, color="#000000"):
    """
    Caviarde les motifs (emails, téléphones, cartes, SSN, noms, dates) dans une page avec PyMuPDF.
    """
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]

    try:
        import fitz
        import re

        text = page.get_text()

        # Patterns prédéfinis
        pattern_dict = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b',
            'creditcard': r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
            'ssn': r'\b\d{1,2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\b',
            'name': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        }

        rgb = hex_to_rgb(color) if isinstance(color, str) else [0, 0, 0]

        for pattern_name in patterns:
            regex = pattern_dict.get(pattern_name, pattern_name)  # fallback si regex custom
            matches = re.findall(regex, text)
            for match in matches:
                areas = page.search_for(match)
                for area in areas:
                    annot = page.add_redact_annot(area)
                    annot.set_colors(fill=rgb)
                    annot.update()

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
    Édite un PDF : ajoute/modifie du texte, ajoute une image, supprime ou réorganise les pages.
    Totalement indépendant de Flask pour l'upload d'image.
    """
    if not HAS_PYPDF or not HAS_REPORTLAB:
        return {'error': 'pypdf ou reportlab non installé'}

    try:
        import shutil
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader

        # Dossier temporaire
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)

        # Lire le PDF
        pdf_reader = pypdf.PdfReader(input_path)
        pdf_writer = pypdf.PdfWriter()

        total_pages = len(pdf_reader.pages)

        # Options par défaut
        edit_type = form_data.get('edit_type', 'add_text') if form_data else 'add_text'
        page_number = int(form_data.get('page_number', '1')) - 1 if form_data else 0
        page_number = max(0, min(page_number, total_pages - 1))
        position_x = float(form_data.get('position_x', '50')) if form_data else 50
        position_y = float(form_data.get('position_y', '50')) if form_data else 50
        text_content = form_data.get('text_content', '') if form_data else ''
        font_size = int(form_data.get('font_size', '12')) if form_data else 12
        font_color = form_data.get('font_color', '#000000') if form_data else '#000000'
        image_file = form_data.get('image_file', None)  # doit être un file-like
        page_order = form_data.get('page_order', '') if form_data else ''
        pages_to_delete = form_data.get('pages_to_delete', '') if form_data else ''

        # Fonction pour créer un overlay texte
        def create_text_overlay(text, x, y, size, color, width=595, height=842):
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            if color.startswith('#'):
                color = color[1:]
                r, g, b = tuple(int(color[i:i+2], 16)/255 for i in (0,2,4))
                can.setFillColorRGB(r, g, b)
            else:
                can.setFillColorRGB(0,0,0)
            can.setFont("Helvetica", size)
            can.drawString(x, height - y - size, text)
            can.save()
            packet.seek(0)
            return pypdf.PdfReader(packet)

        # Fonction pour créer un overlay image
        def create_image_overlay(image_file, x, y, width=None, height=None, page_width=595, page_height=842):
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(page_width, page_height))
            img_reader = ImageReader(image_file)
            img_width, img_height = img_reader.getSize()
            if width is None:
                width = img_width
            if height is None:
                height = img_height
            can.drawImage(img_reader, x, page_height - y - height, width, height)
            can.save()
            packet.seek(0)
            return pypdf.PdfReader(packet)

        # Gestion des pages à supprimer
        delete_set = set()
        if pages_to_delete:
            for part in pages_to_delete.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    delete_set.update(range(start-1, end))
                else:
                    delete_set.add(int(part)-1)

        # Gestion de l'ordre des pages
        if edit_type == 'reorder' and page_order:
            order = [int(p.strip())-1 for p in page_order.split(',') if p.strip()]
            order = [p for p in order if 0 <= p < total_pages]
            for page_num in order:
                pdf_writer.add_page(pdf_reader.pages[page_num])
        else:
            # Boucle normale
            for i, page in enumerate(pdf_reader.pages):
                if i in delete_set:
                    continue  # sauter cette page
                # Texte
                if edit_type == 'add_text' and i == page_number and text_content:
                    overlay_pdf = create_text_overlay(text_content, position_x, position_y, font_size, font_color,
                                                      width=page.mediabox.width, height=page.mediabox.height)
                    page.merge_page(overlay_pdf.pages[0])
                # Image
                if edit_type == 'add_image' and i == page_number and image_file:
                    overlay_pdf = create_image_overlay(image_file, position_x, position_y,
                                                      page_width=page.mediabox.width, page_height=page.mediabox.height)
                    page.merge_page(overlay_pdf.pages[0])
                pdf_writer.add_page(page)

        # Métadonnées
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


def create_text_overlay(text, x, y, page_width=595, page_height=842, font_size=12, color='#000000'):
    """Crée un PDF overlay avec du texte, adaptable à n'importe quelle page."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    can.setFont("Helvetica", font_size)
    can.setFillColor(HexColor(color))
    can.drawString(x, page_height - y - font_size, text)  # y inversé + décalage font_size
    can.save()
    
    packet.seek(0)
    return pypdf.PdfReader(packet)


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
    Ajoute une signature électronique à un PDF (image ou texte).
    Supporte plusieurs pages et tailles dynamiques.
    """
    if not HAS_PYPDF or not HAS_PILLOW:
        return {'error': 'pypdf ou Pillow non installé'}

    try:
        # Lire le PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        pdf_writer = pypdf.PyPdfWriter()

        # Récupérer les options
        signature_type = form_data.get('signature_type', 'draw') if form_data else 'draw'
        page_numbers = form_data.get('page_numbers', '1') if form_data else '1'
        position_x = float(form_data.get('position_x', '50')) if form_data else 50
        position_y = float(form_data.get('position_y', '50')) if form_data else 50
        signature_text = form_data.get('signature_text', '') if form_data else ''
        max_width = int(form_data.get('max_width', '200')) if form_data else 200
        max_height = int(form_data.get('max_height', '100')) if form_data else 100

        # Transformer page_numbers en liste d’indices
        pages_to_sign = []
        for part in page_numbers.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages_to_sign.extend(range(start-1, end))
            else:
                pages_to_sign.append(int(part)-1)

        overlay_pdf = None

        if signature_type == 'draw' and 'signature_image' in request.files:
            sig_file = request.files['signature_image']
            overlay_pdf = create_signature_overlay(sig_file, position_x, position_y,
                                                   max_width=max_width, max_height=max_height)

        elif signature_type == 'type' and signature_text:
            font_size = int(form_data.get('font_size', '24')) if form_data else 24
            font_family = form_data.get('font_family', 'Courier') if form_data else 'Courier'
            overlay_pdf = create_text_signature(signature_text, position_x, position_y,
                                               font_size, font_family)

        elif signature_type == 'certificate':
            return {'error': 'Signature numérique avec certificat non encore implémentée'}

        # Appliquer la signature
        for i, page in enumerate(pdf_reader.pages):
            if i in pages_to_sign and overlay_pdf:
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


def create_signature_overlay(signature_file, x, y, max_width=200, max_height=100):
    """
    Crée un overlay PDF avec une signature image.
    Redimensionne automatiquement si la signature dépasse max_width / max_height.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from PIL import Image

    # Sauvegarder l'image temporairement
    temp_img = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    signature_file.save(temp_img.name)

    # Redimensionner si nécessaire
    img = Image.open(temp_img.name)
    if img.width > max_width or img.height > max_height:
        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img.save(temp_img.name, 'PNG')

    # Créer overlay PDF
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

    # Nettoyer le fichier temporaire
    os.unlink(temp_img.name)

    return overlay_pdf


def create_text_signature(text, x, y, font_size=24, font_family='Courier', color='#0000FF'):
    """Crée un overlay avec une signature textuelle."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor

    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Style manuscrit approximatif
    if font_family == 'Courier':
        can.setFont('Helvetica-Oblique', font_size)
    else:
        can.setFont(font_family, font_size)
    
    can.setFillColor(HexColor(color))
    can.drawString(x, letter[1] - y, text)
    
    # Ligne sous la signature
    can.line(x, letter[1] - y - 5, x + len(text) * font_size * 0.6, letter[1] - y - 5)
    
    can.save()
    packet.seek(0)
    
    overlay_pdf = pypdf.PdfReader(packet)
    return overlay_pdf


def prepare_form(file, form_data=None, ocr_enabled=True):
    """
    Prépare un formulaire PDF interactif ultra complet.
    - Détecte automatiquement champs texte, date, signature, checkbox, emails, téléphone, code postal.
    - Supporte PDF, Word, Excel, Images.
    - OCR intégré pour les PDFs scannés ou images.
    """
    try:
        # Vérifier les bibliothèques
        if not (HAS_PYPDF and HAS_REPORTLAB):
            return {'error': 'pypdf ou reportlab non installé'}
        import fitz
        import pdfplumber
        if ocr_enabled:
            import pytesseract
            from PIL import Image
        
        # Préparer le fichier source
        filename = file.filename
        ext = Path(filename).suffix.lower()
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, secure_filename(filename))
        file.save(input_path)
        pdf_path = input_path

        # Conversion Word/Excel -> PDF
        if ext in ['.doc', '.docx', '.xls', '.xlsx']:
            pdf_path = os.path.join(temp_dir, f"{Path(filename).stem}.pdf")
            try:
                subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', temp_dir, input_path
                ], check=True, capture_output=True)
            except:
                return {'error': f'Impossible de convertir {ext} en PDF'}

        # Conversion image -> PDF
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            if not (HAS_PILLOW and HAS_REPORTLAB):
                return {'error': 'Pillow ou reportlab non installé pour la conversion image->PDF'}
            pdf_path = os.path.join(temp_dir, f"{Path(filename).stem}.pdf")
            img = Image.open(input_path)
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4

            c = canvas.Canvas(pdf_path, pagesize=A4)
            w, h = A4
            ratio = min(w / img.width, h / img.height)
            new_w, new_h = img.width * ratio * 0.9, img.height * ratio * 0.9
            x = (w - new_w) / 2
            y = (h - new_h) / 2

            temp_img = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            img.save(temp_img.name, 'JPEG')
            c.drawImage(temp_img.name, x, y, width=new_w, height=new_h)
            c.save()
            os.unlink(temp_img.name)

        # Lecture PDF
        pdf_reader = pypdf.PdfReader(pdf_path)
        pdf_writer = pypdf.PdfWriter()
        form_fields = []

        # Analyse avec PyMuPDF + pdfplumber + OCR
        pdf_doc = fitz.open(pdf_path)
        pdf_pl = pdfplumber.open(pdf_path)
        keywords = ['nom', 'prénom', 'date', 'adresse', 'email', 'téléphone',
                    'ville', 'code postal', 'signature', 'commentaire', 'checkbox']

        for page_num, (page_fitz, page_pl) in enumerate(zip(pdf_doc, pdf_pl.pages)):
            # Texte standard
            words = page_pl.extract_words()
            # OCR si activé et page vide
            text_blocks = page_fitz.get_text("blocks")
            page_text = page_fitz.get_text()
            if ocr_enabled and not page_text.strip():
                pix = page_fitz.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img)
                # Ajouter mots OCR comme mots "simulés"
                y_pos = pix.height - 50
                for line in ocr_text.split('\n'):
                    x_pos = 50
                    for word in line.split():
                        words.append({'text': word, 'x0': x_pos, 'top': y_pos,
                                      'x1': x_pos + len(word)*6, 'bottom': y_pos + 12})
                        x_pos += len(word)*6 + 5
                    y_pos -= 20

            # Détection des champs
            for keyword in keywords:
                for word in words:
                    if keyword in word['text'].lower():
                        field_type = 'text'
                        if keyword == 'signature':
                            field_type = 'signature'
                        elif keyword == 'date':
                            field_type = 'date'
                        elif keyword == 'checkbox':
                            field_type = 'checkbox'
                        elif keyword == 'email':
                            field_type = 'text'
                        form_fields.append({
                            'page': page_num,
                            'label': word['text'],
                            'type': field_type,
                            'x': float(word['x0']),
                            'y': float(page_pl.height - word['top']),
                            'width': float(word['x1'] - word['x0']),
                            'height': float(word['bottom'] - word['top'])
                        })

        # Copier les pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)

        # Création AcroForm interactif
        if form_fields:
            from pypdf.generic import NameObject, create_string_object, DictionaryObject, ArrayObject
            acroform = DictionaryObject()
            fields_array = ArrayObject()

            for i, field in enumerate(form_fields):
                ft_type = "/Tx"
                if field['type'] == 'checkbox':
                    ft_type = "/Btn"

                rect = ArrayObject([
                    pypdf.generic.NumberObject(field['x']),
                    pypdf.generic.NumberObject(field['y'] - field['height']),
                    pypdf.generic.NumberObject(field['x'] + field['width']),
                    pypdf.generic.NumberObject(field['y'])
                ])
                field_dict = DictionaryObject({
                    NameObject("/FT"): NameObject(ft_type),
                    NameObject("/T"): create_string_object(f"Field_{i}"),
                    NameObject("/TU"): create_string_object(field['label']),
                    NameObject("/Rect"): rect,
                    NameObject("/Ff"): pypdf.generic.NumberObject(2),
                    NameObject("/P"): pdf_writer.pages[field['page']].indirect_reference
                })
                fields_array.append(field_dict)

            acroform[NameObject("/Fields")] = fields_array
            pdf_writer._root_object[NameObject("/AcroForm")] = acroform

        # Métadonnées
        pdf_writer.add_metadata({
            '/Producer': 'PDF Fusion Pro Ultimate',
            '/Creator': 'PDF Fusion Pro Ultimate',
            '/Title': f"{Path(filename).stem} (formulaire complet)",
            '/CreationDate': datetime.now().strftime('D:%Y%m%d%H%M%S')
        })

        # Sauvegarde finale
        output = BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        shutil.rmtree(temp_dir, ignore_errors=True)

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{Path(filename).stem}_form_ultimate.pdf"
        )

    except Exception as e:
        logger.error(f"Erreur préparation formulaire ultimate: {str(e)}")
        return {'error': f'Erreur lors de la préparation du formulaire ultimate: {str(e)}'}

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
