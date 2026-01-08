"""
Moteur de traitement PDF
"""

import io
import base64
import zipfile
from typing import List, Tuple, Optional, Any
from PyPDF2 import PdfReader, PdfWriter

try:
    from PyPDF2 import Transformation
except ImportError:
    Transformation = None

class PDFEngine:
    """Moteur de traitement PDF avec méthodes statiques"""
    
    @staticmethod
    def _normalize_pages_input(pages_input: str, total_pages: int) -> Optional[List[int]]:
        """Normalise l'entrée des pages (all, range, selected)"""
        pages_input = pages_input.lower().strip()
        
        if pages_input == "all":
            return list(range(total_pages))
        
        try:
            pages_set = set()
            parts = [p.strip() for p in pages_input.split(",") if p.strip()]
            
            for part in parts:
                if "-" in part:
                    start_str, end_str = part.split("-", 1)
                    start = max(1, int(start_str))
                    end = min(int(end_str), total_pages)
                    pages_set.update(range(start, end + 1))
                else:
                    page_num = int(part)
                    if 1 <= page_num <= total_pages:
                        pages_set.add(page_num)
            
            return sorted([p - 1 for p in pages_set])  # Convertir en index 0-based
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def rotate_page(page, angle: int):
        """Tourne une page PDF selon l'angle spécifié"""
        angle = int(angle) % 360
        if angle == 0:
            return page
        
        # Tentative avec rotate() moderne
        if hasattr(page, "rotate") and callable(page.rotate):
            try:
                page.rotate(angle)
                return page
            except Exception:
                pass
        
        # Méthodes legacy
        rotate_methods = ["rotate_clockwise", "rotateClockwise"]
        for method_name in rotate_methods:
            method = getattr(page, method_name, None)
            if callable(method):
                try:
                    method(angle)
                    return page
                except Exception:
                    pass
        
        # Fallback avec Transformation
        if Transformation is not None:
            try:
                page.add_transformation(Transformation().rotate(angle))
                if hasattr(page, "flush"):
                    page.flush()
                return page
            except Exception:
                pass
        
        return page
    
    @staticmethod
    def merge(files_data: List[bytes]) -> Tuple[bytes, int]:
        """Fusionne plusieurs fichiers PDF en un seul"""
        writer = PdfWriter()
        total_pages = 0
        
        for pdf_data in files_data:
            reader = PdfReader(io.BytesIO(pdf_data))
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1
        
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue(), total_pages
    
    @staticmethod
    def split(pdf_bytes: bytes, mode: str, arg: str = "") -> List[bytes]:
        """Divise un PDF selon différents modes"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        
        if mode == "all":
            # Chaque page devient un PDF séparé
            return [
                PDFEngine._create_single_page_pdf(reader.pages[i])
                for i in range(total_pages)
            ]
        
        elif mode == "range":
            # Plages de pages
            output_files = []
            ranges = [r.strip() for r in arg.split(",") if r.strip()]
            
            for range_str in ranges:
                if "-" not in range_str:
                    continue
                
                try:
                    start_str, end_str = range_str.split("-", 1)
                    start = max(1, int(start_str)) - 1
                    end = min(int(end_str), total_pages)
                    
                    writer = PdfWriter()
                    for i in range(start, end):
                        writer.add_page(reader.pages[i])
                    
                    output_files.append(PDFEngine._writer_to_bytes(writer))
                except (ValueError, IndexError):
                    continue
            
            return output_files
        
        elif mode == "selected":
            # Pages spécifiques
            writer = PdfWriter()
            page_nums = [n.strip() for n in arg.split(",") if n.strip()]
            
            for page_num in page_nums:
                try:
                    idx = int(page_num) - 1
                    if 0 <= idx < total_pages:
                        writer.add_page(reader.pages[idx])
                except ValueError:
                    continue
            
            return [PDFEngine._writer_to_bytes(writer)]
        
        return []
    
    @staticmethod
    def _create_single_page_pdf(page) -> bytes:
        """Crée un PDF à partir d'une seule page"""
        writer = PdfWriter()
        writer.add_page(page)
        return PDFEngine._writer_to_bytes(writer)
    
    @staticmethod
    def _writer_to_bytes(writer: PdfWriter) -> bytes:
        """Convertit un PdfWriter en bytes"""
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    
    @staticmethod
    def rotate(pdf_bytes: bytes, angle: int, pages_input: str) -> Tuple[bytes, int, int]:
        """Tourne les pages spécifiées d'un PDF"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
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
        reader = PdfReader(io.BytesIO(pdf_bytes))
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
        """Génère des aperçus des premières pages"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        previews = []
        
        for i in range(min(max_pages, total_pages)):
            single_page_pdf = PDFEngine._create_single_page_pdf(reader.pages[i])
            previews.append(base64.b64encode(single_page_pdf).decode())
        
        return previews, total_pages
    
    @staticmethod
    def create_zip(files: List[bytes], zip_name: str = "pdf_split_results.zip") -> Tuple[bytes, str]:
        """Crée une archive ZIP contenant les fichiers PDF"""
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, pdf_data in enumerate(files):
                filename = f"pdf_page_{i+1:03d}.pdf"
                zip_file.writestr(filename, pdf_data)
        
        return buffer.getvalue(), zip_name