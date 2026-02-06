#!/usr/bin/env python3
"""
Blueprint pour les conversions de fichiers - Version avec OCR pour Image/PDF -> Excel
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

# OCR / PDF -> images
try:
    import pytesseract
    from pytesseract import Output
except Exception as _e:
    pytesseract = None
    Output = None

try:
    from pdf2image import convert_from_bytes
except Exception as _e:
    convert_from_bytes = None

# Import corrigé - utiliser la classe FileValidation si dispo
try:
    from utils.file_validation import FileValidation
    FILE_VALIDATION_AVAILABLE = True
except ImportError:
    print("⚠️  FileValidation non disponible - utilisation d'une version simplifiée")
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
            # (Flask ne renseigne pas toujours content_length au niveau du FileStorage)
            if max_size and request.content_length:
                if request.content_length > max_size:
                    return False, f"Fichier trop volumineux (> {max_size/1024/1024:.1f} MB)"

            return (ext in allowed_extensions,
                    f"Format {ext} supporté" if ext in allowed_extensions else f"Format {ext} non supporté")


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
        try:
            margin = int(request.form.get('margin', 10))
        except ValueError:
            margin = 10
        quality = request.form.get('quality', 'medium')

        if not files or files[0].filename == '':
            flash('Veuillez sélectionner au moins un fichier', 'error')
            return redirect(request.url)

        # Valider les fichiers
        valid_files = []
        for file in files:
            if file.filename == '':
                continue

            # Validation simple par extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext in AppConfig.SUPPORTED_IMAGE_FORMATS.get('pdf', {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}):
                valid_files.append(file)
            else:
                flash(f'Format non supporté: {file.filename} ({ext})', 'warning')

        if not valid_files:
            flash('Aucun fichier valide pour la conversion', 'error')
            return redirect(request.url)

        try:
            # Créer un PDF en mémoire
            output = BytesIO()

            # Déterminer la taille de page (A4 par défaut)
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

                    # Sauvegarder temporairement en PNG (ReportLab lit mieux le PNG)
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    img.save(temp_file.name, 'PNG')

                    # Ajouter l'image au PDF
                    c.drawImage(temp_file.name, x, y, width=new_width, height=new_height)

                    # Nettoyer le fichier temporaire
                    try:
                        os.unlink(temp_file.name)
                    except Exception:
                        pass

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
    """Conversion d'images en document Word - Version fonctionnelle (gabarit)."""
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
        if ext not in AppConfig.SUPPORTED_IMAGE_FORMATS.get('word', {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}):
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


# -----------------------------
# Helpers OCR pour Image -> Excel
# -----------------------------
def _ensure_ocr_available():
    if pytesseract is None or Output is None:
        raise RuntimeError("pytesseract n'est pas disponible. Installez 'pytesseract' et le binaire système 'tesseract'.")


def ocr_image_to_dataframe(pil_image, lang='fra+eng', min_conf=30):
    """
    OCR sur une image PIL → DataFrame tabulaire approximatif par lignes.
    - Regroupe les mots par (page, block, paragraph, line)
    - Trie par position horizontale (left)
    - Produit une ligne = liste de mots (pad à longueur max)
    """
    _ensure_ocr_available()

    try:
        df_data = pytesseract.image_to_data(pil_image, lang=lang, output_type=Output.DATAFRAME)
    except Exception as e:
        raise RuntimeError(f"OCR indisponible: {e}")

    if df_data is None or df_data.empty:
        # Fallback: texte brut → une seule colonne
        raw = pytesseract.image_to_string(pil_image, lang=lang) or ""
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return pd.DataFrame({"Texte": lines if lines else ["(vide)"]})

    # Nettoyage
    df = df_data.copy()
    # Convertir conf en numérique et filtrer
    try:
        df['conf'] = pd.to_numeric(df['conf'], errors='coerce')
    except Exception:
        df['conf'] = -1
    df = df[(df['text'].astype(str).str.strip() != '') & (df['conf'].fillna(-1) >= min_conf)]

    if df.empty:
        raw = pytesseract.image_to_string(pil_image, lang=lang) or ""
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return pd.DataFrame({"Texte": lines if lines else ["(vide)"]})

    # Regrouper par lignes logiques
    group_cols = ['page_num', 'block_num', 'par_num', 'line_num']
    df = df.sort_values(['page_num', 'line_num', 'left'])

    rows = []
    for _, grp in df.groupby(group_cols, dropna=False):
        # Ordonner les mots sur l'axe X
        words = [w for w in grp.sort_values('left')['text'].astype(str).tolist() if w.strip()]
        if words:
            rows.append(words)

    if not rows:
        raw = pytesseract.image_to_string(pil_image, lang=lang) or ""
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return pd.DataFrame({"Texte": lines if lines else ["(vide)"]})

    # Normaliser le nombre de colonnes
    max_cols = max(len(r) for r in rows)
    norm_rows = [r + [''] * (max_cols - len(r)) for r in rows]
    df_out = pd.DataFrame(norm_rows)
    # En-têtes génériques Col1..ColN
    df_out.columns = [f"Col{idx+1}" for idx in range(df_out.shape[1])]
    return df_out


