#!/usr/bin/env python3
"""
Blueprint pour les conversions de fichiers - Version universelle
"""
from flask import Blueprint, after_this_request, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
import sys
import os
import json
os.environ["OMP_THREAD_LIMIT"] = "1"
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from pypdf import PdfMerger
import shutil
import traceback
from io import BytesIO
from collections import defaultdict
from typing import Dict, List, Optional, Any, Union
import subprocess
import logging
import importlib
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from flask_babel import _, lazy_gettext as _l

# =========================
# CONSTANTES GLOBALES
# =========================
# Ajoutez ceci après les imports, avant les vérifications de dépendances
OCR_LANG_MAP = {
    'fra': 'fra', 'en': 'eng', 'es': 'spa', 'de': 'deu', 
    'it': 'ita', 'pt': 'por', 'ru': 'rus', 'ar': 'ara',
    'zh': 'chi_sim', 'ja': 'jpn', 'nl': 'nld'
}

PDF_PERMISSIONS_MAP = {
    'can_print': 4,
    'can_modify': 8,
    'can_copy': 16,
    'can_annotate': 32,
    'can_fill_forms': 256,
    'can_extract_for_accessibility': 512,
    'can_assemble': 1024,
    'can_print_high_res': 2048
}
# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
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
    from PIL import  Image, ImageOps, ImageFilter, ImageDraw, ImageEnhance
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
    from sklearn.cluster import KMeans
    import numpy as np
    HAS_NUMPY = True
    HAS_SKLEARN = True
except ImportError:
    np = None
    KMeans = None
    HAS_NUMPY = False
    HAS_SKLEARN = False
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
        'title': _('Word vers PDF'),
        'description': _('Convertissez vos documents Word en PDF'),
        'from_format': _('Word'),
        'to_format': _('PDF'),
        'icon': 'file-word',
        'color': '#2b579a',
        'accept': '.doc,.docx',
        'max_files': 5,
        'deps': ['reportlab', 'libreoffice']
    },
    
    'excel-en-pdf': {
        'template': 'excel_to_pdf.html',
        'title': _('Excel vers PDF'),
        'description': _('Convertissez vos feuilles Excel en PDF'),
        'from_format': _('Excel'),
        'to_format': _('PDF'),
        'icon': 'file-excel',
        'color': '#217346',
        'accept': '.xls,.xlsx,.xlsm',
        'max_files': 5,
        'deps': ['reportlab', 'libreoffice']
    },
    
    'powerpoint-en-pdf': {
        'template': 'powerpoint_to_pdf.html',
        'title': _('PowerPoint vers PDF'),
        'description': _('Convertissez vos présentations PowerPoint en PDF'),
        'from_format': _('PowerPoint'),
        'to_format': _('PDF'),
        'icon': 'file-powerpoint',
        'color': '#d24726',
        'accept': '.ppt,.pptx',
        'max_files': 5,
        'deps': ['reportlab', 'libreoffice']
    },
    
    'image-en-pdf': {
        'template': 'image_to_pdf.html',
        'title': _('Image vers PDF'),
        'description': _('Convertissez vos images en document PDF'),
        'from_format': _('Image'),
        'to_format': _('PDF'),
        'icon': 'file-image',
        'color': '#e74c3c',
        'accept': '.jpg,.jpeg,.png,.bmp,.gif,.tiff,.webp',
        'max_files': 20,
        'deps': ['Pillow', 'reportlab']
    },
    
    'jpg-en-pdf': {
        'template': 'image_to_pdf.html',
        'title': _('JPG vers PDF'),
        'description': _('Convertissez vos images JPG en PDF'),
        'from_format': _('JPG'),
        'to_format': _('PDF'),
        'icon': 'file-image',
        'color': '#e74c3c',
        'accept': '.jpg,.jpeg',
        'max_files': 20,
        'deps': ['Pillow', 'reportlab']
    },
    
    'png-en-pdf': {
        'template': 'image_to_pdf.html',
        'title': _('PNG vers PDF'),
        'description': _('Convertissez vos images PNG en PDF'),
        'from_format': _('PNG'),
        'to_format': _('PDF'),
        'icon': 'file-image',
        'color': '#e74c3c',
        'accept': '.png',
        'max_files': 20,
        'deps': ['Pillow', 'reportlab']
    },
    
    'html-en-pdf': {
        'template': 'html_to_pdf.html',
        'title': _('HTML vers PDF'),
        'description': _('Convertissez vos pages HTML en PDF'),
        'from_format': _('HTML'),
        'to_format': _('PDF'),
        'icon': 'code',
        'color': '#f16529',
        'accept': '.html,.htm',
        'max_files': 1,
        'deps': ['weasyprint', 'pdfkit']
    },
    
    'txt-en-pdf': {
        'template': 'txt_to_pdf.html',
        'title': _('TXT vers PDF'),
        'description': _('Convertissez vos fichiers texte en PDF'),
        'from_format': _('TXT'),
        'to_format': _('PDF'),
        'icon': 'file-alt',
        'color': '#3498db',
        'accept': '.txt',
        'max_files': 1,
        'deps': ['reportlab']
    },
    
    # ==================== CONVERTIR DEPUIS PDF ====================
    'pdf-en-word': {
        'template': 'pdf_to_word.html',
        'title': _('PDF vers Word'),
        'description': _('Extrayez le texte de vos PDF en documents Word'),
        'from_format': _('PDF'),
        'to_format': _('Word'),
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'python-docx']
    },
    
    'pdf-en-doc': {
        'template': 'pdf_to_doc.html',
        'title': _('PDF vers DOC'),
        'description': _('Convertissez vos PDF en documents Word (format DOC)'),
        'from_format': _('PDF'),
        'to_format': _('DOC'),
        'icon': 'file-word',
        'color': '#2b579a',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'python-docx']
    },
    
    'pdf-en-excel': {
        'template': 'pdf_to_excel.html',
        'title': _('PDF vers Excel'),
        'description': _('Extrayez les tableaux de vos PDF en feuilles Excel'),
        'from_format': _('PDF'),
        'to_format': _('Excel'),
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'pdf2image', 'pytesseract', 'pandas', 'openpyxl']
    },
    
    'pdf-en-ppt': {
        'template': 'pdf_to_ppt.html',
        'title': _('PDF vers PowerPoint'),
        'description': _('Convertissez vos PDF en présentations PowerPoint modifiables'),
        'from_format': _('PDF'),
        'to_format': _('PowerPoint'),
        'icon': 'file-powerpoint',
        'color': '#d24726',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pdf2image', 'Pillow', 'python-pptx']
    },
    
    'pdf-en-image': {
        'template': 'pdf_to_image.html',
        'title': _('PDF vers Image'),
        'description': _('Convertissez les pages de vos PDF en images'),
        'from_format': _('PDF'),
        'to_format': _('Image'),
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pdf2image']
    },
    
    'pdf-en-pdfa': {
        'template': 'pdf_to_pdfa.html',
        'title': _('PDF vers PDF/A'),
        'description': _('Convertissez vos PDF en format PDF/A pour l\'archivage'),
        'from_format': _('PDF'),
        'to_format': _('PDF/A'),
        'icon': 'file-pdf',
        'color': '#e74c3c',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },
    
    'pdf-en-html': {
        'template': 'pdf_to_html.html',
        'title': _('PDF vers HTML'),
        'description': _('Convertissez vos PDF en pages HTML'),
        'from_format': _('PDF'),
        'to_format': _('HTML'),
        'icon': 'code',
        'color': '#f16529',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },
    
    'pdf-en-txt': {
        'template': 'pdf_to_txt.html',
        'title': _('PDF vers TXT'),
        'description': _('Extrayez le texte de vos PDF en fichiers texte'),
        'from_format': _('PDF'),
        'to_format': _('TXT'),
        'icon': 'file-alt',
        'color': '#3498db',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },
    
    # ==================== OUTILS PDF ====================
    'proteger-pdf': {
        'template': 'protect_pdf.html',
        'title': _('Protéger PDF'),
        'description': _('Ajoutez un mot de passe pour protéger vos PDF'),
        'from_format': _('PDF'),
        'to_format': _('PDF'),
        'icon': 'lock',
        'color': '#e67e22',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },

    'deverrouiller-pdf': {
        'template': 'unlock_pdf.html',
        'title': _('Déverrouiller PDF'),
        'description': _('Retirez la protection des PDF'),
        'from_format': _('PDF'),
        'to_format': _('PDF'),
        'icon': 'unlock',
        'color': '#1abc9c',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf']
    },

    # ==================== NOUVEAUX OUTILS PDF ====================
    'redact-pdf': {
        'template': 'redact_pdf.html',
        'title': _('Caviarder PDF'),
        'description': _('Supprimez définitivement et en toute sécurité le contenu sensible de votre PDF'),
        'from_format': _('PDF'),
        'to_format': _('PDF'),
        'icon': 'mask',
        'color': '#e67e22',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow']
    },
    
    'edit-pdf': {
        'template': 'edit_pdf.html',
        'title': _('Éditer PDF'),
        'description': _('Modifiez ou ajoutez du texte, des images et des pages à votre PDF'),
        'from_format': _('PDF'),
        'to_format': _('PDF'),
        'icon': 'edit',
        'color': '#3498db',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow', 'reportlab']
    },
    
    'sign-pdf': {
        'template': 'sign_pdf.html',
        'title': _('Signer PDF'),
        'description': _('Ajoutez votre signature électronique à votre PDF'),
        'from_format': _('PDF'),
        'to_format': _('PDF'),
        'icon': 'pen',
        'color': '#27ae60',
        'accept': '.pdf',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow', 'reportlab']
    },
    
    'prepare-form': {
        'template': 'prepare_form.html',
        'title': _('Préparer formulaire PDF'),
        'description': _('Transformez vos documents Word, Excel ou numérisés en formulaires PDF interactifs'),
        'from_format': _('Document'),
        'to_format': _('PDF Formulaire'),
        'icon': 'file-signature',
        'color': '#9b59b6',
        'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png',
        'max_files': 1,
        'deps': ['pypdf', 'Pillow', 'reportlab', 'python-docx', 'pandas']
    },    
    
    # ==================== CONVERSIONS DIVERSES ====================
    'image-en-word': {
        'template': 'image_to_word.html',
        'title': _('Image vers Word'),
        'description': _('Extrayez le texte des images en documents Word'),
        'from_format': _('Image'),
        'to_format': _('Word'),
        'icon': 'image',
        'color': '#2b579a',
        'accept': '.jpg,.jpeg,.png,.bmp,.tiff',
        'max_files': 1,
        'deps': ['Pillow', 'pytesseract', 'python-docx']
    },
    
    'image-en-excel': {
        'template': 'image_to_excel.html',
        'title': _('Image vers Excel'),
        'description': _('Extrayez les tableaux des images en Excel'),
        'from_format': _('Image'),
        'to_format': _('Excel'),
        'icon': 'image',
        'color': '#217346',
        'accept': '.jpg,.jpeg,.png,.bmp,.tiff,.pdf',
        'max_files': 1,
        'deps': ['Pillow', 'pytesseract', 'pandas', 'openpyxl']
    },
    
    'csv-en-excel': {
        'template': 'csv_to_excel.html',
        'title': _('CSV vers Excel'),
        'description': _('Convertissez vos fichiers CSV en Excel'),
        'from_format': _('CSV'),
        'to_format': _('Excel'),
        'icon': 'file-csv',
        'color': '#217346',
        'accept': '.csv,.txt',
        'max_files': 5,
        'deps': ['pandas', 'openpyxl']
    },
    
    'excel-en-csv': {
        'template': 'excel_to_csv.html',
        'title': _('Excel vers CSV'),
        'description': _('Exportez vos feuilles Excel en CSV'),
        'from_format': _('Excel'),
        'to_format': _('CSV'),
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


# =========================
# PROCESS CONVERSION
# =========================

def handle_conversion_request(conversion_type, request, config):
    """Gère la requête de conversion."""
    # ✅ Debug temporaire — à supprimer après diagnostic
    current_app.logger.info(f"=== FILES KEYS: {list(request.files.keys())} ===")
    current_app.logger.info(f"=== FORM KEYS: {list(request.form.keys())} ===")
    current_app.logger.info(f"=== CONTENT-TYPE: {request.content_type} ===")

    try:
        if config['max_files'] > 1:
            # ✅ Chercher 'files' ET 'file' pour couvrir les deux cas
            files = request.files.getlist('files')
            if not files or all(f.filename == '' for f in files):
                files = request.files.getlist('file')

            # ✅ Log debug pour diagnostiquer
            current_app.logger.info(
                f"Fichiers reçus pour '{conversion_type}': "
                f"keys={list(request.files.keys())}, count={len(files)}"
            )

            files, error = normalize_files_input(files, max_files=config['max_files'])
            if error:
                flash(error['error'], 'error')
                return redirect(request.url)

            result = process_conversion(conversion_type, files=files, form_data=request.form)

        else:
            # ✅ Chercher 'file' ET 'files' pour couvrir les deux cas
            file = request.files.get('file')
            if not file or file.filename == '':
                file = request.files.get('files')

            current_app.logger.info(
                f"Fichier reçu pour '{conversion_type}': "
                f"keys={list(request.files.keys())}, filename={getattr(file, 'filename', 'None')}"
            )

            file, error = normalize_file_input(file)
            if error:
                flash(error['error'], 'error')
                return redirect(request.url)

            if config.get('accept'):
                allowed_ext = {ext.strip() for ext in config['accept'].split(',')}
                if not validate_file_extension(file.filename, allowed_ext):
                    flash(f"Type de fichier non supporté. Formats acceptés: {config['accept']}", 'error')
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
        'word-en-pdf': convert_word_to_pdf if HAS_REPORTLAB else None,
        'excel-en-pdf': convert_excel_to_pdf if HAS_REPORTLAB else None,
        'powerpoint-en-pdf': convert_powerpoint_to_pdf if HAS_REPORTLAB else None,
        'image-en-pdf': convert_images_to_pdf if HAS_PILLOW and HAS_REPORTLAB else None,
        'jpg-en-pdf': convert_images_to_pdf if HAS_PILLOW and HAS_REPORTLAB else None,
        'png-en-pdf': convert_images_to_pdf if HAS_PILLOW and HAS_REPORTLAB else None,
        'html-en-pdf': convert_html_to_pdf if HAS_PDFKIT or HAS_WEASYPRINT else None,
        'txt-en-pdf': convert_txt_to_pdf if HAS_REPORTLAB else None,

        # === CONVERSIONS DEPUIS PDF ===
        'pdf-en-word': convert_pdf_to_word if HAS_PYPDF and HAS_DOCX else None,
        'pdf-en-doc': convert_pdf_to_doc if HAS_PYPDF and HAS_DOCX else None,
        'pdf-en-excel': convert_pdf_to_excel if HAS_PDF2IMAGE and HAS_TESSERACT and HAS_PANDAS else None,
        'pdf-en-ppt': convert_pdf_to_ppt if HAS_PDF2IMAGE and HAS_PILLOW and HAS_PPTX else None,
        'pdf-en-image': convert_pdf_to_images if HAS_PDF2IMAGE else None,
        'pdf-en-pdfa': convert_pdf_to_pdfa if HAS_PYPDF else None,
        'pdf-en-html': convert_pdf_to_html if HAS_PYPDF else None,
        'pdf-en-txt': convert_pdf_to_txt if HAS_PYPDF else None,

        # === OUTILS PDF ===
        'proteger-pdf': protect_pdf_advanced if HAS_PYPDF else None,
        'deverrouiller-pdf': unlock_pdf if HAS_PYPDF else None,
        'redact-pdf': redact_pdf if HAS_PYPDF else None,
        'edit-pdf': edit_pdf if HAS_PYPDF and HAS_REPORTLAB else None,
        'sign-pdf': sign_pdf if HAS_PYPDF and HAS_PILLOW else None,
        'prepare-form': prepare_form if HAS_PYPDF and HAS_REPORTLAB else None,

        # === AUTRES CONVERSIONS ===
        'image-en-word': convert_image_to_word if HAS_PILLOW and HAS_TESSERACT and HAS_DOCX else None,
        'image-en-excel': convert_image_to_excel if HAS_PILLOW and HAS_TESSERACT and HAS_PANDAS else None,
        'csv-en-excel': convert_csv_to_excel if HAS_PANDAS else None,
        'excel-en-csv': convert_excel_to_csv if HAS_PANDAS else None
    }

    # Vérification type de conversion
    if conversion_type not in conversion_functions:
        return {'error': 'Type de conversion non implémenté'}

    func = conversion_functions[conversion_type]
    if func is None:
        return {'error': 'Cette conversion nécessite des dépendances manquantes'}

    try:
        # CAS 1: Plusieurs fichiers fournis
        if files is not None:
            # Les fichiers ont déjà été normalisés par normalize_files_input
            if not files:
                return {'error': 'Aucun fichier fourni'}
            
            # Liste des conversions qui acceptent plusieurs fichiers
            multi_file_conversions = ['csv-en-excel', 'excel-en-csv', 'image-en-pdf', 
                                      'jpg-en-pdf', 'png-en-pdf', 'word-en-pdf']
            
            if conversion_type in multi_file_conversions:
                # Ces fonctions acceptent directement une liste de fichiers
                return func(files, form_data)
            else:
                # Pour les autres conversions, on prend le premier fichier
                return func(files[0], form_data)
        
        # CAS 2: Un seul fichier fourni
        elif file is not None:
            # Le fichier a déjà été normalisé par normalize_file_input
            return func(file, form_data)
        
        # CAS 3: Aucun fichier fourni
        else:
            return {'error': 'Aucun fichier fourni pour la conversion'}
            
    except Exception as e:
        current_app.logger.error(f"Exception dans {conversion_type}: {str(e)}\n{traceback.format_exc()}")
        
        # Tentative de fallback PDF si possible
        try:
            # Déterminer le nom du fichier pour le fallback
            filename = "document"
            if file is not None:
                filename = getattr(file, 'filename', 'document')
            elif files is not None and len(files) > 0:
                filename = getattr(files[0], 'filename', 'document')
            
            return generate_fallback_pdf(filename, conversion_type)
            
        except Exception as fallback_e:
            current_app.logger.error(f"Erreur fallback PDF: {str(fallback_e)}")
            
        return {'error': f'Erreur interne: {str(e)}'}

