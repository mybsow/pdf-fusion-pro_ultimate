"""
Moteur de traitement PDF (PDFEngine) - Version finale
"""

import io
import base64
import zipfile
from typing import List, Tuple, Optional
from pypdf import PdfReader, PdfWriter

try:
    from pypdf import Transformation
except ImportError:
    Transformation = None

class PDFEngine:
    """Moteur de traitement PDF avec méthodes statiques"""

    # ==========================
    # UTILITAIRES INTERNES
    # ==========================
    @staticmethod
    def _normalize_pages_input(pages_input: str, total_pages: int) -> Optional[List[int]]:
        """Normalise l'entrée des pages (all, range, selected)"""
        pages_input = (pages_input or "all").lower().strip()
        if pages_input == "all":
            return list(range(total_pages))
        try:
            pages_set = set()
            for part in pages_input.split(","):
                part = part.strip()
                if not part:
                    continue
                if "-" in part:
                    start, end = map(int, part.split("-", 1))
                    start = max(1, start)
                    end = min(end, total_pages)
                    pages_set.update(range(start, end+1))
                else:
                    page_num = int(part)
                    if 1 <= page_num <= total_pages:
                        pages_set.add(page_num)
            return sorted([p-1 for p in pages_set])
        except Exception:
            return None

    @staticmethod
    def _repair_pdf(pdf_bytes: bytes) -> PdfReader:
        """Tente de récupérer un PDF corrompu"""
        return PdfReader(io.BytesIO(pdf_bytes), strict=False)

    @staticmethod
    def _writer_to_bytes(writer: PdfWriter) -> bytes:
        """Convertit un PdfWriter en bytes"""
        buffer = io.BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    @staticmethod
    def _create_single_page_pdf(page) -> bytes:
        """Crée un PDF à partir d'une seule page"""
        writer = PdfWriter()
        writer.add_page(page)
        return PDFEngine._writer_to_bytes(writer)

    @staticmethod
    def rotate_page(page, angle: int):
        """Tourne une page PDF selon l'angle spécifié"""
        angle = int(angle) % 360
        if angle == 0:
            return page
        if hasattr(page, "rotate") and callable(page.rotate):
            try:
                page.rotate(angle)
                return page
            except Exception:
                pass
        for method_name in ["rotate_clockwise", "rotateClockwise"]:
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method(angle)
                    return page
                except Exception:
                    pass
        if Transformation:
            try:
                page.add_transformation(Transformation().rotate(angle))
                if hasattr(page, "flush"):
                    page.flush()
                return page
            except Exception:
                pass
        return page

    # ==========================
    # FONCTIONS PRINCIPALES
    # ==========================
    @staticmethod
    def merge(files_data: List[bytes]) -> Tuple[bytes, int]:
        """Fusionne plusieurs fichiers PDF en un seul"""
        writer = PdfWriter()
        total_pages = 0
        for pdf_data in files_data:
            try:
                reader = PdfReader(io.BytesIO(pdf_data))
            except Exception:
                reader = PDFEngine._repair_pdf(pdf_data)
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1
        return PDFEngine._writer_to_bytes(writer), total_pages

    @staticmethod
    def split(pdf_bytes: bytes, mode: str, arg: str = "") -> List[bytes]:
        """Divise un PDF selon différents modes"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception:
            reader = PDFEngine._repair_pdf(pdf_bytes)
        total_pages = len(reader.pages)
        if mode == "all":
            return [PDFEngine._create_single_page_pdf(reader.pages[i]) for i in range(total_pages)]
        elif mode == "range":
            output_files = []
            ranges = [r.strip() for r in arg.split(",") if r.strip()]
            for r in ranges:
                if "-" not in r:
                    continue
                try:
                    start, end = map(int, r.split("-", 1))
                    start = max(1, start) - 1
                    end = min(end, total_pages)
                    writer = PdfWriter()
                    for i in range(start, end):
                        writer.add_page(reader.pages[i])
                    output_files.append(PDFEngine._writer_to_bytes(writer))
                except Exception:
                    continue
            return output_files
        elif mode == "selected":
            writer = PdfWriter()
            for page_num in [n.strip() for n in arg.split(",") if n.strip()]:
                try:
                    idx = int(page_num) - 1
                    if 0 <= idx < total_pages:
                        writer.add_page(reader.pages[idx])
                except Exception:
                    continue
            return [PDFEngine._writer_to_bytes(writer)]
        return []

    @staticmethod
    def create_zip(files: List[bytes], zip_name: str = "pdf_split_results.zip") -> Tuple[bytes, str]:
        """Crée une archive ZIP contenant les fichiers PDF"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, pdf_data in enumerate(files):
                filename = f"pdf_page_{i+1:03d}.pdf"
                zip_file.writestr(filename, pdf_data)
        return buffer.getvalue(), zip_name

    @staticmethod
    def rotate(pdf_bytes: bytes, angle: int, pages_input: str) -> Tuple[bytes, int, int]:
        """Tourne les pages spécifiées d'un PDF"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception:
            reader = PDFEngine._repair_pdf(pdf_bytes)
        total_pages = len(reader.pages)
        pages_to_rotate = PDFEngine._normalize_pages_input(pages_input, total_pages)
        rotated_count = 0
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if pages_to_rotate is None or i in pages_to_rotate:
                PDFEngine.rotate_page(page, angle)
                rotated_count += 1
            writer.add_page(page)
        return PDFEngine._writer_to_bytes(writer), total_pages, rotated_count

    @staticmethod
    def compress(pdf_bytes: bytes) -> Tuple[bytes, int]:
        """Compresse un PDF"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception:
            reader = PDFEngine._repair_pdf(pdf_bytes)
        writer = PdfWriter()
        for page in reader.pages:
            try:
                page.compress_content_streams()
            except AttributeError:
                pass
            writer.add_page(page)
        return PDFEngine._writer_to_bytes(writer), len(reader.pages)

    @staticmethod
    def preview(pdf_bytes: bytes, max_pages: int = 3) -> Tuple[List[str], int]:
        """Génère des aperçus Base64 des premières pages"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
        except Exception:
            reader = PDFEngine._repair_pdf(pdf_bytes)
        total_pages = len(reader.pages)
        previews = []
        for i in range(min(max_pages, total_pages)):
            single_page_pdf = PDFEngine._create_single_page_pdf(reader.pages[i])
            previews.append(base64.b64encode(single_page_pdf).decode())
        return previews, total_pages