@conversion_bp.route('/conversion/image-vers-excel', methods=['GET', 'POST'])
def image_to_excel():
    """
    Conversion d'images ou PDF en Excel avec OCR (pytesseract) - Version fonctionnelle.
    - Accepte images (PNG, JPG, JPEG, BMP, TIFF) et PDF scannés
    - Pour PDF, rasterisation page par page (300 DPI) via pdf2image
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        file = request.files['file']
        format_type = (request.form.get('format') or 'xlsx').lower().strip()

        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400

        # ✅ Accepter aussi les PDF côté serveur (aligné avec le front)
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.pdf'}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Format non supporté: {file_ext}'}), 400

        if format_type not in ('xlsx', 'csv'):
            return jsonify({'error': f'Format de sortie non supporté: {format_type}'}), 400

        try:
            frames = []

            if file_ext == '.pdf':
                # Prérequis pdf2image + poppler
                if convert_from_bytes is None:
                    return jsonify({'error': "pdf2image/poppler non disponibles. Installez 'pdf2image' et 'poppler'."}), 500

                try:
                    pdf_bytes = file.read()
                    pages = convert_from_bytes(pdf_bytes, dpi=300)
                except Exception as e:
                    return jsonify({'error': f'Impossible de convertir le PDF en images (poppler requis): {e}'}), 500

                if not pages:
                    return jsonify({'error': 'Aucune page détectée dans le PDF'}), 400

                for idx, page_img in enumerate(pages, start=1):
                    df_page = ocr_image_to_dataframe(page_img, lang='fra+eng', min_conf=30)
                    # Ajouter une colonne "Page" pour tracer l'origine
                    df_page.insert(0, 'Page', idx)
                    frames.append(df_page)

            else:
                # Image unique
                try:
                    img = Image.open(file.stream).convert('RGB')
                except Exception as e:
                    return jsonify({'error': f'Image invalide: {e}'}), 400

                df_img = ocr_image_to_dataframe(img, lang='fra+eng', min_conf=30)
                frames.append(df_img)

            # Fusionner
            if not frames:
                return jsonify({'error': "Aucune donnée extraite"}), 500

            df = pd.concat(frames, ignore_index=True)

            # Exporter
            output = BytesIO()
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base = os.path.splitext(filename)[0] or "export"

            if format_type == 'xlsx':
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Extraction')
                    # Onglet d’infos (optionnel)
                    info_df = pd.DataFrame({
                        'Information': ['Fichier source', 'Date conversion', 'Lignes', 'Colonnes'],
                        'Valeur': [filename, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(df), df.shape[1]]
                    })
                    info_df.to_excel(writer, index=False, sheet_name='Infos')
                output.seek(0)
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                out_name = f'{base}_{stamp}.xlsx'
            else:
                # CSV en UTF-8 BOM pour compat Excel
                csv_bytes = df.to_csv(index=False).encode('utf-8-sig')
                output = BytesIO(csv_bytes)
                mimetype = 'text/csv'
                out_name = f'{base}_{stamp}.csv'

            # Sanity check
            if output.getbuffer().nbytes < 10:
                return jsonify({'error': 'Fichier vide généré'}), 500

            return send_file(output, mimetype=mimetype, as_attachment=True, download_name=out_name)

        except Exception as e:
            current_app.logger.error(f"Erreur conversion Excel: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Erreur de conversion: {str(e)}'}), 500

    # GET
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
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Test')
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
                except Exception:
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
    'python-docx': 'Pour génération Word',
    'pytesseract': 'Pour OCR (Image/PDF -> Excel)',
    'pdf2image': 'Pour rasteriser les PDF scannés (nécessite poppler)'
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

    # Vérification du binaire Tesseract
    tess_ok = True
    tess_error = None
    try:
        if pytesseract is None:
            tess_ok = False
            tess_error = "pytesseract non importable"
        else:
            # Appel simple qui échouera si tesseract n'est pas installé côté OS
            _ = pytesseract.get_tesseract_version()
    except Exception as e:
        tess_ok = False
        tess_error = str(e)

    if not tess_ok:
        missing.append(f"✗ tesseract (binaire système): requis - {tess_error}")
    else:
        installed.append("✓ tesseract (binaire système)")

    # Vérification de poppler pour pdf2image (indirecte)
    poppler_hint = "Installez 'poppler' (Linux: poppler-utils, macOS: brew install poppler) si vous traitez des PDF scannés."
    if convert_from_bytes is None:
        missing.append(f"✗ poppler/pdf2image: requis pour PDF scannés - {poppler_hint}")
    else:
        installed.append(f"✓ pdf2image présent - {poppler_hint}")

    return render_template('conversion/dependencies.html',
                           title="Vérification dépendances",
                           installed=installed,
                           missing=missing,
                           required_packages=REQUIRED_PACKAGES)