def validate_file_extension(filename, allowed_extensions):
    """
    Vérifie si l'extension du fichier est autorisée.
    allowed_extensions peut être un set ou une liste d'extensions avec ou sans le point.
    """
    if not filename:
        return False
    
    # S'assurer que toutes les extensions commencent par un point
    normalized_exts = set()
    for ext in allowed_extensions:
        if not ext.startswith('.'):
            ext = '.' + ext
        normalized_exts.add(ext.lower())
    
    ext = Path(filename).suffix.lower()
    return ext in normalized_exts

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

# ----- Word -> PDF -----
def convert_word_to_pdf(file, form_data=None):
    """
    Convertit Word -> PDF (docx, doc, odt, rtf).
    - Conversion via LibreOffice (headless) avec vérification stabilité fichier
    - Fallback reportlab si LibreOffice absent
    - Fusion PDF optionnelle
    - Nettoyage sécurisé après envoi
    """
    import time

    files, error = normalize_files_input(file if isinstance(file, list) else [file])
    if error:
        return error

    if not files:
        return {"error": "Aucun fichier fourni"}

    allowed = {".docx", ".doc", ".odt", ".rtf"}
    form_data = form_data or {}
    merge_output = form_data.get("merge", True)

    # ✅ Sauvegarde des noms de fichiers avant toute opération
    original_filenames = [f.filename for f in files]

    temp_dir = create_temp_directory("word2pdf_")
    generated_pdfs = []

    try:
        libreoffice = shutil.which("libreoffice")
        if not libreoffice:
            current_app.logger.warning("LibreOffice non installé → fallback reportlab")

        for i, f in enumerate(files):
            original_name = original_filenames[i]

            if not validate_file_extension(original_name, allowed):
                current_app.logger.warning(f"Extension non autorisée ignorée : {original_name}")
                continue

            input_path = os.path.join(temp_dir, secure_filename(original_name))
            f.save(input_path)

            # ✅ Vérification que le fichier est bien sauvegardé
            if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
                current_app.logger.error(f"Fichier invalide ou vide : {original_name}")
                continue

            # ------------------------------------------------------------------
            # CONVERSION LIBREOFFICE
            # ------------------------------------------------------------------
            if libreoffice:
                cmd = [
                    libreoffice,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", temp_dir,
                    input_path
                ]

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=120,
                    check=False
                )

                # ✅ Vérification du code de retour
                if result.returncode != 0:
                    stderr_msg = result.stderr.decode("utf-8", errors="replace")
                    current_app.logger.error(
                        f"LibreOffice échec (code {result.returncode}) "
                        f"pour '{original_name}' : {stderr_msg}"
                    )
                else:
                    # ✅ Nom du PDF prévisible (pas de pdf_candidates[-1] aléatoire)
                    expected_pdf = os.path.join(
                        temp_dir,
                        Path(secure_filename(original_name)).stem + ".pdf"
                    )

                    # ✅ Attente que le fichier soit stable (écriture terminée)
                    pdf_ready = False
                    for _ in range(20):  # 20 × 100ms = 2s max
                        if os.path.exists(expected_pdf) and os.path.getsize(expected_pdf) > 0:
                            size_before = os.path.getsize(expected_pdf)
                            time.sleep(0.1)
                            size_after = os.path.getsize(expected_pdf)
                            if size_before == size_after:
                                pdf_ready = True
                                break
                        time.sleep(0.1)

                    if pdf_ready:
                        current_app.logger.info(f"LibreOffice OK : {expected_pdf}")
                        generated_pdfs.append(expected_pdf)
                        continue
                    else:
                        current_app.logger.warning(
                            f"PDF non stable après conversion LibreOffice : {expected_pdf}"
                        )

            # ------------------------------------------------------------------
            # FALLBACK REPORTLAB
            # ------------------------------------------------------------------
            current_app.logger.info(f"Fallback reportlab pour : {original_name}")

            if original_name.lower().endswith(".docx"):
                try:
                    doc = Document(input_path)
                    text = "\n\n".join(
                        p.text for p in doc.paragraphs if p.text.strip()
                    )
                    if not text.strip():
                        text = "[Document sans contenu textuel extractible]"
                except Exception as e:
                    current_app.logger.error(f"Erreur lecture docx '{original_name}': {e}")
                    text = "Contenu non extractible."
            else:
                text = f"Format '{Path(original_name).suffix}' non supporté par le fallback.\nVeuillez installer LibreOffice pour convertir ce type de fichier."

            output_pdf = os.path.join(
                temp_dir,
                f"{Path(secure_filename(original_name)).stem}_fallback.pdf"
            )

            try:
                c = canvas.Canvas(output_pdf, pagesize=A4)
                width, height = A4
                y = height - 50
                c.setFont("Helvetica", 11)

                for line in text.split("\n"):
                    # ✅ Découpage des lignes trop longues
                    while len(line) > 90:
                        c.drawString(50, y, line[:90])
                        line = line[90:]
                        y -= 15
                        if y < 50:
                            c.showPage()
                            c.setFont("Helvetica", 11)
                            y = height - 50

                    if y < 50:
                        c.showPage()
                        c.setFont("Helvetica", 11)
                        y = height - 50

                    c.drawString(50, y, line)
                    y -= 15

                c.save()

                # ✅ Vérification que le PDF fallback a bien été créé
                if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
                    generated_pdfs.append(output_pdf)
                else:
                    current_app.logger.error(f"PDF fallback vide : {output_pdf}")

            except Exception as e:
                current_app.logger.error(f"Erreur fallback reportlab '{original_name}': {e}")

        # ------------------------------------------------------------------
        # AUCUN PDF GÉNÉRÉ
        # ------------------------------------------------------------------
        if not generated_pdfs:
            cleanup_temp_directory(temp_dir)
            return {"error": "Aucune conversion n'a abouti. Vérifiez les fichiers fournis."}

        # ✅ Nettoyage APRÈS l'envoi Flask
        @after_this_request
        def cleanup(response):
            cleanup_temp_directory(temp_dir)
            return response

        # ------------------------------------------------------------------
        # FUSION PDF (multi-fichiers)
        # ------------------------------------------------------------------
        if merge_output and len(generated_pdfs) > 1:
            try:
                merger = PdfMerger()
                for pdf in generated_pdfs:
                    merger.append(pdf)
                merged_path = os.path.join(temp_dir, "merged_output.pdf")
                merger.write(merged_path)
                merger.close()

                return send_file(
                    merged_path,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name="converted_documents.pdf"
                )
            except Exception as e:
                current_app.logger.error(f"Erreur fusion PDF : {e}")
                # ✅ Fallback : on envoie le premier PDF si la fusion échoue
                return send_file(
                    generated_pdfs[0],
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"{Path(original_filenames[0]).stem}.pdf"
                )

        # ------------------------------------------------------------------
        # FICHIER UNIQUE
        # ------------------------------------------------------------------
        return send_file(
            generated_pdfs[0],
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{Path(original_filenames[0]).stem}.pdf"  # ✅ variable locale
        )

    except Exception as e:
        current_app.logger.error(f"Erreur Word->PDF : {str(e)}")
        current_app.logger.error(traceback.format_exc())
        cleanup_temp_directory(temp_dir)
        return generate_fallback_pdf("document", "Word")

# ----- Excel -> PDF -----
def convert_excel_to_pdf(file, form_data=None):
    """
    Conversion Excel -> PDF
    Priorité : LibreOffice (qualité parfaite)
    Fallback : Pandas + ReportLab
    """

    # Sécurité : accepter liste ou fichier
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]

    if not hasattr(file, "filename"):
        return {'error': 'Objet fichier invalide'}

    temp_dir = tempfile.mkdtemp()

    try:
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)

        # ============================
        # 1️⃣ Conversion LibreOffice
        # ============================
        libreoffice = shutil.which("libreoffice")

        if libreoffice:

            cmd = [
                libreoffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                temp_dir,
                input_path
            ]

            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120
            )

            pdf_files = [
                f for f in os.listdir(temp_dir)
                if f.lower().endswith(".pdf")
            ]

            if pdf_files:

                pdf_path = os.path.join(temp_dir, pdf_files[0])

                return send_file(
                    pdf_path,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}.pdf"
                )

        # ============================
        # 2️⃣ Fallback Pandas
        # ============================

        sheets = pd.read_excel(input_path, sheet_name=None)

        output = BytesIO()

        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4

        y = height - 50

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, f"Excel export : {file.filename}")
        y -= 40

        for sheet_name, df in sheets.items():

            if y < 100:
                c.showPage()
                y = height - 50

            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y, f"Sheet : {sheet_name}")
            y -= 25

            c.setFont("Helvetica", 9)

            for _, row in df.head(40).iterrows():

                if y < 50:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 9)

                row_text = " | ".join(
                    str(v)[:25] for v in row.values
                )[:140]

                c.drawString(60, y, row_text)

                y -= 14

            y -= 20

        c.save()

        output.seek(0)

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )

    except Exception as e:

        current_app.logger.error(f"Erreur Excel->PDF : {str(e)}")

        return generate_fallback_pdf(
            file.filename,
            "Excel"
        )

    finally:

        shutil.rmtree(temp_dir, ignore_errors=True)

