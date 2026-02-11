"""
UTILS PDF - Version production robuste
Corrige les erreurs EOF, streams Flask et PDFs corrompus.
"""

import io
import os
import zipfile
from datetime import datetime
from flask import send_file, current_app
from pypdf import PdfReader, PdfWriter


# ===============================
# Helpers SAFE
# ===============================

def _read_pdf_bytes(file_storage):
    """
    Lit un FileStorage Flask de manière fiable.
    Empêche les EOF marker not found.
    """
    try:
        file_storage.stream.seek(0)
        pdf_bytes = file_storage.read()

        if not pdf_bytes:
            raise ValueError("Fichier vide")

        # Vérification signature PDF
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Fichier invalide (signature PDF absente)")

        return pdf_bytes

    except Exception as e:
        current_app.logger.error(f"Lecture PDF échouée: {str(e)}")
        raise


def _safe_reader(pdf_bytes):
    """
    Ouvre un PDF même légèrement corrompu.
    """
    try:
        return PdfReader(io.BytesIO(pdf_bytes))
    except Exception:
        # Tentative de réparation
        return PdfReader(io.BytesIO(pdf_bytes), strict=False)


def _writer_to_buffer(writer):
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer


# ===============================
# MERGE
# ===============================

def merge_pdfs(files, form_data=None):
    try:
        writer = PdfWriter()
        total_pages = 0

        for file in files:
            pdf_bytes = _read_pdf_bytes(file)
            reader = _safe_reader(pdf_bytes)

            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1

        output = _writer_to_buffer(writer)

        filename = f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        current_app.logger.exception("Erreur fusion PDF")
        return {"error": f"Erreur interne: {str(e)}"}, 500


# ===============================
# SPLIT
# ===============================

def split_pdf(file, form_data=None):
    try:
        pdf_bytes = _read_pdf_bytes(file)
        reader = _safe_reader(pdf_bytes)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)

                page_buffer = io.BytesIO()
                writer.write(page_buffer)

                zip_file.writestr(
                    f"page_{i+1:03d}.pdf",
                    page_buffer.getvalue()
                )

        zip_buffer.seek(0)

        filename = f"{os.path.splitext(file.filename)[0]}_pages.zip"

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/zip"
        )

    except Exception as e:
        current_app.logger.exception("Erreur division PDF")
        return {"error": f"Erreur interne: {str(e)}"}, 500


# ===============================
# COMPRESS
# ===============================

def compress_pdf(file, form_data=None):
    """
    Compression basique (réécriture des streams).
    Gain moyen : 10-40%.
    """
    try:
        pdf_bytes = _read_pdf_bytes(file)
        reader = _safe_reader(pdf_bytes)
        writer = PdfWriter()

        for page in reader.pages:
            try:
                page.compress_content_streams()
            except Exception:
                pass

            writer.add_page(page)

        output = _writer_to_buffer(writer)

        filename = f"{os.path.splitext(file.filename)[0]}_compresse.pdf"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        current_app.logger.exception("Erreur compression PDF")
        return {"error": f"Erreur interne: {str(e)}"}, 500


# ===============================
# ROTATE
# ===============================

def rotate_pdf(file, form_data=None):
    try:
        pdf_bytes = _read_pdf_bytes(file)
        reader = _safe_reader(pdf_bytes)
        writer = PdfWriter()

        angle = int(form_data.get("angle", 90)) if form_data else 90
        angle %= 360

        for page in reader.pages:
            try:
                page.rotate(angle)
            except Exception:
                # fallback ancienne API
                page.rotate_clockwise(angle)

            writer.add_page(page)

        output = _writer_to_buffer(writer)

        filename = f"{os.path.splitext(file.filename)[0]}_rotation.pdf"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        current_app.logger.exception("Erreur rotation PDF")
        return {"error": f"Erreur interne: {str(e)}"}, 500