# ----- PowerPoint -> PDF -----
def convert_powerpoint_to_pdf(file, form_data=None):
    """
    Conversion PowerPoint -> PDF
    Priorité : LibreOffice
    Fallback : python-pptx + ReportLab
    """

    # Normaliser l'entrée (file ou liste)
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]

    # Vérifier objet fichier
    if not hasattr(file, "filename") or not hasattr(file, "save"):
        return {'error': 'Objet fichier invalide'}

    # Vérifier extension
    allowed = (".pptx", ".ppt", ".odp")
    if not file.filename.lower().endswith(allowed):
        return {'error': 'Format PowerPoint non supporté'}

    temp_dir = tempfile.mkdtemp()

    try:
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)

        # =====================================================
        # 1️⃣ Conversion via LibreOffice
        # =====================================================
        libreoffice = shutil.which("libreoffice")

        if libreoffice:

            cmd = [
                libreoffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                temp_dir,
                input_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
                check=False
            )

            pdf_candidates = [
                f for f in os.listdir(temp_dir)
                if f.lower().endswith(".pdf")
            ]

            if result.returncode == 0 and pdf_candidates:

                output_path = os.path.join(temp_dir, pdf_candidates[0])

                return send_file(
                    output_path,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}.pdf"
                )

        # =====================================================
        # 2️⃣ Fallback python-pptx
        # =====================================================

        prs = Presentation(input_path)

        output = BytesIO()

        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4

        for i, slide in enumerate(prs.slides):

            y = height - 50

            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y, f"Diapositive {i+1}")
            y -= 30

            text_found = False

            for shape in slide.shapes:

                if hasattr(shape, "text") and shape.text.strip():

                    text_found = True
                    c.setFont("Helvetica", 10)

                    for line in shape.text.split("\n"):

                        if y < 50:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y = height - 50

                        c.drawString(50, y, line[:110])
                        y -= 14

            if not text_found:
                c.setFont("Helvetica", 10)
                c.drawString(50, y, "[Aucun texte détecté dans cette diapositive]")

            c.showPage()

        c.save()

        output.seek(0)

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )

    except Exception as e:

        current_app.logger.error(f"Erreur PowerPoint->PDF : {str(e)}")

        return generate_fallback_pdf(file.filename, "PowerPoint")

    finally:

        shutil.rmtree(temp_dir, ignore_errors=True)

# ----- Images -> PDF -----
def convert_images_to_pdf(files, form_data=None):
    """Conversion Images -> PDF (version PRO)"""
    # Normalisation
    files, error = normalize_files_input(files, max_files=20)
    if error:
        return error

    if not HAS_PILLOW or not HAS_REPORTLAB:
        return {"error": "Pillow ou reportlab non installé"}

    allowed_ext = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")
    form_data = form_data or {}
    page_size = form_data.get("pageSize", "A4")
    orientation = form_data.get("orientation", "portrait")
    quality = form_data.get("quality", "medium")

    pagesize = A4 if page_size == "A4" else letter
    if orientation == "landscape":
        pagesize = (pagesize[1], pagesize[0])
    width, height = pagesize

    quality_map = {"high": 95, "medium": 75, "low": 50}
    quality_val = quality_map.get(quality, 75)

    # Filtrer et trier les fichiers valides
    valid_files = []
    for f in files:
        if validate_file_extension(f.filename, allowed_ext):
            valid_files.append(f)
    
    if not valid_files:
        return {"error": "Aucune image valide"}

    # Tri alphabétique
    valid_files.sort(key=lambda x: x.filename.lower())

    output = BytesIO()
    c = canvas.Canvas(output, pagesize=pagesize)
    images_processed = 0

    for file in valid_files:
        try:
            # Opération sécurisée sur l'image
            img = safe_image_operation(Image.open, file.stream)
            if img is None:
                continue

            # Correction rotation EXIF
            try:
                exif = img._getexif()
                if exif:
                    orientation_key = 274
                    if orientation_key in exif:
                        orientation_val = exif[orientation_key]
                        if orientation_val == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation_val == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation_val == 8:
                            img = img.rotate(90, expand=True)
            except Exception:
                pass

            # Correction mode / transparence
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                mask = img.split()[-1] if img.mode in ("RGBA", "LA") else None
                background.paste(img, mask=mask)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Redimensionnement
            max_w = int(width * 0.9)
            max_h = int(height * 0.9)
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            new_w, new_h = img.size
            x = (width - new_w) / 2
            y = (height - new_h) / 2

            temp_img = BytesIO()
            img.save(temp_img, format="JPEG", quality=quality_val, optimize=True)
            temp_img.seek(0)

            c.drawImage(ImageReader(temp_img), x, y, width=new_w, height=new_h)
            c.showPage()
            images_processed += 1

        except Exception as e:
            logger.error(f"Erreur image {getattr(file, 'filename', 'inconnu')} : {e}")
            continue

    if images_processed == 0:
        return {"error": "Aucune image traitée avec succès"}

    c.save()
    output.seek(0)

    if not output.getvalue().startswith(b"%PDF"):
        return {"error": "PDF généré invalide"}

    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="images_converted.pdf"
    )

# ----- PDF -> WORD -----
def convert_pdf_to_word(file, form_data=None):
    """
    Convertit un PDF en document Word (.docx)
    Compatible avec pypdf + python-docx
    """

    # Normalisation
    file, error = normalize_file_input(file)
    if error:
        return error

    if not HAS_PYPDF or not HAS_DOCX:
        return {'error': 'pypdf ou python-docx non installé'}

    try:
        # Vérification extension PDF
        if not file.filename.lower().endswith(".pdf"):
            return {"error": "Le fichier fourni n’est pas un PDF"}

        # Lecture PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        if len(pdf_reader.pages) == 0:
            return {"error": "PDF vide ou invalide"}

        logger.info(f"📄 Conversion PDF->Word: {file.filename} ({len(pdf_reader.pages)} pages)")

        # Création document Word
        doc = Document()
        doc.add_heading(f'Extraction du PDF : {Path(file.filename).stem}', 0)
        doc.add_paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        doc.add_paragraph(f"Nombre de pages détectées : {len(pdf_reader.pages)}")
        doc.add_paragraph()

        pages_with_text = 0

        # ---- Extraction page par page ----
        for page_num, page in enumerate(pdf_reader.pages):
            if page_num > 0:
                doc.add_page_break()

            doc.add_heading(f'Page {page_num + 1}', level=1)

            try:
                extracted = page.extract_text() or ""
                extracted = extracted.replace("\x00", "").strip()

                if extracted:
                    pages_with_text += 1
                    doc.add_paragraph(extracted)
                else:
                    doc.add_paragraph("[⚠ Aucun texte détecté sur cette page]")

            except Exception as e_page:
                logger.warning(f"⚠ Impossible d’extraire texte page {page_num+1}: {e_page}")
                doc.add_paragraph("[Erreur d’extraction de cette page]")

        # ---- Si aucune page ne contient du texte ----
        if pages_with_text == 0:
            doc.add_page_break()
            doc.add_heading("Analyse du document", level=1)
            doc.add_paragraph(
                "Ce PDF semble être un document scanné ou une image.\n"
                "Aucun texte n'a pu être extrait automatiquement."
            )

        # ---- Export mémoire ----
        output = BytesIO()
        doc.save(output)
        output.seek(0)

        logger.info(f"✅ Conversion PDF->Word terminée pour {file.filename}")

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.docx"
        )

    except Exception as e:
        logger.error(f"❌ Erreur PDF->Word: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur lors de la conversion: {str(e)}"}

# ----- PDF -> DOC -----
def convert_pdf_to_doc(file, form_data=None):
    """
    Convertit un PDF en document Word (.doc)
    En réutilisant la conversion PDF->DOCX puis renommage pour compatibilité.
    """

    # Normalisation
    file, error = normalize_file_input(file)
    if error:
        return error

    try:
        # Réutilisation de convert_pdf_to_word
        response = convert_pdf_to_word(file, form_data)

        # Si la conversion retourne une erreur, on la transmet
        if isinstance(response, dict) and "error" in response:
            return response

        # Vérification que c'est bien un objet Flask response
        if not hasattr(response, "headers"):
            return {"error": "Réponse inattendue du convertisseur PDF->DOCX"}

        # Renommer le fichier de sortie .docx → .doc
        content_disp = response.headers.get("Content-Disposition", "")
        if ".docx" in content_disp:
            content_disp = content_disp.replace(".docx", ".doc")
            response.headers["Content-Disposition"] = content_disp

        return response

    except Exception as e:
        logger.error(f"❌ Erreur PDF->DOC: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur lors de la conversion: {str(e)}"}

# ----- PDF -> EXCEL -----
def convert_pdf_to_excel(file_storage, form_data=None):
    if isinstance(file_storage, list):
        if not file_storage:
            return {'error': 'Aucun fichier fourni'}
        file_storage = file_storage[0]

    if not hasattr(file_storage, "filename") or not hasattr(file_storage, "save"):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PDF2IMAGE:
        return {'error': 'pdf2image non installé (obligatoire)'}
    if not HAS_TESSERACT:
        return {'error': 'Tesseract OCR non installé'}
    if not HAS_PANDAS:
        return {'error': 'pandas non installé'}

    # ✅ Sauvegarde du nom avant toute opération async
    original_filename = file_storage.filename

    temp_dir = None
    try:
        temp_dir = create_temp_directory("pdf2excel_")

        pdf_path = os.path.join(temp_dir, secure_filename(original_filename))
        file_storage.save(pdf_path)

        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            return {'error': 'PDF non valide ou vide'}

        language = (form_data.get('language') if form_data else 'fra') or 'fra'
        ocr_enabled = str(form_data.get('ocr_enabled', 'true') if form_data else 'true').lower() == 'true'

        lang_map = {
            'fra': 'fra', 'en': 'eng', 'es': 'spa', 'de': 'deu', 'it': 'ita',
            'pt': 'por', 'ru': 'rus', 'ar': 'ara', 'zh': 'chi_sim',
            'ja': 'jpn', 'nl': 'nld'
        }
        lang_list = language.split('+')
        ocr_lang = "+".join([lang_map.get(l, "fra") for l in lang_list])

        # ✅ Vérification que les langues Tesseract sont disponibles
        try:
            available_langs = pytesseract.get_languages()
            for lang in ocr_lang.split('+'):
                if lang not in available_langs:
                    logger.warning(f"Langue Tesseract '{lang}' non installée, fallback sur 'fra'")
                    ocr_lang = 'fra'
                    break
        except Exception:
            logger.warning("Impossible de vérifier les langues Tesseract disponibles")

        logger.info(f"OCR => {ocr_lang}")

        try:
            images = convert_from_path(pdf_path, dpi=200)
        except Exception as e:
            logger.error(f"Erreur GhostScript : {e}")
            return {'error': 'Impossible de convertir le PDF en image. GhostScript doit être installé.'}

        if not images:
            return {'error': 'PDF sans pages utilisables'}

        logger.info(f"{len(images)} pages détectées")

        all_rows = []
        pages_with_text = 0

        for i, img in enumerate(images):
            logger.info(f"OCR page {i + 1}/{len(images)}")
            try:
                page_lines = []

                if ocr_enabled:
                    data = pytesseract.image_to_data(
                        img, lang=ocr_lang, output_type=Output.DICT,
                        config="--oem 3 --psm 6"
                    )

                    rows = []
                    current = []
                    last_top = None
                    row_threshold = 18

                    for idx, txt in enumerate(data['text']):
                        txt = txt.strip()
                        if not txt:
                            continue

                        # ✅ except ValueError au lieu de except nu
                        try:
                            conf = int(data['conf'][idx])
                        except (ValueError, TypeError):
                            conf = -1

                        if conf < 30:
                            continue

                        top = data['top'][idx]
                        left = data['left'][idx]

                        if last_top is None or abs(top - last_top) > row_threshold:
                            if current:
                                rows.append(current)
                            current = []
                            last_top = top

                        current.append((left, txt))

                    if current:
                        rows.append(current)

                    page_lines = [
                        " ".join([word for _, word in sorted(row)])
                        for row in rows if row
                    ]
                else:
                    txt = pytesseract.image_to_string(img, lang=ocr_lang)
                    page_lines = [l.strip() for l in txt.split("\n") if l.strip()]

                if page_lines:
                    pages_with_text += 1
                    for ln_idx, line in enumerate(page_lines, 1):
                        all_rows.append({"Page": i + 1, "Ligne": ln_idx, "Contenu": line})
                else:
                    all_rows.append({"Page": i + 1, "Ligne": 1, "Contenu": "[Aucun texte détecté]"})

            except Exception as e_ocr:
                logger.error(f"Erreur OCR page {i+1} : {e_ocr}")
                all_rows.append({"Page": i + 1, "Ligne": 1, "Contenu": "[Erreur OCR]"})

        df = pd.DataFrame(all_rows)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Extraction")

            sheet = writer.sheets["Extraction"]
            for col in sheet.columns:
                max_len = max(len(str(cell.value) or "") for cell in col)
                sheet.column_dimensions[col[0].column_letter].width = min(max_len + 2, 60)

            summary = pd.DataFrame({
                "Propriété": [
                    "Nom du fichier", "Pages totales", "Pages avec contenu",
                    "OCR activé", "Langues OCR", "Date de conversion"
                ],
                "Valeur": [
                    original_filename,  # ✅ variable locale, pas file_storage.filename
                    len(images), pages_with_text,
                    "Oui" if ocr_enabled else "Non",
                    ocr_lang,
                    datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                ]
            })
            summary.to_excel(writer, sheet_name="Résumé", index=False)
            sheet2 = writer.sheets["Résumé"]
            sheet2.column_dimensions["A"].width = 25
            sheet2.column_dimensions["B"].width = 40

        output.seek(0)

        # ✅ Nettoyage sécurisé — BytesIO est en mémoire donc pas de risque,
        #    mais on nettoie proprement après la réponse quand même
        @after_this_request
        def cleanup(response):
            cleanup_temp_directory(temp_dir)
            return response

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"{Path(original_filename).stem}.xlsx"
        )

    except Exception as e:
        logger.error(f"Erreur PDF->Excel : {e}")
        logger.error(traceback.format_exc())
        cleanup_temp_directory(temp_dir)  # ✅ nettoyage immédiat sur erreur
        return {"error": f"Erreur lors de la conversion : {e}"}

# ----- PDF -> PPT -----
def convert_pdf_to_ppt(file_storage, form_data=None):
    """Conversion PDF → PowerPoint (.pptx) robuste, fiable et stable."""

    if isinstance(file_storage, list):
        if not file_storage:
            return {'error': 'Aucun fichier fourni'}
        file_storage = file_storage[0]

    if not hasattr(file_storage, "filename") or not hasattr(file_storage, "save"):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PDF2IMAGE or not HAS_PILLOW or not HAS_PPTX:
        return {'error': 'Dépendances manquantes pour PDF→PowerPoint'}

    # ✅ Sauvegarde du nom avant toute opération
    original_filename = file_storage.filename

    temp_dir = None
    try:
        temp_dir = create_temp_directory("pdf2ppt_")

        input_pdf = os.path.join(temp_dir, secure_filename(original_filename))
        file_storage.save(input_pdf)

        if not os.path.exists(input_pdf) or os.path.getsize(input_pdf) == 0:
            return {"error": "PDF non valide ou vide"}

        slide_size_opt = form_data.get("slide_size", "widescreen") if form_data else "widescreen"

        if slide_size_opt == "standard":
            slide_width, slide_height = 9144000, 6858000
        else:
            slide_width, slide_height = 12192000, 6858000

        try:
            images = convert_from_path(input_pdf, dpi=220)
        except Exception as e:
            logger.error(f"Erreur conversion PDF→images : {e}")
            return {"error": "Impossible de convertir le PDF en images. Vérifiez Ghostscript."}

        if not images:
            return {"error": "Aucune page détectée dans le PDF."}

        prs = Presentation()
        prs.slide_width = slide_width
        prs.slide_height = slide_height

        for i, img in enumerate(images, start=1):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            img = img.convert("RGB")

            img_path = os.path.join(temp_dir, f"page_{i}.jpg")
            img.save(img_path, "JPEG", quality=95)

            # ✅ Vérification que l'image a bien été écrite sur disque
            if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
                logger.error(f"Image page {i} non générée, slide ignoré")
                continue

            sw, sh = slide_width, slide_height
            iw, ih = img.size
            scale = min(sw / iw, sh / ih) * 0.96
            new_w = int(iw * scale)
            new_h = int(ih * scale)
            left = int((sw - new_w) / 2)
            top = int((sh - new_h) / 2)

            slide.shapes.add_picture(img_path, left, top, width=new_w, height=new_h)

            tx = slide.shapes.add_textbox(
                Inches(0.25), sh - Inches(0.5), Inches(2), Inches(0.4)
            )
            tf = tx.text_frame
            tf.text = f"Page {i}"
            tf.paragraphs[0].font.size = Pt(10)
            tf.paragraphs[0].font.color.rgb = RGBColor(80, 80, 80)

        # ✅ prs.save() AVANT tout nettoyage — les images doivent exister
        output = BytesIO()
        prs.save(output)
        output.seek(0)

        # ✅ Nettoyage après l'envoi
        @after_this_request
        def cleanup(response):
            cleanup_temp_directory(temp_dir)
            return response

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True,
            download_name=f"{Path(original_filename).stem}.pptx"  # ✅ variable locale
        )

    except Exception as e:
        logger.error(f"Erreur PDF→PPT : {e}")
        logger.error(traceback.format_exc())
        cleanup_temp_directory(temp_dir)  # ✅ nettoyage immédiat sur erreur
        return {"error": f"Erreur lors de la conversion : {e}"}

# ----- PDF -> IMAGE -----
def _enhance_scan(img: Image.Image, do_binarize: bool) -> Image.Image:
    """
    Amélioration visuelle légère pour scans :
    - autocontraste
    - filtre médian
    - binarisation optionnelle (Otsu si NumPy disponible)
    """
    try:
        out = img.convert("RGB")
        out = ImageOps.autocontrast(out)
        out = out.filter(ImageFilter.MedianFilter(size=3))

        if do_binarize:
            gray = out.convert("L")
            if HAS_NUMPY:
                arr = np.array(gray, dtype=np.uint8)
                # Otsu simple
                hist, _ = np.histogram(arr, bins=256, range=(0, 255))
                total = arr.size
                sum_total = np.dot(np.arange(256), hist)
                sumB = 0.0
                wB = 0
                max_var = 0.0
                threshold = 127
                for t in range(256):
                    wB += hist[t]
                    if wB == 0:
                        continue
                    wF = total - wB
                    if wF == 0:
                        break
                    sumB += t * hist[t]
                    mB = sumB / wB
                    mF = (sum_total - sumB) / wF
                    var_between = wB * wF * (mB - mF) ** 2
                    if var_between > max_var:
                        max_var = var_between
                        threshold = t
                bw = gray.point(lambda x: 255 if x > threshold else 0, mode='1')
                out = bw.convert("L").convert("RGB")
            else:
                # Seuil fixe si NumPy non disponible
                bw = gray.point(lambda x: 255 if x > 160 else 0, mode='1')
                out = bw.convert("L").convert("RGB")

        return out

    except Exception as e:
        logger.debug(f"_enhance_scan fallback: {e}")
        return img.convert("RGB")


def _is_blank(img: Image.Image, white_ratio_threshold: float = 0.99) -> bool:
    """
    Détecte si une page est quasi blanche.
    - white_ratio_threshold : fraction de pixels très clairs pour considérer l'image comme blanche
    """
    try:
        gray = img.convert("L")

        if HAS_NUMPY:
            arr = np.array(gray, dtype=np.uint8)
            white_pixels = (arr > 245).sum()
            ratio = white_pixels / arr.size
        else:
            data = list(gray.getdata())
            white_pixels = sum(1 for v in data if v > 245)
            ratio = white_pixels / len(data)

        return ratio >= white_ratio_threshold

    except Exception as e:
        logger.debug(f"_is_blank detection failed: {e}")
        return False


def _annotate_ocr_boxes(img: Image.Image, ocr_lang: str) -> Image.Image:
    """Ajoute des boîtes et libellés mots grâce à Tesseract (si dispo)."""
    if not HAS_TESSERACT:
        return img
    try:
        # Tesseract attend du RGB
        work = img.convert("RGB")
        data = pytesseract.image_to_data(work, lang=ocr_lang, output_type=Output.DICT, config="--oem 3 --psm 6")
        draw = ImageDraw.Draw(work)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        for i, text in enumerate(data["text"]):
            txt = (text or "").strip()
            conf_raw = data["conf"][i]
            try:
                conf = int(conf_raw)
            except Exception:
                conf = -1
            if not txt or conf < 40:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            draw.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=2)
            if font:
                draw.text((x, max(0, y - 10)), txt[:20], fill=(255, 0, 0), font=font)
        return work
    except Exception as e:
        logger.debug(f"OCR annotate failed: {e}")
        return img


def _save_image_as_pdf(img: Image.Image, buffer: BytesIO):
    """Sauve une image en PDF dans un buffer. Utilise reportlab si dispo sinon PIL."""
    if HAS_REPORTLAB:
        # Centrage sur A4 avec marge
        from reportlab.lib.units import inch
        c = canvas.Canvas(buffer, pagesize=A4)
        pw, ph = A4
        # Convertir image en JPEG temp (RGB)
        tmp = BytesIO()
        rgb = img.convert("RGB")
        rgb.save(tmp, format="JPEG", quality=90)
        tmp.seek(0)
        # Taille cible avec marge 0.5"
        max_w, max_h = pw - inch, ph - inch
        iw, ih = rgb.size
        # px -> points (approx): 72 dpi baseline si inconnu
        # On normalise par un facteur en points relatif: remplir en gardant le ratio
        scale = min(max_w / iw, max_h / ih)
        w, h = iw * scale, ih * scale
        x = (pw - w) / 2
        y = (ph - h) / 2
        c.drawImage(tmp, x, y, width=w, height=h)
        c.showPage()
        c.save()
    else:
        # PIL peut sauver directement en PDF (une page)
        rgb = img.convert("RGB")
        rgb.save(buffer, format="PDF")

# ----- PDF -> Image -----
def convert_pdf_to_images(file, form_data=None):
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]

    # ✅ Ajout vérification de save()
    if not hasattr(file, "filename") or not hasattr(file, "save"):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PDF2IMAGE:
        return {'error': "La dépendance 'pdf2image' est requise."}

    # ✅ Sauvegarde du nom avant toute opération
    original_filename = file.filename

    temp_dir = None
    try:
        temp_dir = create_temp_directory("pdf2images_")
        pdf_path = os.path.join(temp_dir, secure_filename(original_filename))
        file.save(pdf_path)

        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            return {"error": "PDF vide ou invalide."}

        image_format = (form_data.get('format', 'png') if form_data else 'png').lower()
        quality_opt = form_data.get('quality', 'medium') if form_data else 'medium'

        # ✅ DPI borné pour éviter saturation RAM
        try:
            dpi = max(72, min(int(form_data.get('dpi', 180) if form_data else 180), 600))
        except (ValueError, TypeError):
            dpi = 180

        enhance = str(form_data.get('enhance', 'false')).lower() == 'true' if form_data else False
        do_binarize = str(form_data.get('binarize', 'false')).lower() == 'true' if form_data else False
        remove_blanks = str(form_data.get('remove_blanks', 'false')).lower() == 'true' if form_data else False

        # ✅ blank_threshold borné entre 0 et 1
        try:
            blank_threshold = max(0.0, min(float(form_data.get('blank_threshold', 0.99) if form_data else 0.99), 1.0))
        except (ValueError, TypeError):
            blank_threshold = 0.99

        contact_sheet = str(form_data.get('contact_sheet', 'false')).lower() == 'true' if form_data else False

        # ✅ contact_cols / contact_rows bornés
        try:
            contact_cols = max(1, min(int(form_data.get('contact_cols', 4) if form_data else 4), 10))
            contact_rows = max(1, min(int(form_data.get('contact_rows', 5) if form_data else 5), 10))
        except (ValueError, TypeError):
            contact_cols, contact_rows = 4, 5

        export_per_pdf = str(form_data.get('export_per_page_pdf', 'false')).lower() == 'true' if form_data else False
        annotate_ocr = str(form_data.get('annotate_ocr', 'false')).lower() == 'true' if form_data else False
        language = (form_data.get('language', 'fra') if form_data else 'fra')

        lang_map = {
            'fra': 'fra', 'en': 'eng', 'es': 'spa', 'de': 'deu', 'it': 'ita',
            'pt': 'por', 'ru': 'rus', 'ar': 'ara', 'zh': 'chi_sim', 'ja': 'jpn', 'nl': 'nld'
        }
        ocr_lang = "+".join([
            lang_map.get(l.strip(), 'fra')
            for l in (language.split('+') if '+' in language else [language])
        ])

        if image_format not in ['png', 'jpg', 'jpeg']:
            image_format = 'png'
        if image_format == 'jpeg':
            image_format = 'jpg'
        quality_val = 95 if quality_opt == 'high' else 75 if quality_opt == 'medium' else 50

        try:
            pages = convert_from_path(pdf_path, dpi=dpi)
        except Exception as e:
            logger.error(f"Erreur conversion PDF→images : {e}")
            return {"error": "Impossible de convertir le PDF. Vérifiez Ghostscript."}

        if not pages:
            return {"error": "Aucune page détectée dans le PDF."}

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            kept_images, kept_indices = [], []

            for idx, img in enumerate(pages, start=1):
                work = img.convert("RGB")
                if enhance or do_binarize:
                    work = _enhance_scan(work, do_binarize=do_binarize)
                if annotate_ocr and HAS_TESSERACT:
                    work = _annotate_ocr_boxes(work, ocr_lang=ocr_lang)
                if remove_blanks and _is_blank(work, white_ratio_threshold=blank_threshold):
                    continue

                img_buf = BytesIO()
                if image_format == 'png':
                    work.save(img_buf, format='PNG', optimize=True)
                else:
                    work.save(img_buf, format='JPEG', quality=quality_val, optimize=True)
                img_buf.seek(0)
                zipf.writestr(f"images/page_{idx}.{image_format}", img_buf.getvalue())
                kept_images.append(work)
                kept_indices.append(idx)

                if export_per_pdf:
                    pdf_buf = BytesIO()
                    _save_image_as_pdf(work, pdf_buf)
                    pdf_buf.seek(0)
                    zipf.writestr(f"per_page_pdf/page_{idx}.pdf", pdf_buf.getvalue())

            if contact_sheet and kept_images:
                cols = contact_cols
                rows = contact_rows
                thumb_w, thumb_h, margin = 400, 400, 20
                sheet_w = cols * thumb_w + (cols + 1) * margin
                sheet_h = rows * thumb_h + (rows + 1) * margin
                pages_count = len(kept_images)
                sheets_needed = (pages_count + (cols * rows) - 1) // (cols * rows)

                for s in range(sheets_needed):
                    start = s * (cols * rows)
                    end = min(start + cols * rows, pages_count)
                    canvas_img = Image.new("RGB", (sheet_w, sheet_h), (240, 240, 240))
                    draw = ImageDraw.Draw(canvas_img)
                    try:
                        font = ImageFont.load_default()
                    except Exception:
                        font = None
                    for k, page_img in enumerate(kept_images[start:end]):
                        r, c = divmod(k, cols)
                        x0 = margin + c * (thumb_w + margin)
                        y0 = margin + r * (thumb_h + margin)
                        thumb = page_img.copy()
                        thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                        tx = x0 + (thumb_w - thumb.width) // 2
                        ty = y0 + (thumb_h - thumb.height) // 2
                        canvas_img.paste(thumb, (tx, ty))
                        if font:
                            draw.text((x0 + 5, y0 + 5), f"Page {kept_indices[start + k]}", fill=(0, 0, 0), font=font)
                    cs_buf = BytesIO()
                    canvas_img.save(cs_buf, format='PNG', optimize=True)
                    cs_buf.seek(0)
                    zipf.writestr(f"contact_sheets/contact_{s + 1}.png", cs_buf.getvalue())

        zip_buffer.seek(0)

        # ✅ Nettoyage après l'envoi
        @after_this_request
        def cleanup(response):
            cleanup_temp_directory(temp_dir)
            return response

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{Path(original_filename).stem}_images.zip"  # ✅ variable locale
        )

    except Exception as e:
        logger.error(f"Erreur PDF->Images : {e}")
        logger.error(traceback.format_exc())
        cleanup_temp_directory(temp_dir)  # ✅ nettoyage immédiat sur erreur
        return {'error': f'Erreur lors de la conversion: {e}'}

# ----- PDF -> PDFA -----
def convert_pdf_to_pdfa(file, form_data=None):
    """
    Convertit réellement un PDF en PDF/A via Ghostscript.
    Compatible : PDF/A-1b, 2b, 3b, 2u, 3u.
    100% conforme aux normes ISO 19005.
    """

    # Sécurité : accepter liste ou fichier
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]
    
    if not hasattr(file, "filename"):
        return {'error': 'Objet fichier invalide'}

    try:
        temp_dir = tempfile.mkdtemp()
        
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)

        # Extraire version PDF/A demandée
        version = (form_data.get('version', '2b') if form_data else '2b').lower()

        # Maps réels Ghostscript
        version_map = {
            "1b": "1",
            "1a": "1",
            "2b": "2",
            "2u": "2",
            "2a": "2",
            "3b": "3",
            "3u": "3",
            "3a": "3"
        }

        conformance_map = {
            "1b": "B",
            "1a": "A",
            "2b": "B",
            "2u": "U",
            "2a": "A",
            "3b": "B",
            "3u": "U",
            "3a": "A"
        }

        pdfa_level = version_map.get(version, "2")
        pdfa_conformance = conformance_map.get(version, "B")  # Valeur par défaut : "B"

        output_path = os.path.join(
            temp_dir,
            f"{Path(file.filename).stem}_pdfa.pdf"
        )

        ghostscript_path = shutil.which("gs") or shutil.which("gswin64c") or shutil.which("gswin32c")
        if not ghostscript_path:
            return {"error": "Ghostscript n'est pas installé sur le serveur."}

        # Commande Ghostscript PDF/A ISO
        cmd = [
            ghostscript_path,
            "-dPDFA",
            f"-dPDFACompatibilityPolicy=1",
            f"-sPDFACompatibilityPolicy=1",
            f"-sProcessColorModel=DeviceRGB",
            f"-sDEVICE=pdfwrite",
            f"-dPDFA=1",
            f"-dBATCH",
            f"-dNOPAUSE",
            f"-dUseCIEColor",
            f"-dEmbedAllFonts=true",
            f"-dSubsetFonts=true",
            f"-sColorConversionStrategy=RGB",
            f"-sOutputFile={output_path}",
            input_path
        ]

        # Adapter selon version PDF/A (1, 2 ou 3)
        cmd[1] = f"-dPDFA={pdfa_level}"
        cmd.insert(2, f"-dPDFACompatibilityPolicy=1")

        # Exécuter Ghostscript
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if proc.returncode != 0:
            logger.error(proc.stderr)
            return {"error": f"Ghostscript a échoué : {proc.stderr}"}

        # Retourner le vrai PDF/A généré
        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_pdfa.pdf"
        )

    except Exception as e:
        logger.error(f"Erreur PDF->PDF/A : {e}")
        return {"error": f"Erreur conversion PDF/A : {e}"}

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

# ----- PDF -> HTML -----
def convert_pdf_to_html(file, form_data=None):
    if isinstance(file, list):
        if len(file) == 0:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]

    if not hasattr(file, 'filename') or not hasattr(file, 'save'):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PYPDF:
        return {"error": "pypdf n'est pas installé"}

    # ✅ Sauvegarde du nom avant toute opération
    original_filename = file.filename
    original_stem = Path(original_filename).stem
    original_name = Path(original_filename).name

    ocr_enabled = False
    include_images = False
    image_format = "png"
    dpi = 150
    encoding = "utf-8"

    if form_data:
        # ✅ Encoding validé pour éviter LookupError
        raw_encoding = form_data.get("encoding", "utf-8")
        try:
            "".encode(raw_encoding)
            encoding = raw_encoding
        except LookupError:
            logger.warning(f"Encoding inconnu '{raw_encoding}', fallback utf-8")
            encoding = "utf-8"

        ocr_enabled = str(form_data.get("ocr", "false")).lower() == "true"
        include_images = str(form_data.get("include_images", "false")).lower() == "true"
        image_format = form_data.get("image_format", "png").lower()

        # ✅ DPI borné
        try:
            dpi = max(72, min(int(form_data.get("dpi", "150")), 600))
        except (ValueError, TypeError):
            dpi = 150

    if image_format == "jpeg":
        image_format = "jpg"
    if image_format not in ("png", "jpg"):
        image_format = "png"

    temp_dir = None
    # ✅ zip_file initialisé à None pour le finally
    zip_file = None
    zip_buffer = None

    try:
        temp_dir = create_temp_directory("pdf2html_")

        pdf_path = os.path.join(temp_dir, secure_filename(original_filename))
        file.save(pdf_path)

        pdf_reader = pypdf.PdfReader(pdf_path)

        if len(pdf_reader.pages) == 0:
            return {"error": "PDF vide ou invalide"}

        # ✅ original_filename utilisé partout, jamais file.filename
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="{encoding}">
<title>PDF vers HTML - {original_stem}</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
    .page {{ margin-bottom: 60px; border-bottom: 1px solid #ddd; padding-bottom: 40px; }}
    h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
    .img-page {{ margin-top: 20px; max-width: 100%; border: 1px solid #ccc; }}
    .ocr-note {{ color: #b00; font-size: 12px; }}
</style>
</head>
<body>
<h1>Extraction du PDF : {original_name}</h1>
<p><em>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</em></p>
<hr>
"""

        if ocr_enabled and not HAS_TESSERACT:
            return {"error": "OCR demandé mais Tesseract n'est pas installé"}

        pages_img = []
        if include_images or ocr_enabled:
            try:
                from pdf2image import convert_from_path
                pages_img = convert_from_path(pdf_path, dpi=dpi)
            except Exception as e:
                return {"error": f"Impossible de convertir le PDF en images : {e}"}

        if include_images:
            zip_buffer = BytesIO()
            zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

        for idx, page in enumerate(pdf_reader.pages, start=1):
            html += f'<div class="page">\n<h2>Page {idx}</h2>\n'

            text = page.extract_text()

            if not text or not text.strip():
                if ocr_enabled:
                    # ✅ Vérification bounds avant accès pages_img
                    if idx - 1 < len(pages_img):
                        text = pytesseract.image_to_string(
                            pages_img[idx - 1],
                            lang="fra+eng"
                        )
                        html += '<p class="ocr-note">[Texte extrait par OCR]</p>\n'
                    else:
                        text = "[Page image non disponible pour OCR]"
                else:
                    text = "[Aucun texte détecté]"

            safe_text = (
                text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
            )

            for p in safe_text.split("\n\n"):
                if p.strip():
                    html += f"<p>{p.replace(chr(10), '<br>')}</p>\n"

            if include_images and idx - 1 < len(pages_img):  # ✅ bounds check
                img = pages_img[idx - 1]
                img_buffer = BytesIO()

                if image_format == "png":
                    img.save(img_buffer, "PNG")
                else:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(img_buffer, "JPEG", quality=90)

                img_buffer.seek(0)
                img_name = f"page_{idx}.{image_format}"
                zip_file.writestr(img_name, img_buffer.getvalue())
                html += f'<img class="img-page" src="{img_name}" alt="Page {idx}"><br>\n'

            html += "</div>\n"

        html += "</body></html>"

        if include_images:
            zip_file.writestr("index.html", html.encode(encoding))
            zip_file.close()
            zip_file = None  # ✅ Marqué comme fermé
            zip_buffer.seek(0)

            @after_this_request
            def cleanup(response):
                cleanup_temp_directory(temp_dir)
                return response

            return send_file(
                zip_buffer,
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"{original_stem}_html.zip"  # ✅ variable locale
            )

        output = BytesIO()
        output.write(html.encode(encoding))
        output.seek(0)

        @after_this_request
        def cleanup(response):
            cleanup_temp_directory(temp_dir)
            return response

        return send_file(
            output,
            mimetype="text/html",
            as_attachment=True,
            download_name=f"{original_stem}.html"  # ✅ variable locale
        )

    except Exception as e:
        logger.error(f"Erreur PDF->HTML : {e}")
        logger.error(traceback.format_exc())
        # ✅ Fermeture du ZIP si exception pendant son écriture
        if zip_file is not None:
            try:
                zip_file.close()
            except Exception:
                pass
        cleanup_temp_directory(temp_dir)
        return {"error": f"Erreur lors de la conversion : {e}"}

# ----- PDF -> TXT -----
def convert_pdf_to_txt(file, form_data=None):
    """Conversion PDF -> TXT robuste, avec OCR fallback optionnel."""
    # Normalisation
    file, error = normalize_file_input(file)
    if error:
        return error

    if not HAS_PYPDF:
        return {"error": "pypdf non installé"}

    try:
        # Options utilisateur
        encoding = (form_data.get("encoding", "utf-8") if form_data else "utf-8")
        add_markers = str(form_data.get("addPageMarkers", "true")).lower() == "true" if form_data else True
        ocr_enabled = str(form_data.get("ocr", "false")).lower() == "true" if form_data else False
        language = (form_data.get("language", "fra") if form_data else "fra")

        # Mapping OCR complet
        ocr_lang = build_ocr_lang_string(language)

        logger.info(f"PDF->TXT : encoding={encoding}, markers={add_markers}, OCR={ocr_enabled}, languages={ocr_lang}")

        # Lecture PDF
        pdf_reader = pypdf.PdfReader(file.stream)
        num_pages = len(pdf_reader.pages)

        if num_pages == 0:
            return {"error": "PDF vide ou invalide"}

        # OCR nécessite pdf2image + Tesseract
        temp_dir = None
        pages_img = []
        if ocr_enabled:
            if not HAS_TESSERACT:
                return {"error": "OCR activé mais Tesseract n'est pas installé"}
            if not HAS_PDF2IMAGE:
                return {"error": "OCR activé mais pdf2image n'est pas installé"}

            temp_dir = create_temp_directory("pdf2txt_")
            pdf_temp = os.path.join(temp_dir, secure_filename(file.filename))
            
            # Sauvegarder le fichier pour pdf2image
            file.stream.seek(0)
            with open(pdf_temp, 'wb') as f:
                f.write(file.read())

            try:
                pages_img = convert_from_path(pdf_temp, dpi=200)
            except Exception as e:
                cleanup_temp_directory(temp_dir)
                return {"error": f"Impossible de rasteriser le PDF pour OCR : {e}"}

        # Extraction texte
        full_text = []

        if add_markers:
            full_text.append("=" * 80)
            full_text.append(f"EXTRACTION DU PDF : {Path(file.filename).name}")
            full_text.append(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            full_text.append(f"Pages : {num_pages}")
            full_text.append("=" * 80 + "\n")

        for idx, page in enumerate(pdf_reader.pages, start=1):

            if add_markers:
                full_text.append(f"\n--- Page {idx} ---\n")

            # Extraction native
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""

            txt = txt.replace("\x00", "").strip()

            # Si pas de texte → Fallback OCR
            if ocr_enabled and (not txt or not txt.strip()) and pages_img and idx-1 < len(pages_img):
                ocr_text = safe_ocr_call(
                    pytesseract.image_to_string, 
                    pages_img[idx-1], 
                    lang=ocr_lang
                )
                if ocr_text:
                    txt = ocr_text.strip()
                    full_text.append("[Texte extrait via OCR]\n")

            # Si encore vide
            if not txt:
                txt = "[Aucun texte trouvé sur cette page]"

            full_text.append(txt)
            full_text.append("")

        if add_markers:
            full_text.append("=" * 80)
            full_text.append(f"Fin du document - {num_pages} pages")
            full_text.append("=" * 80)

        final_txt = "\n".join(full_text)

        # Export fichier
        output = BytesIO()
        output.write(final_txt.encode(encoding, errors="replace"))
        output.seek(0)

        # Nettoyage
        if temp_dir:
            cleanup_temp_directory(temp_dir)

        return send_file(
            output,
            mimetype="text/plain",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.txt"
        )

    except Exception as e:
        logger.error(f"Erreur PDF->TXT : {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur lors de la conversion : {e}"}

# ----- HTML -> PDF -----
def convert_html_to_pdf(file, form_data=None):
    """
    Convertit du HTML en PDF avec priorité à Chromium (Playwright) pour un rendu pixel-perfect.
    Fallback: WeasyPrint puis PDFKit si Chromium indisponible.
    
    Options `form_data` (toutes facultatives) :
      - engine: "chromium" | "weasyprint" | "pdfkit" | "auto" (défaut: "auto")
      - pageSize: "A4"|"Letter"|... (défaut "A4") ou width/height explicites ("210mm","297mm")
      - orientation: "portrait"|"landscape" (défaut "portrait")
      - margin: "20mm" (appliqué aux 4 bords) OU marginTop/Right/Bottom/Left
      - scale: "1" (float string) (0.1 à 2)
      - printBackground: "true"|"false" (défaut "true")
      - headerHtml / footerHtml: HTML (peut contenir <span class="pageNumber"></span> et <span class="totalPages"></span>)
      - waitUntil: "load"|"domcontentloaded"|"networkidle" (défaut "networkidle")
      - base_url: base pour les ressources relatives (ex: "file:///.../assets/" ou "https://...")
      - css_url: URL CSS (WeasyPrint uniquement)
      - encoding: "utf-8" (défaut)
    """
    # Protection contre les listes
    if isinstance(file_input, list):
        if len(file_input) == 0:
            return {'error': 'Aucun fichier fourni'}
        file = file_input[0]
    else:
        file = file_input
    
    # Vérifier que c'est bien un objet fichier
    if not hasattr(file, 'filename') or not hasattr(file, 'save'):
        return {'error': 'Objet fichier invalide'}

    # ==== Détections des moteurs disponibles ====
    has_chromium = False
    has_weasy = False
    has_pdfkit = False

    # Flags que vous avez peut-être déjà dans votre projet :
    try:
        from playwright.sync_api import sync_playwright
        has_chromium = True
    except Exception:
        has_chromium = False

    if 'HAS_WEASYPRINT' in globals() and HAS_WEASYPRINT:
        has_weasy = True

    if 'HAS_PDFKIT' in globals() and HAS_PDFKIT:
        has_pdfkit = True

    if not (has_chromium or has_weasy or has_pdfkit):
        return {'error': "Aucun moteur HTML->PDF disponible (Playwright/Chromium, WeasyPrint, ou PDFKit requis)."}

    temp_dir = None
    try:
        temp_dir = create_temp_directory("html2pdf_")
        # CRÉATION DOSSIER TEMPORAIRE
        input_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(input_path)  # Sauvegarde du fichier
        # ---------- Lecture HTML ----------
        try:
            raw = file.read()
            encoding = (form_data.get('encoding', 'utf-8') if form_data else 'utf-8')
            html_content = raw.decode(encoding, errors='replace')
        except Exception:
            return {"error": "Impossible de lire le fichier HTML"}

        # ---------- Options ----------
        engine = (form_data.get('engine', 'auto') if form_data else 'auto').lower()
        page_size = (form_data.get('pageSize', 'A4') if form_data else 'A4')
        orientation = (form_data.get('orientation', 'portrait') if form_data else 'portrait').lower()
        margin = form_data.get('margin') if form_data else None
        margin_top = form_data.get('marginTop') if form_data else None
        margin_right = form_data.get('marginRight') if form_data else None
        margin_bottom = form_data.get('marginBottom') if form_data else None
        margin_left = form_data.get('marginLeft') if form_data else None
        scale = float(form_data.get('scale', '1.0')) if form_data else 1.0
        print_background = str(form_data.get('printBackground', 'true')).lower() == 'true' if form_data else True
        wait_until = form_data.get('waitUntil', 'networkidle') if form_data else 'networkidle'
        base_url = form_data.get('base_url') if form_data else None
        header_html = form_data.get('headerHtml') if form_data else None
        footer_html = form_data.get('footerHtml') if form_data else None
        css_url = form_data.get('css_url') if form_data else None

        logger.info(f"HTML->PDF (engine={engine}) pageSize={page_size} orient={orientation} scale={scale} bg={print_background}")

        # ---------- Chromium (Playwright) PRIORITAIRE si demandé ----------
        if (engine in ('auto', 'chromium')) and has_chromium:
            try:
                temp_dir = tempfile.mkdtemp()
                # Écrire un fichier HTML temporaire pour gérer les ressources relatives en file://
                html_path = os.path.join(temp_dir, "input.html")
                with open(html_path, "w", encoding=encoding, errors="replace") as f_html:
                    # Si un base_url est fourni et que le HTML ne le définit pas, on peut injecter une balise <base>
                    # pour que les liens relatifs (CSS/IMG) résolvent correctement.
                    if base_url and "<head" in html_content.lower():
                        # Injection propre d'une balise <base> juste après <head>
                        injected = html_content.replace(
                            "<head>",
                            f"<head><base href=\"{base_url}\">",
                        )
                        f_html.write(injected)
                    else:
                        f_html.write(html_content)

                # Lancer Chromium
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                    context = browser.new_context()
                    page = context.new_page()

                    # Naviguer sur file:// pour conserver les ressources locales (si base_url absent)
                    target_url = f"file://{html_path}" if not base_url else f"file://{html_path}"
                    page.goto(target_url, wait_until=wait_until)

                    # Préparer marges (Playwright accepte string "20mm")
                    pdf_margins = {}
                    if margin:
                        pdf_margins = {"top": margin, "right": margin, "bottom": margin, "left": margin}
                    else:
                        if margin_top: pdf_margins["top"] = margin_top
                        if margin_right: pdf_margins["right"] = margin_right
                        if margin_bottom: pdf_margins["bottom"] = margin_bottom
                        if margin_left: pdf_margins["left"] = margin_left

                    # Taille de page : si valeurs width/height fournies dans form_data, on les privilégie
                    width = form_data.get('width')
                    height = form_data.get('height')
                    prefer_css_page_size = True  # respecte @page size s'il existe
                    pdf_kwargs = {
                        "landscape": (orientation == "landscape"),
                        "print_background": print_background,
                        "scale": scale,
                        "prefer_css_page_size": prefer_css_page_size,
                    }
                    if pdf_margins:
                        pdf_kwargs["margin"] = pdf_margins

                    if width and height:
                        pdf_kwargs["width"] = width
                        pdf_kwargs["height"] = height
                    else:
                        # Sinon utiliser un format standard (A4, Letter, etc.)
                        pdf_kwargs["format"] = page_size

                    # Header/Footer (peuvent inclure <span class="pageNumber"></span> / <span class="totalPages"></span>)
                    if header_html or footer_html:
                        pdf_kwargs["display_header_footer"] = True
                        pdf_kwargs["header_template"] = header_html or "<span></span>"
                        pdf_kwargs["footer_template"] = footer_html or "<span></span>"

                    pdf_bytes = page.pdf(**pdf_kwargs)

                    await_close = True
                    try:
                        page.close()
                        context.close()
                        browser.close()
                        await_close = False
                    finally:
                        if await_close:
                            try: browser.close()
                            except: pass

                if pdf_bytes and pdf_bytes[:4] == b'%PDF':
                    output = BytesIO(pdf_bytes)
                    output.seek(0)
                    return send_file(
                        output,
                        mimetype="application/pdf",
                        as_attachment=True,
                        download_name=f"{Path(file.filename).stem}.pdf"
                    )
                else:
                    logger.warning("Playwright a produit un flux qui ne commence pas par %PDF — on tente un fallback.")

            except Exception as e:
                logger.warning(f"Chromium/Playwright a échoué : {e} — tentative fallback.")
            finally:
                cleanup_temp_directory(temp_dir)

        # ---------- Fallback WeasyPrint ----------
        if (engine in ('auto', 'weasyprint')) and has_weasy:
            try:
                html_obj = weasyprint.HTML(string=html_content, base_url=base_url or None)
                stylesheets = []
                if css_url:
                    stylesheets.append(weasyprint.CSS(css_url))
                pdf_bytes = html_obj.write_pdf(stylesheets=stylesheets, presentational_hints=True)
                if pdf_bytes and pdf_bytes[:4] == b'%PDF':
                    output = BytesIO(pdf_bytes)
                    output.seek(0)
                    return send_file(
                        output,
                        mimetype="application/pdf",
                        as_attachment=True,
                        download_name=f"{Path(file.filename).stem}.pdf"
                    )
            except Exception as e:
                logger.warning(f"WeasyPrint échoué : {e}")

        # ---------- Fallback PDFKit / wkhtmltopdf ----------
        if (engine in ('auto', 'pdfkit')) and has_pdfkit:
            try:
                options = {
                    'page-size': page_size,
                    'orientation': orientation.capitalize(),
                    'margin-top': margin_top or margin or '20mm',
                    'margin-right': margin_right or margin or '20mm',
                    'margin-bottom': margin_bottom or margin or '20mm',
                    'margin-left': margin_left or margin or '20mm',
                    'encoding': encoding.upper(),
                    'enable-local-file-access': None,
                    'no-outline': None
                }
                pdf_bytes = pdfkit.from_string(html_content, False, options=options)
                if pdf_bytes and pdf_bytes[:4] == b'%PDF':
                    output = BytesIO(pdf_bytes)
                    output.seek(0)
                    return send_file(
                        output,
                        mimetype="application/pdf",
                        as_attachment=True,
                        download_name=f"{Path(file.filename).stem}.pdf"
                    )
            except Exception as e:
                logger.warning(f"PDFKit échoué : {e}")

        return {"error": "Impossible de générer un PDF valide (tous les moteurs ont échoué)."}

    except Exception as e:
        logger.error(f"Erreur HTML->PDF (Chromium) : {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur lors de la conversion : {e}"}

# ----- TXT -> PDF -----
def convert_txt_to_pdf(file, form_data=None):
    """Conversion professionnelle de TXT vers PDF."""
    # Normalisation
    file, error = normalize_file_input(file)
    if error:
        return error

    if not HAS_REPORTLAB:
        return {'error': 'reportlab non installé'}

    try:
        # Lecture du fichier TXT
        raw = file.read()
        encoding = (form_data.get("encoding", "utf-8") if form_data else "utf-8")
        try:
            text_content = raw.decode(encoding, errors="replace")
        except Exception:
            text_content = raw.decode("utf-8", errors="replace")

        # Options utilisateur
        page_size_opt = (form_data.get("pageSize", "A4") if form_data else "A4").upper()
        font_name = form_data.get("font", "Helvetica") if form_data else "Helvetica"
        font_size = int(form_data.get("fontSize", "12")) if form_data else 12
        margin = int(form_data.get("margin", "50")) if form_data else 50

        logger.info(f"TXT->PDF: page_size={page_size_opt}, font={font_name}, size={font_size}, margin={margin}")

        pagesize = A4 if page_size_opt == "A4" else letter
        width, height = pagesize
        line_height = font_size * 1.4

        # Création du PDF
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=pagesize)

        # Charger la police
        try:
            pdf.setFont(font_name, font_size)
        except:
            logger.warning("Police non trouvée, fallback Helvetica.")
            font_name = "Helvetica"
            pdf.setFont(font_name, font_size)

        y = height - margin
        max_width = width - (margin * 2)

        # Fonction de wrapping des lignes
        def wrap_line(line):
            from reportlab.pdfbase.pdfmetrics import stringWidth
            wrapped = []
            current = ""

            for word in line.split(" "):
                test = (current + " " + word).strip()
                if stringWidth(test, font_name, font_size) < max_width:
                    current = test
                else:
                    if current.strip():
                        wrapped.append(current.strip())
                    current = word
            if current.strip():
                wrapped.append(current.strip())

            return wrapped

        # Écriture du texte
        for line in text_content.split("\n"):
            wrapped_lines = wrap_line(line)

            for wrapped in wrapped_lines:
                if y < margin:
                    pdf.showPage()
                    pdf.setFont(font_name, font_size)
                    y = height - margin

                pdf.drawString(margin, y, wrapped)
                y -= line_height

        pdf.save()
        output.seek(0)

        # Validation PDF
        pdf_bytes = output.getvalue()
        if not pdf_bytes.startswith(b'%PDF'):
            return {"error": "PDF généré invalide"}

        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}.pdf"
        )

    except Exception as e:
        logger.error(f"Erreur TXT->PDF : {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur lors de la conversion : {e}"}

# ----- PDF UNLOCK -----
def analyze_pdf_permissions_advanced(file, form_data=None):
    """
    Analyse complète d'un PDF :
    - Chiffrement (AES/RC4), longueur clé, révision, filtre.
    - Permissions détaillées.
    - Version PDF.
    - Vérifie si mot de passe nécessaire et validité.
    """
    # Protection contre les listes
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]

    if not hasattr(file, 'filename') or not hasattr(file, 'read'):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PYPDF:
        return {"error": "pypdf non installé"}

    try:
        pdf_bytes = file.read()
        pdf_stream = BytesIO(pdf_bytes)
        pdf_stream.seek(0)
        reader = pypdf.PdfReader(pdf_stream)

        report = {
            "filename": file.filename,
            "encrypted": reader.is_encrypted,
            "requires_password": False,
            "password_valid": None,
            "encryption": {},
            "permissions": {},
            "pdf_version": None
        }

        # PDF version
        try:
            report["pdf_version"] = reader.pdf_header.decode("latin-1").strip()
        except:
            report["pdf_version"] = "inconnue"

        # -----------------------------
        # 1) Chiffrement
        # -----------------------------
        if reader.is_encrypted:
            password = form_data.get("password", "") if form_data else ""
            if not password:
                report["requires_password"] = True
                return report

            # Essai user password
            res = reader.decrypt(password)
            if res not in (1, 2, True):
                res2 = reader.decrypt(password, owner_pwd=password)
                report["password_valid"] = res2 in (1, 2, True)
            else:
                report["password_valid"] = True

            # Lecture détails chiffrement
            try:
                encrypt_dict = reader.trailer.get("/Encrypt", {})

                filter_name = encrypt_dict.get("/Filter")
                subfilter_name = encrypt_dict.get("/SubFilter")
                version = encrypt_dict.get("/V")
                revision = encrypt_dict.get("/R")
                key_length = encrypt_dict.get("/Length")  # en bits

                # Détection AES vs RC4
                aes = False
                aes_strength = None
                if filter_name == "/Standard":
                    if version in (4, 5, 6) and subfilter_name in ("/AESV2", "/AESV3"):
                        aes = True
                        aes_strength = key_length
                    else:
                        aes = False
                        aes_strength = key_length
                elif filter_name == "/Adobe.PubSec":
                    aes = True
                    aes_strength = key_length
                else:
                    aes = key_length >= 128  # approximation

                report["encryption"] = {
                    "filter": filter_name,
                    "subfilter": subfilter_name,
                    "version": version,
                    "revision": revision,
                    "key_length_bits": key_length,
                    "aes": aes,
                    "aes_strength_bits": aes_strength
                }
            except Exception as e:
                report["encryption"] = {"error": f"Impossible de lire chiffrement : {e}"}

        # -----------------------------
        # 2) Permissions
        # -----------------------------
        try:
            encrypt_dict = reader.trailer.get("/Encrypt", {})
            perms_raw = encrypt_dict.get("/P")
            if perms_raw is None:
                # PDF non protégé => toutes permissions
                report["permissions"] = {k: True for k in [
                    "can_print","can_modify","can_copy","can_annotate",
                    "can_fill_forms","can_extract_for_accessibility",
                    "can_assemble","can_print_high_res"
                ]}
            else:
                perms = int(perms_raw)

                def allowed(mask):
                    return (perms & mask) == mask

                report["permissions"] = {
                    "can_print": allowed(4),
                    "can_modify": allowed(8),
                    "can_copy": allowed(16),
                    "can_annotate": allowed(32),
                    "can_fill_forms": allowed(256),
                    "can_extract_for_accessibility": allowed(512),
                    "can_assemble": allowed(1024),
                    "can_print_high_res": allowed(2048)
                }
        except Exception as e:
            report["permissions"] = {"error": str(e)}

        return report

    except Exception as e:
        logger.error(f"Erreur analyse PDF avancée : {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur analyse PDF avancée : {e}"}

# ----- PDF PROTECT -----
def protect_pdf_advanced(file, form_data=None, return_report=False):
    """
    Protège un PDF avec mot de passe et permissions avancées.
    Retourne un PDF protégé et optionnellement un rapport JSON :
      - user_password : requis pour ouvrir
      - owner_password : mot de passe administrateur
      - encryption : 'AES128' (défaut), 'AES256', 'RC4'
      - allow_printing, allow_copy, allow_modify, allow_annotate, allow_fill_forms, allow_assemble, allow_extract_access : true/false
    """
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]

    if not hasattr(file, 'filename') or not hasattr(file, 'read'):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PYPDF:
        return {"error": "pypdf non installé"}

    try:
        # ===============================
        # 1) Paramètres utilisateur
        # ===============================
        user_password = (form_data.get("user_password") if form_data else "") or ""
        owner_password = (form_data.get("owner_password") if form_data else None) or (user_password + "_master")
        encryption_type = (form_data.get("encryption", "AES128") if form_data else "AES128").upper()

        # Permissions avancées
        allow_printing = str(form_data.get("allow_printing", "true")).lower() == "true"
        allow_copy = str(form_data.get("allow_copy", "true")).lower() == "true"
        allow_modify = str(form_data.get("allow_modify", "false")).lower() == "true"
        allow_annotate = str(form_data.get("allow_annotate", "true")).lower() == "true"
        allow_fill_forms = str(form_data.get("allow_fill_forms", "true")).lower() == "true"
        allow_assemble = str(form_data.get("allow_assemble", "true")).lower() == "true"
        allow_extract_access = str(form_data.get("allow_extract_access", "true")).lower() == "true"

        if not user_password or len(user_password) < 6:
            return {"error": "Mot de passe utilisateur requis et >= 6 caractères"}

        # ===============================
        # 2) Lecture PDF
        # ===============================
        pdf_bytes = file.read()
        reader = pypdf.PdfReader(BytesIO(pdf_bytes))

        initial_permissions = {}
        initial_encrypted = reader.is_encrypted
        if reader.is_encrypted:
            try:
                reader.decrypt(owner_password)
            except:
                pass

        for perm_name, perm_mask in [
            ("can_print", 4),
            ("can_modify", 8),
            ("can_copy", 16),
            ("can_annotate", 32),
            ("can_fill_forms", 256),
            ("can_extract_accessibility", 512),
            ("can_assemble", 1024),
            ("can_print_high_res", 2048),
        ]:
            try:
                perms_raw = reader.trailer.get("/Encrypt", {}).get("/P")
                if perms_raw is None:
                    initial_permissions[perm_name] = True
                else:
                    initial_permissions[perm_name] = bool(int(perms_raw) & perm_mask)
            except:
                initial_permissions[perm_name] = None

        if len(reader.pages) == 0:
            return {"error": "PDF vide ou illisible"}

        # ===============================
        # 3) Création PDF protégé
        # ===============================
        writer = pypdf.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        # Permissions PDF combinées
        permissions = 0
        if allow_printing: permissions |= pypdf.Permissions.PRINTING
        if allow_copy: permissions |= pypdf.Permissions.COPYING
        if allow_modify: permissions |= pypdf.Permissions.MODIFYING
        if allow_annotate: permissions |= pypdf.Permissions.ANNOTATING
        if allow_fill_forms: permissions |= pypdf.Permissions.FILLING
        if allow_assemble: permissions |= pypdf.Permissions.ASSEMBLING
        if allow_extract_access: permissions |= pypdf.Permissions.ACCESSIBILITY

        # Algorithme
        if encryption_type == "AES256":
            encryption_algorithm = pypdf.Encryption.AES_256
        elif encryption_type == "RC4":
            encryption_algorithm = pypdf.Encryption.RC4_128
        else:
            encryption_algorithm = pypdf.Encryption.AES_128

        # Appliquer chiffrement
        writer.encrypt(
            user_password=user_password,
            owner_password=owner_password,
            permissions=permissions,
            encryption_algorithm=encryption_algorithm
        )

        now = datetime.now().strftime("D:%Y%m%d%H%M%S")
        writer.add_metadata({
            "/Producer": "PDF Fusion Pro",
            "/Creator": "PDF Fusion Pro",
            "/Title": f"{Path(file.filename).stem} (protégé)",
            "/CreationDate": now,
            "/ModDate": now
        })

        output = BytesIO()
        writer.write(output)
        output.seek(0)

        # ===============================
        # 4) Rapport (optionnel)
        # ===============================
        report = {
            "filename": file.filename,
            "original_encrypted": initial_encrypted,
            "original_permissions": initial_permissions,
            "new_encrypted": True,
            "new_permissions": {
                "can_print": allow_printing,
                "can_modify": allow_modify,
                "can_copy": allow_copy,
                "can_annotate": allow_annotate,
                "can_fill_forms": allow_fill_forms,
                "can_extract_accessibility": allow_extract_access,
                "can_assemble": allow_assemble
            },
            "encryption_algorithm": encryption_type
        }

        if return_report:
            return {
                "file": send_file(
                    output,
                    mimetype="application/pdf",
                    as_attachment=True,
                    download_name=f"{Path(file.filename).stem}_protege.pdf"
                ),
                "report": report
            }

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{Path(file.filename).stem}_protege.pdf"
        )

    except Exception as e:
        logger.error(f"Erreur protection PDF avancée : {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Erreur lors de la protection avancée : {e}"}



# ================= FONCTIONS UTILITAIRES IMAGE =================

def build_ocr_lang_string(language_input):
    """
    Construit une chaîne de langues pour Tesseract à partir de l'entrée utilisateur.
    Exemple: "fra+eng" ou ["fra", "eng"] ou "fra"
    """
    if isinstance(language_input, str):
        if '+' in language_input:
            langs = [l.strip() for l in language_input.split('+') if l.strip()]
        else:
            langs = [language_input]
    elif isinstance(language_input, list):
        langs = language_input
    else:
        langs = ['fra']
    
    ocr_langs = []
    for lang in langs:
        tess_lang = OCR_LANG_MAP.get(lang, 'fra')
        ocr_langs.append(tess_lang)
    
    return "+".join(ocr_langs) if ocr_langs else 'fra'

def normalize_file_input(file_input):
    """
    Convertit l'entrée en un seul fichier.
    Retourne (file, None) en cas de succès, (None, error_dict) en cas d'erreur.
    """
    # Cas liste
    if isinstance(file_input, list):
        if not file_input:
            return None, {'error': 'Aucun fichier fourni'}
        return file_input[0], None
    
    # Cas fichier unique
    if not hasattr(file_input, 'filename') or not hasattr(file_input, 'save'):
        return None, {'error': 'Objet fichier invalide'}
    
    return file_input, None

def normalize_files_input(files_input, max_files=None):
    """
    Convertit l'entrée en une liste de fichiers.
    Retourne (files, None) en cas de succès, (None, error_dict) en cas d'erreur.
    """
    if not isinstance(files_input, list):
        files_input = [files_input] if files_input else []
    
    # Filtrer les fichiers valides
    valid_files = [f for f in files_input 
                   if hasattr(f, 'filename') and hasattr(f, 'save') and f.filename]
    
    if not valid_files:
        return None, {'error': 'Aucun fichier valide fourni'}
    
    if max_files and len(valid_files) > max_files:
        return None, {'error': f'Maximum {max_files} fichiers autorisés'}
    
    return valid_files, None

def safe_ocr_call(func, *args, **kwargs):
    """
    Wrapper sécurisé pour les appels OCR.
    Retourne le résultat ou une chaîne vide en cas d'erreur.
    """
    if not HAS_TESSERACT:
        logger.warning("Tesseract non installé")
        return ""
    
    try:
        return func(*args, **kwargs)
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract non trouvé dans le système")
        return ""
    except pytesseract.TesseractError as e:
        logger.error(f"Erreur Tesseract: {e}")
        return ""
    except Exception as e:
        logger.error(f"Erreur OCR inattendue: {e}")
        return ""

def safe_image_operation(func, *args, default=None, **kwargs):
    """
    Wrapper sécurisé pour les opérations sur les images.
    """
    if not HAS_PILLOW:
        return default
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Erreur opération image: {e}")
        return default

def validate_file_extension(filename, allowed_extensions):
    """
    Vérifie si l'extension du fichier est autorisée.
    """
    if not filename:
        return False
    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions

def create_temp_directory(prefix="conversion_"):
    """
    Crée un dossier temporaire et retourne son chemin.
    """
    return tempfile.mkdtemp(prefix=prefix)

def cleanup_temp_directory(temp_dir):
    """
    Nettoie un dossier temporaire en ignorant les erreurs.
    """
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.debug(f"Dossier temporaire nettoyé: {temp_dir}")

def _ensure_rgb(im: Image.Image) -> Image.Image:
    """Convertit l'image en RGB."""
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        if im.mode == "P":
            im = im.convert("RGBA")
        mask = im.split()[-1] if im.mode in ("RGBA", "LA") else None
        bg.paste(im, mask=mask)
        return bg
    elif im.mode != "RGB":
        return im.convert("RGB")
    return im

def _auto_rotate_osd(im: Image.Image) -> Image.Image:
    """Corrige automatiquement l'orientation via Tesseract OSD."""
    try:
        osd = pytesseract.image_to_osd(im)
        for line in osd.splitlines():
            if "Rotate:" in line:
                angle = int(line.split(":")[1].strip())
                if angle in (90, 180, 270):
                    return im.rotate(360 - angle, expand=True)
                break
    except Exception as e:
        logger.debug(f"OSD non disponible: {e}")
    return im

def _binarize_otsu(im: Image.Image) -> Image.Image:
    """Binarisation par méthode d'Otsu."""
    try:
        gray = im.convert("L")
        arr = np.array(gray)
        hist, _ = np.histogram(arr, bins=256, range=(0, 255))
        total = arr.size
        sum_total = np.dot(np.arange(256), hist)
        sumB = 0.0
        wB = 0
        max_var = 0.0
        threshold = 127
        
        for t in range(256):
            wB += hist[t]
            if wB == 0:
                continue
            wF = total - wB
            if wF == 0:
                break
            sumB += t * hist[t]
            mB = sumB / wB
            mF = (sum_total - sumB) / wF
            between = wB * wF * (mB - mF) ** 2
            if between > max_var:
                max_var = between
                threshold = t
        
        bw = gray.point(lambda x: 255 if x > threshold else 0, mode='1')
        return bw.convert("L")
    except Exception as e:
        logger.warning(f"Binarisation Otsu échouée, utilisation seuil simple: {e}")
        gray = im.convert("L")
        bw = gray.point(lambda x: 255 if x > 160 else 0, mode='1')
        return bw.convert("L")

def preprocess_for_ocr(im: Image.Image, enhance_image: bool = True, 
                       deskew: bool = True, binarize: bool = False, 
                       max_ocr_px: int = 3000) -> Image.Image:
    """Prétraite l'image pour l'OCR."""
    work = _ensure_rgb(im)
    
    if enhance_image:
        work = ImageOps.autocontrast(work)
        work = work.filter(ImageFilter.MedianFilter(size=3))
    
    if deskew:
        work = _auto_rotate_osd(work)
    
    if binarize:
        work = _binarize_otsu(work).convert("RGB")
    
    # Limiter la taille pour éviter les problèmes de mémoire
    w, h = work.size
    max_side = max(w, h)
    if max_side > max_ocr_px:
        ratio = max_ocr_px / float(max_side)
        new_size = (int(w * ratio), int(h * ratio))
        work = work.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(f"Image redimensionnée: {w}x{h} -> {new_size[0]}x{new_size[1]}")
    
    return work

# ================= FONCTIONS OCR =================

def ocr_get_words_positions(img: Image.Image, ocr_lang: str, config: str, min_conf: int = 30) -> List[Dict]:
    """
    Retourne une liste de mots avec positions.
    
    Args:
        img: Image PIL
        ocr_lang: Langue(s) pour Tesseract
        config: Configuration Tesseract
        min_conf: Confidence minimale (0-100)
    
    Returns:
        Liste de dictionnaires avec texte et positions
    """
    data = pytesseract.image_to_data(
        img,
        lang=ocr_lang,
        output_type=Output.DICT,
        config=config
    )

    words = []
    for i in range(len(data["text"])):
        txt = data["text"][i].strip()
        try:
            conf = int(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1

        if not txt or conf < min_conf:
            continue

        words.append({
            "text": txt,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i],
            "conf": conf
        })
    
    return words

def ocr_preserve_layout(im: Image.Image, ocr_lang: str, config: str, min_conf: int) -> str:
    """
    Reconstruit paragraphes/ligne avec préservation de layout.
    """
    try:
        data = pytesseract.image_to_data(
            im, 
            lang=ocr_lang, 
            output_type=Output.DICT, 
            config=config
        )
    except Exception as e:
        raise RuntimeError(f"OCR data error: {e}")

    # Grouper par (block_num, par_num), puis par line_num
    blocks = defaultdict(lambda: defaultdict(list))
    N = len(data.get('text', []))
    
    for i in range(N):
        txt = (data['text'][i] or "").strip()
        try:
            conf = int(data['conf'][i])
        except (ValueError, TypeError):
            conf = -1
            
        if not txt or conf < min_conf:
            continue
        
        b = data.get('block_num', [0])[i]
        p = data.get('par_num', [0])[i]
        ln = data.get('line_num', [0])[i]
        left = data.get('left', [0])[i]
        blocks[(b, p)][ln].append((left, txt))

    paragraphs = []
    # Trier par block/par puis lignes croissantes
    for (b, p), lines in sorted(blocks.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        # Reconstruire chaque ligne
        line_texts = []
        for ln, items in sorted(lines.items(), key=lambda kv: kv[0]):
            items_sorted = sorted(items, key=lambda t: t[0])
            line_texts.append(" ".join([t for _, t in items_sorted]).strip())
        
        if line_texts:
            paragraphs.append("\n".join(line_texts).strip())

    return "\n\n".join([para for para in paragraphs if para])

def ocr_simple(im: Image.Image, ocr_lang: str, config: str) -> str:
    """OCR simple sans préservation de layout."""
    try:
        return (pytesseract.image_to_string(im, lang=ocr_lang, config=config) or "").strip()
    except Exception as e:
        raise RuntimeError(f"OCR string error: {e}")

def perform_ocr(image: Image.Image, ocr_lang: str, config: str, 
                preserve_layout: bool, min_conf: int) -> str:
    """Exécute l'OCR avec la méthode choisie."""
    if preserve_layout:
        return ocr_preserve_layout(image, ocr_lang, config, min_conf)
    else:
        return ocr_simple(image, ocr_lang, config)

# ================= FONCTIONS DE POST-TRAITEMENT =================

def detect_columns_from_words(words: List[Dict], max_columns: int = 4) -> Dict[int, List[Dict]]:
    """
    Regroupe les mots en colonnes via clustering X.
    
    Args:
        words: Liste de mots avec positions
        max_columns: Nombre maximum de colonnes
    
    Returns:
        Dictionnaire: index_colonne -> [mots]
    """
    if not words:
        return {0: []}

    X_coords = np.array([[w["left"]] for w in words])
    
    # Ajuster le nombre de clusters
    k = min(max_columns, len(words))
    if k < 2:  # Pas assez de mots pour plusieurs colonnes
        return {0: words}
    
    kmeans = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = kmeans.fit_predict(X_coords)

    columns = {}
    for w, lab in zip(words, labels):
        if lab not in columns:
            columns[lab] = []
        columns[lab].append(w)

    # Trier par position horizontale
    sorted_cols = dict(sorted(
        columns.items(), 
        key=lambda kv: np.mean([w["left"] for w in kv[1]])
    ))

    return sorted_cols

def reconstruct_text_from_columns(columns: Dict[int, List[Dict]]) -> str:
    """
    Reconstruit du texte à partir des colonnes détectées.
    """
    result = []
    line_threshold = 20  # Seuil pour considérer la même ligne

    for col_idx, words in columns.items():
        # Trier par position verticale puis horizontale
        words_sorted = sorted(words, key=lambda w: (w["top"], w["left"]))
        
        text_lines = []
        current_top = -999
        buffer = []

        for w in words_sorted:
            if abs(w["top"] - current_top) > line_threshold:
                if buffer:
                    text_lines.append(" ".join(buffer))
                buffer = []
                current_top = w["top"]
            buffer.append(w["text"])

        if buffer:
            text_lines.append(" ".join(buffer))

        result.append(f"[COLONNE {col_idx+1}]\n" + "\n".join(text_lines) + "\n")

    return "\n\n".join(result)

def ai_restructure_text(text: str, api_key: Optional[str] = None, 
                        model: str = "gpt-4o-mini") -> str:
    """
    Passe le texte OCR dans un modèle IA pour le structurer.
    """
    if not text.strip():
        return text
    
    prompt = f"""Tu es un expert en mise en forme documentaire.
Reformate le texte suivant issu d'un OCR :
- reforme des paragraphes propres
- crée des titres (H1, H2) si pertinent
- supprime les artefacts OCR (mots collés, caractères étranges)
- reconstruit une mise en page logique et lisible
- retourne uniquement du texte propre, sans commentaires

TEXTE A REFORMATER :
{text}
"""
    
    # Essayer d'utiliser OpenAI si la clé est fournie
    if api_key:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except ImportError:
            logger.warning("Module openai non installé")
        except Exception as e:
            logger.error(f"Erreur API OpenAI: {e}")
    
    # Fallback: retourner le texte original avec un avertissement
    return f"[NOTE: Restructuration IA non appliquée - clé API manquante]\n\n{text}"

# ================= FONCTIONS D'EXTRACTION DES PARAMÈTRES =================

def extract_ocr_params(form_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Extrait et valide les paramètres du formulaire."""
    if form_data is None:
        form_data = {}
    
    # Paramètres de base
    params = {
        'language': form_data.get('language', 'fra'),
        'preserve_layout': str(form_data.get('preserve_layout', 'true')).lower() == 'true',
        'enhance_image': str(form_data.get('enhance_image', 'true')).lower() == 'true',
        'deskew': str(form_data.get('deskew', 'true')).lower() == 'true',
        'binarize': str(form_data.get('binarize', 'false')).lower() == 'true',
        'min_conf': int(form_data.get('min_confidence', '30')),
        'oem': int(form_data.get('oem', '3')),
        'psm': int(form_data.get('psm', '6')),
        'add_original_image': str(form_data.get('add_original_image', 'true')).lower() == 'true',
        'max_image_width_in': float(form_data.get('max_image_width_in', '6.0')),
        'max_ocr_px': int(form_data.get('max_ocr_px', '3000')),
        'export_positions': str(form_data.get('export_positions', 'false')).lower() == 'true',
        'detect_columns': str(form_data.get('detect_columns', 'false')).lower() == 'true',
        'ai_restructure': str(form_data.get('ai_restructure', 'false')).lower() == 'true',
        'ai_api_key': form_data.get('ai_api_key', os.environ.get('OPENAI_API_KEY', '')),
    }
    
    # Construire la chaîne de langue Tesseract
    selected_langs = [l.strip() for l in params['language'].split('+') if l.strip()]
    ocr_langs = []
    for lang in selected_langs:
        tess_lang = LANG_MAP.get(lang, 'fra')
        ocr_langs.append(tess_lang)
    
    params['ocr_lang'] = "+".join(ocr_langs) if ocr_langs else 'fra'
    params['custom_config'] = f'--oem {params["oem"]} --psm {params["psm"]}'
    
    logger.info(f"Paramètres OCR: langue={params['ocr_lang']}, "
                f"preserve_layout={params['preserve_layout']}, "
                f"min_conf={params['min_conf']}")
    
    return params

# ================= FONCTIONS DE GESTION DES IMAGES =================

def extract_frames(image_path: str) -> List[Image.Image]:
    """Extrait les frames d'une image (TIFF multi-pages)."""
    frames = []
    try:
        img = Image.open(image_path)
        
        # Vérifier si c'est un multi-pages
        if getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1:
            for i in range(img.n_frames):
                img.seek(i)
                frames.append(img.copy())
        else:
            frames.append(img)
    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture de l'image: {e}")
        raise
    
    return frames

# ================= FONCTIONS DE CONSTRUCTION DOCX =================

def create_base_document(filename: str, params: Dict) -> Document:
    """Crée le document Word de base avec en-tête."""
    doc = Document()
    
    # Titre principal
    doc.add_heading(f"Texte extrait de l'image : {Path(filename).stem}", 0)
    
    # Informations d'extraction
    doc.add_paragraph(f"Date d'extraction : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    doc.add_paragraph(f"Langues OCR : {params['ocr_lang']}")
    doc.add_paragraph(f"Configuration : OEM={params['oem']}, PSM={params['psm']}")
    doc.add_paragraph()
    
    return doc

def add_page_to_document(doc: Document, page_num: int, extracted_text: str, 
                         original_image: Image.Image, params: Dict):
    """Ajoute une page au document Word."""
    
    if page_num > 1:
        doc.add_page_break()
    
    doc.add_heading(f'Page {page_num}', level=1)
    
    # Ajouter le texte extrait
    if extracted_text and extracted_text.strip():
        for para in extracted_text.split("\n\n"):
            if para.strip():
                for line in para.split("\n"):
                    doc.add_paragraph(line.strip())
                doc.add_paragraph()  # Espace entre paragraphes
    else:
        doc.add_paragraph("[Aucun texte détecté sur cette page]")
    
    # Ajouter l'image originale si demandé
    if params['add_original_image']:
        doc.add_paragraph()
        doc.add_heading("Image originale", level=2)
        
        # Sauvegarder l'image en mémoire
        buf = BytesIO()
        orig_rgb = _ensure_rgb(original_image)
        orig_rgb.save(buf, format='PNG')
        buf.seek(0)
        
        # Ajouter l'image avec redimensionnement
        doc.add_picture(buf, width=Inches(params['max_image_width_in']))
        
        # Légende
        cap = doc.add_paragraph()
        cap.style = 'Caption'
        cap.add_run(f"Image originale - Page {page_num}")

def add_positions_to_doc(doc: Document, image: Image.Image, params: Dict):
    """Ajoute les positions des mots au document."""
    words_pos = ocr_get_words_positions(
        image, 
        params['ocr_lang'], 
        params['custom_config'], 
        params['min_conf']
    )
    
    doc.add_heading("Données OCR (mots + positions)", level=2)
    doc.add_paragraph(json.dumps(words_pos, indent=2, ensure_ascii=False))

def add_columns_to_doc(doc: Document, image: Image.Image, params: Dict):
    """Ajoute le texte reconstruit par colonnes."""
    words_pos = ocr_get_words_positions(
        image, 
        params['ocr_lang'], 
        params['custom_config'], 
        params['min_conf']
    )
    
    columns = detect_columns_from_words(words_pos)
    text_columns = reconstruct_text_from_columns(columns)
    
    doc.add_heading("Texte (mise en page colonnes détectée)", level=2)
    doc.add_paragraph(text_columns)

def add_ai_restructured_to_doc(doc: Document, extracted_text: str, params: Dict):
    """Ajoute le texte restructuré par IA."""
    structured_text = ai_restructure_text(
        extracted_text, 
        api_key=params.get('ai_api_key')
    )
    
    doc.add_heading("Texte restructuré par IA", level=2)
    doc.add_paragraph(structured_text)

def generate_document_response(doc: Document, original_filename: str):
    """Génère la réponse avec le document Word."""
    # Protection contre les listes
    if isinstance(file, list):
        if len(file) == 0:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]
    
    # Vérifier que c'est bien un objet fichier
    if not hasattr(file, 'filename') or not hasattr(file, 'save'):
        return {'error': 'Objet fichier invalide'}

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    
    logger.info(f"Document Word généré ({output.getbuffer().nbytes} octets)")
    
    from flask import send_file  # Import ici si utilisation Flask
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f"{Path(original_filename).stem}.docx"
    )

# ================= FONCTION PRINCIPALE =================

def convert_image_to_word(file, form_data: Optional[Dict] = None):
    # ✅ Validation de l'objet fichier
    if not hasattr(file, "filename") or not hasattr(file, "save"):
        return {'error': 'Objet fichier invalide'}

    if not HAS_PILLOW:
        return {'error': 'Pillow non installé'}
    if not HAS_TESSERACT:
        return {'error': 'Tesseract non installé ou non trouvé'}
    if not HAS_DOCX:
        return {'error': 'python-docx non installé'}

    # ✅ Sauvegarde du nom avant toute opération
    original_filename = file.filename

    temp_dir = None
    try:
        temp_dir = create_temp_directory("image2word_")
        input_path = os.path.join(temp_dir, secure_filename(original_filename))
        file.save(input_path)

        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            return {'error': 'Fichier image invalide ou vide'}

        logger.info(f"Image sauvegardée : {input_path}")

        params = extract_ocr_params(form_data)

        frames = extract_frames(input_path)
        logger.info(f"Nombre de pages/frames: {len(frames)}")

        # ✅ Vérification explicite si aucune frame extraite
        if not frames:
            return {'error': "Impossible d'extraire les pages de l'image (format non supporté ou fichier corrompu)"}

        # ✅ original_filename transmis, jamais file.filename
        doc = create_base_document(original_filename, params)

        any_text = False

        for idx, frame in enumerate(frames, start=1):
            logger.info(f"Traitement de la page {idx}/{len(frames)}")

            work = preprocess_for_ocr(
                frame,
                enhance_image=params['enhance_image'],
                deskew=params['deskew'],
                binarize=params['binarize'],
                max_ocr_px=params['max_ocr_px']
            )

            try:
                extracted = perform_ocr(
                    work,
                    params['ocr_lang'],
                    params['custom_config'],
                    params['preserve_layout'],
                    params['min_conf']
                )
            except Exception as e:
                logger.error(f"Erreur OCR page {idx}: {e}")
                extracted = ""

            # ✅ original_filename transmis
            add_page_to_document(doc, idx, extracted, frame, params)

            if extracted and extracted.strip():
                any_text = True

            # ✅ Post-traitements appliqués sur TOUTES les pages, pas seulement la première
            if params['export_positions']:
                add_positions_to_doc(doc, work, params)

            if params['detect_columns']:
                add_columns_to_doc(doc, work, params)

            if params['ai_restructure'] and extracted:
                add_ai_restructured_to_doc(doc, extracted, params)

        if not any_text:
            doc.add_paragraph()
            doc.add_paragraph(
                "Note : Aucun texte n'a pu être extrait automatiquement "
                "(image trop floue, langue non installée, ou paramètres inadaptés)."
            )

        # ✅ @after_this_request si generate_document_response utilise send_file
        @after_this_request
        def cleanup(response):
            cleanup_temp_directory(temp_dir)
            return response

        return generate_document_response(doc, original_filename)  # ✅ variable locale

    except Exception as e:
        logger.error(f"Erreur Image->Word : {e}")
        logger.error(traceback.format_exc())
        cleanup_temp_directory(temp_dir)  # ✅ nettoyage immédiat sur erreur
        return {'error': f'Erreur lors de la conversion: {str(e)}'}

# ================= POINT D'ENTRÉE POUR TEST =================

if __name__ == "__main__":
    # Test simple si exécuté directement
    print("Module de conversion Image -> Word")
    print(f"Dépendances: Pillow={HAS_PILLOW}, Tesseract={HAS_TESSERACT}, python-docx={HAS_DOCX}")
    print("\nFonctions disponibles:")
    print("  - convert_image_to_word(file, form_data)")
    print("  - ocr_get_words_positions(img, lang, config, min_conf)")
    print("  - detect_columns_from_words(words)")
    print("  - ai_restructure_text(text, api_key)")

# ----- IMAGE -> EXCEL -----
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
    """Convertit un ou plusieurs fichiers CSV en Excel."""
    # Normalisation
    files, error = normalize_files_input(files, max_files=5)
    if error:
        return error

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
    """Convertit un ou plusieurs fichiers Excel en CSV."""
    # Normalisation
    files, error = normalize_files_input(files, max_files=5)
    if error:
        return error

    if not HAS_PANDAS:
        return {'error': 'pandas non installé'}
    
    import pandas as pd
    import zipfile

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
                        df.to_csv(csv_buffer, sep=delimiter, index=False, 
                                 header=include_header=='true', encoding=encoding)
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
            df.to_csv(output, sep=delimiter, index=False, 
                     header=include_header=='true', encoding=encoding)
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
    # Sécurité : accepter liste ou fichier
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]
    
    if not hasattr(file, "filename"):
        return {'error': 'Objet fichier invalide'}

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
    # Sécurité : accepter liste ou fichier
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]
    
    if not hasattr(file, "filename"):
        return {'error': 'Objet fichier invalide'}

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
    # Sécurité : accepter liste ou fichier
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]
    
    if not hasattr(file, "filename"):
        return {'error': 'Objet fichier invalide'}

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
    # Sécurité : accepter liste ou fichier
    if isinstance(file, list):
        if not file:
            return {'error': 'Aucun fichier fourni'}
        file = file[0]
    
    if not hasattr(file, "filename"):
        return {'error': 'Objet fichier invalide'}

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
                ocr_text = safe_ocr_call(pytesseract.image_to_string, img, lang='fra')
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
