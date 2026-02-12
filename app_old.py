# ============================================================
# PDF Fusion Pro – Application Web Complète
# Version 6.1 – 2026
# Développé par MYBSOW
# ============================================================

import os
import io
import uuid
import base64
import json
import zipfile
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from flask import Flask, jsonify, request, render_template_string, Response, g
from werkzeug.middleware.proxy_fix import ProxyFix
from pypdf import PdfReader, PdfWriter

try:
    from pypdf import Transformation
except ImportError:
    Transformation = None

# ============================================================
# CONFIGURATION DE L'APPLICATION
# ============================================================

class AppConfig:
    """Configuration centralisée de l'application"""
    VERSION = "6.1-Material-Pro"
    NAME = "PDF Fusion Pro"
    DEVELOPER_NAME = "MYBSOW"
    DEVELOPER_EMAIL = "banousow@gmail.com"
    HOSTING = "Render Cloud Platform"
    DOMAIN = "pdf-fusion-pro-ultimate.onrender.com"
    
    # Paramètres de sécurité
    SECRET_KEY = os.environ.get("SECRET_KEY", str(uuid.uuid4()))
    MAX_CONTENT_SIZE = 50 * 1024 * 1024  # 50MB
    TEMP_FOLDER = Path("/tmp/pdf_fusion_pro")
    
    # AdSense
    ADSENSE_CLIENT_ID = "pub-8967416460526921"
    ADSENSE_PUBLISHER_ID = "ca-pub-8967416460526921"
    
    # Chemins
    STATS_FILE = "usage_stats.json"
    
    @classmethod
    def initialize(cls):
        """Initialise les répertoires nécessaires"""
        cls.TEMP_FOLDER.mkdir(exist_ok=True)

AppConfig.initialize()

# ============================================================
# GESTION DES STATISTIQUES
# ============================================================

class StatisticsManager:
    """Gestionnaire des statistiques d'utilisation"""
    
    def __init__(self):
        self.file_path = AppConfig.TEMP_FOLDER / AppConfig.STATS_FILE
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Charge les statistiques depuis le fichier JSON"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Initialisation des statistiques
        now = datetime.now().isoformat()
        return {
            "app_name": AppConfig.NAME,
            "version": AppConfig.VERSION,
            "total_operations": 0,
            "merges": 0,
            "splits": 0,
            "rotations": 0,
            "compressions": 0,
            "user_sessions": 0,
            "zip_downloads": 0,
            "previews": 0,
            "first_use": now,
            "last_use": now,
            "daily_stats": {},
            "monthly_stats": {},
        }
    
    def save(self):
        """Sauvegarde les statistiques dans le fichier JSON"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except IOError:
            pass
    
    def increment(self, operation: str):
        """Incrémente un compteur d'opération"""
        self.stats["total_operations"] += 1
        
        if operation in self.stats:
            self.stats[operation] += 1
        
        # Mise à jour de la date
        self.stats["last_use"] = datetime.now().isoformat()
        
        # Statistiques journalières
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][today] = {}
        self.stats["daily_stats"][today][operation] = \
            self.stats["daily_stats"][today].get(operation, 0) + 1
        
        self.save()
    
    def new_session(self):
        """Enregistre une nouvelle session utilisateur"""
        self.stats["user_sessions"] += 1
        self.save()

stats_manager = StatisticsManager()

# ============================================================
# MOTEUR PDF
# ============================================================

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

# ============================================================
# APPLICATION FLASK
# ============================================================

app = Flask(__name__)
app.secret_key = AppConfig.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_SIZE
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ============================================================
# MIDDLEWARE & SÉCURITÉ
# ============================================================

@app.before_request
def before_request():
    """Exécuté avant chaque requête"""
    if not request.cookies.get("session_id"):
        stats_manager.new_session()
        g._create_session_cookie = True

@app.after_request
def add_security_headers(response):
    """Ajoute les en-têtes de sécurité HTTP"""
    # Sécurité
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "fullscreen=(self)"
    
    # Cache
    if request.path.startswith("/static"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    # Cookie de session
    if getattr(g, "_create_session_cookie", False):
        response.set_cookie(
            "session_id",
            str(uuid.uuid4()),
            httponly=True,
            secure=request.is_secure,
            samesite="Lax",
            max_age=60 * 60 * 24 * 30,  # 30 jours
        )
    
    return response

# ============================================================
# TEMPLATES HTML
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta name="description" content="{{ description }}">
    
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={{ config.ADSENSE_PUBLISHER_ID }}" crossorigin="anonymous"></script>
    <script>
        window.__ads_initialized__ = window.__ads_initialized__ || false;
        if (!window.__ads_initialized__) {
            (adsbygoogle = window.adsbygoogle || []).push({
                google_ad_client: "{{ config.ADSENSE_PUBLISHER_ID }}",
                enable_page_level_ads: true
            });
            window.__ads_initialized__ = true;
        }
    </script>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #4361ee;
            --primary-dark: #3a0ca3;
            --secondary-color: #4cc9f0;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --light-color: #f8f9fa;
            --dark-color: #212529;
            --gray-color: #6c757d;
            --sidebar-width: 280px;
            --sidebar-collapsed: 70px;
            --border-radius: 12px;
            --shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
            --transition: all 0.3s ease;
        }
        
        [data-bs-theme="dark"] {
            --light-color: #1a1d20;
            --dark-color: #f8f9fa;
            --gray-color: #adb5bd;
            --shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: var(--dark-color);
            min-height: 100vh;
            transition: var(--transition);
        }
        
        [data-bs-theme="dark"] body {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        }
        
        /* CORRECTION 1: Header réduit */
        .main-header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            height: 60px; /* Réduit de 70px à 60px */
            display: flex;
            align-items: center;
            min-height: 60px;
        }
        
        [data-bs-theme="dark"] .main-header {
            background: rgba(26, 29, 32, 0.95);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .logo {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.3rem; /* Réduit de 1.5rem */
            color: var(--primary-color);
            text-decoration: none;
            margin-left: var(--sidebar-width);
            padding-left: 1rem;
            height: 60px;
            display: flex;
            align-items: center;
        }
        
        .header-actions {
            margin-left: auto;
            padding-right: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            height: 60px;
        }
        
        /* Layout */
        .app-container {
            display: flex;
            min-height: calc(100vh - 60px);
        }
        
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            z-index: 100;
            transition: var(--transition);
            padding-top: 60px; /* Ajusté pour nouveau header */
            box-shadow: var(--shadow);
        }
        
        [data-bs-theme="dark"] .sidebar {
            background: rgba(26, 29, 32, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .sidebar-header {
            padding: 1.5rem;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            display: none;
        }
        
        [data-bs-theme="dark"] .sidebar-header {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .sidebar-nav {
            padding: 1rem;
        }
        
        .sidebar-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: var(--border-radius);
            cursor: pointer;
            transition: var(--transition);
            color: var(--gray-color);
            text-decoration: none;
        }
        
        .sidebar-item:hover {
            background: rgba(67, 97, 238, 0.1);
            color: var(--primary-color);
            transform: translateX(5px);
        }
        
        .sidebar-item.active {
            background: var(--primary-color);
            color: white;
            box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
        }
        
        .sidebar-item .icon {
            font-size: 1.25rem;
            min-width: 24px;
        }
        
        .sidebar-item .label {
            font-weight: 500;
            white-space: nowrap;
        }
        
        /* CORRECTION 2: Sidebar de publicité gauche */
        .ads-left-sidebar {
            width: 280px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
            position: fixed;
            top: 60px; /* Ajusté pour nouveau header */
            left: var(--sidebar-width);
            height: calc(100vh - 60px);
            padding: 1rem;
            overflow-y: auto;
            box-shadow: var(--shadow);
            z-index: 99;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        [data-bs-theme="dark"] .ads-left-sidebar {
            background: rgba(26, 29, 32, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            margin-left: calc(var(--sidebar-width) + 280px); /* Sidebar + pub gauche */
            padding: 1rem;
            max-width: calc(100% - var(--sidebar-width) - 280px - 300px); /* Compter les 3 sidebars */
        }
        
        @media (max-width: 1400px) {
            .ads-left-sidebar {
                display: none;
            }
            
            .main-content {
                margin-left: var(--sidebar-width);
                max-width: calc(100% - var(--sidebar-width) - 300px);
            }
        }
        
        @media (max-width: 1200px) {
            .main-content {
                max-width: calc(100% - var(--sidebar-width));
                margin-right: 0;
            }
            
            .ads-sidebar {
                display: none;
            }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                width: var(--sidebar-collapsed);
                padding-top: 60px; /* Ajusté pour mobile */
            }
            
            .logo {
                margin-left: var(--sidebar-collapsed);
                font-size: 1.2rem;
            }
            
            .main-content {
                margin-left: var(--sidebar-collapsed);
                max-width: calc(100% - var(--sidebar-collapsed));
            }
            
            .ads-left-sidebar {
                display: none;
            }
            
            .sidebar-item {
                justify-content: center;
                padding: 1rem 0.5rem;
            }
            
            .sidebar-item .label {
                display: none;
            }
            
            .sidebar-item .icon {
                margin: 0;
            }
        }
        
        /* Navigation */
        .nav-links {
            display: flex;
            gap: 1.5rem;
            align-items: center;
        }
        
        .nav-links a {
            color: var(--gray-color);
            text-decoration: none;
            font-weight: 500;
            transition: var(--transition);
            position: relative;
        }
        
        .nav-links a:hover {
            color: var(--primary-color);
        }
        
        .nav-links a::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 0;
            width: 0;
            height: 2px;
            background: var(--primary-color);
            transition: var(--transition);
        }
        
        .nav-links a:hover::after {
            width: 100%;
        }
        
        /* CORRECTION 3: Hero Section optimisée (pub centrale supprimée) */
        .hero-section {
            padding: 2rem 0; /* Restauré le padding original */
            text-align: center;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .hero-title {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
            color: var(--gray-color);
            margin-bottom: 2rem; /* Restauré la marge */
            line-height: 1.6;
        }
        
        /* CORRECTION 4: Supprimer le container de pub centrale */
        .ad-container {
            display: none; /* Masquer complètement */
        }
        
        .ad-label {
            font-size: 0.75rem;
            color: var(--gray-color);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 0.5rem;
        }
        
        /* Tool Container */
        .tool-container {
            background: white;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            overflow: hidden;
            display: none;
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        }
        
        [data-bs-theme="dark"] .tool-container {
            background: var(--light-color);
        }
        
        .tool-container.active {
            display: block;
            opacity: 1;
            transform: translateY(0);
        }
        
        .tool-header {
            padding: 2rem 2rem 1rem;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        
        [data-bs-theme="dark"] .tool-header {
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .tool-header h3 {
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            margin: 0;
            color: var(--primary-color);
        }
        
        .tool-content {
            padding: 2rem;
        }
        
        /* Upload Zone */
        .upload-zone {
            border: 3px dashed #ddd;
            border-radius: var(--border-radius);
            padding: 3rem 2rem;
            text-align: center;
            cursor: pointer;
            transition: var(--transition);
            background: rgba(248, 249, 250, 0.5);
            margin-bottom: 2rem;
        }
        
        [data-bs-theme="dark"] .upload-zone {
            border-color: #444;
            background: rgba(26, 29, 32, 0.5);
        }
        
        .upload-zone:hover {
            border-color: var(--primary-color);
            background: rgba(67, 97, 238, 0.05);
        }
        
        .upload-zone.drag-over {
            border-color: var(--success-color);
            background: rgba(46, 204, 113, 0.1);
        }
        
        .upload-icon {
            font-size: 3rem;
            color: var(--primary-color);
            margin-bottom: 1rem;
        }
        
        .upload-text h4 {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--dark-color);
        }
        
        .upload-text p {
            color: var(--gray-color);
            margin-bottom: 0;
        }
        
        /* File List */
        .file-list {
            margin: 1.5rem 0;
        }
        
        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem;
            background: var(--light-color);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            transition: var(--transition);
        }
        
        .file-item:hover {
            transform: translateX(5px);
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex: 1;
        }
        
        .file-icon {
            color: var(--danger-color);
            font-size: 1.5rem;
        }
        
        .file-details h6 {
            margin: 0;
            font-weight: 600;
        }
        
        .file-details small {
            color: var(--gray-color);
        }
        
        .file-actions {
            display: flex;
            gap: 0.5rem;
        }
        
        /* Form Controls */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--dark-color);
        }
        
        .form-control, .form-select {
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            transition: var(--transition);
        }
        
        [data-bs-theme="dark"] .form-control,
        [data-bs-theme="dark"] .form-select {
            background: #2d2d44;
            border-color: #444;
            color: var(--dark-color);
        }
        
        .form-control:focus, .form-select:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.25rem rgba(67, 97, 238, 0.25);
        }
        
        /* Buttons */
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            transition: var(--transition);
            border: none;
            cursor: pointer;
        }
        
        .btn-primary {
            background: var(--primary-color);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(67, 97, 238, 0.3);
        }
        
        .btn-success {
            background: var(--success-color);
            color: white;
        }
        
        .btn-warning {
            background: var(--warning-color);
            color: white;
        }
        
        .btn-danger {
            background: var(--danger-color);
            color: white;
        }
        
        .btn-outline {
            background: transparent;
            border: 2px solid var(--primary-color);
            color: var(--primary-color);
        }
        
        .btn-outline:hover {
            background: var(--primary-color);
            color: white;
        }
        
        .action-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }
        
        /* Preview */
        .preview-container {
            margin-top: 2rem;
            padding: 1.5rem;
            background: var(--light-color);
            border-radius: var(--border-radius);
        }
        
        .preview-title {
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--primary-color);
        }
        
        .preview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .preview-item {
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }
        
        .preview-frame {
            width: 100%;
            height: 200px;
            border: none;
        }
        
        .preview-label {
            padding: 0.5rem;
            text-align: center;
            background: var(--light-color);
            font-size: 0.875rem;
            color: var(--gray-color);
        }
        
        /* Footer */
        .main-footer {
            background: rgba(255, 255, 255, 0.95);
            border-top: 1px solid rgba(0, 0, 0, 0.05);
            padding: 2rem 0;
            margin-top: 2rem;
            position: relative;
            z-index: 100;
        }
        
        [data-bs-theme="dark"] .main-footer {
            background: rgba(26, 29, 32, 0.95);
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .footer-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 2rem;
            margin-left: calc(var(--sidebar-width) + 280px);
            padding: 0 1rem;
        }
        
        @media (max-width: 1400px) {
            .footer-content {
                margin-left: var(--sidebar-width);
            }
        }
        
        @media (max-width: 768px) {
            .footer-content {
                margin-left: var(--sidebar-collapsed);
            }
        }
        
        .footer-logo {
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.25rem;
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .footer-info {
            color: var(--gray-color);
            font-size: 0.9rem;
            text-align: center;
        }
        
        .footer-info strong {
            color: var(--dark-color);
        }
        
        .footer-links {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
        }
        
        .footer-links a {
            color: var(--gray-color);
            text-decoration: none;
            transition: var(--transition);
        }
        
        .footer-links a:hover {
            color: var(--primary-color);
        }
        
        /* CORRECTION 5: Supprimer la pub du footer */
        .footer-ads {
            display: none;
        }
        
        /* Ads Sidebar (Right) */
        .ads-sidebar {
            width: 300px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-left: 1px solid rgba(0, 0, 0, 0.05);
            position: fixed;
            top: 60px; /* Ajusté pour nouveau header */
            right: 0;
            height: calc(100vh - 60px);
            padding: 1rem;
            overflow-y: auto;
            box-shadow: var(--shadow);
            z-index: 99;
        }
        
        [data-bs-theme="dark"] .ads-sidebar {
            background: rgba(26, 29, 32, 0.95);
            border-left: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .ad-sidebar-item {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: var(--light-color);
            border-radius: var(--border-radius);
        }
        
        /* Loader */
        .loader-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 2000;
            backdrop-filter: blur(5px);
        }
        
        .loader {
            background: white;
            padding: 2rem;
            border-radius: var(--border-radius);
            text-align: center;
            box-shadow: var(--shadow);
            min-width: 300px;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Toast Notifications */
        .toast-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 1000;
            max-width: 350px;
        }
        
        .toast {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        
        .toast.show {
            transform: translateX(0);
        }
        
        .toast-icon {
            font-size: 1.25rem;
        }
        
        .toast-success .toast-icon {
            color: var(--success-color);
        }
        
        .toast-error .toast-icon {
            color: var(--danger-color);
        }
        
        .toast-info .toast-icon {
            color: var(--primary-color);
        }
        
        .toast-content {
            flex: 1;
        }
        
        .toast-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .toast-message {
            color: var(--gray-color);
            font-size: 0.9rem;
        }
        
        .toast-close {
            background: none;
            border: none;
            color: var(--gray-color);
            cursor: pointer;
            padding: 0;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2rem;
            }
            
            .hero-subtitle {
                font-size: 1rem;
            }
            
            .action-buttons {
                flex-direction: column;
            }
            
            .footer-content {
                flex-direction: column;
                text-align: center;
            }
            
            .nav-links {
                flex-wrap: wrap;
                justify-content: center;
                gap: 1rem;
            }
        }
        
        /* Theme Toggle */
        .theme-toggle {
            background: none;
            border: none;
            color: var(--gray-color);
            cursor: pointer;
            font-size: 1.25rem;
            padding: 0.5rem;
            border-radius: 50%;
            transition: var(--transition);
        }
        
        .theme-toggle:hover {
            background: var(--light-color);
            color: var(--primary-color);
        }
        
        /* Mobile Menu Toggle */
        .mobile-menu-toggle {
            display: none;
            background: none;
            border: none;
            color: var(--gray-color);
            font-size: 1.5rem;
            cursor: pointer;
            margin-left: 1rem;
        }
        
        @media (max-width: 768px) {
            .mobile-menu-toggle {
                display: block;
            }
            
            .sidebar {
                transform: translateX(-100%);
            }
            
            .sidebar.open {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
                max-width: 100%;
            }
            
            .logo {
                margin-left: 0;
            }
            
            .footer-content {
                margin-left: 0;
            }
            
            .ads-sidebar {
                display: none;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="main-header">
        <button class="mobile-menu-toggle" id="mobileMenuToggle">
            <i class="fas fa-bars"></i>
        </button>
        
        <a href="/" class="logo">
            <i class="fas fa-file-pdf me-2"></i>{{ config.NAME }}
        </a>
        
        <div class="header-actions">
            <div class="nav-links d-none d-md-flex">
                <a href="/mentions-legales">Mentions</a>
                <a href="/politique-confidentialite">Confidentialité</a>
                <a href="/conditions-utilisation">Conditions</a>
                <a href="/contact">Contact</a>
                <a href="/a-propos">À propos</a>
            </div>
            
            <button class="theme-toggle" id="themeToggle">
                <i class="fas fa-moon"></i>
            </button>
            
            <div class="dropdown d-md-none">
                <button class="btn btn-outline dropdown-toggle" type="button" data-bs-toggle="dropdown">
                    <i class="fas fa-bars"></i>
                </button>
                <ul class="dropdown-menu">
                    <li><a class="dropdown-item" href="/mentions-legales">Mentions légales</a></li>
                    <li><a class="dropdown-item" href="/politique-confidentialite">Confidentialité</a></li>
                    <li><a class="dropdown-item" href="/conditions-utilisation">Conditions</a></li>
                    <li><a class="dropdown-item" href="/contact">Contact</a></li>
                    <li><a class="dropdown-item" href="/a-propos">À propos</a></li>
                </ul>
            </div>
        </div>
    </header>

    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h5 class="mb-0">Outils PDF</h5>
        </div>
        <div class="sidebar-nav">
            <a href="#" class="sidebar-item active" data-tool="merge">
                <i class="fas fa-object-group icon"></i>
                <span class="label">Fusionner PDF</span>
            </a>
            <a href="#" class="sidebar-item" data-tool="split">
                <i class="fas fa-cut icon"></i>
                <span class="label">Diviser PDF</span>
            </a>
            <a href="#" class="sidebar-item" data-tool="rotate">
                <i class="fas fa-sync-alt icon"></i>
                <span class="label">Tourner PDF</span>
            </a>
            <a href="#" class="sidebar-item" data-tool="compress">
                <i class="fas fa-compress-alt icon"></i>
                <span class="label">Compresser PDF</span>
            </a>
        </div>
    </div>

    <!-- CORRECTION: Sidebar de publicité gauche -->
    <div class="ads-left-sidebar" id="adsLeftSidebar">
        <!-- Publicité gauche sous les outils -->
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="1122334455"
                 data-ad-format="vertical"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
        
        <!-- Widget d'outils rapides -->
        <div class="ad-sidebar-item">
            <h6 class="mb-3"><i class="fas fa-bolt me-2"></i>Outils Rapides</h6>
            <div class="small">
                <p class="mb-2">Fusionnez jusqu'à 10 PDFs en un clic</p>
                <p class="mb-2">Divisez par pages ou plages</p>
                <p class="mb-2">Tournez à 90°, 180° ou 270°</p>
                <p class="mb-0">Compressez sans perte de qualité</p>
            </div>
        </div>
        
        <!-- Deuxième pub verticale -->
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="5544332211"
                 data-ad-format="vertical"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Hero Section -->
        <section class="hero-section">
            <h1 class="hero-title">Transformez vos PDFs en toute simplicité</h1>
            <p class="hero-subtitle">
                Outil PDF tout-en-un : fusion, division, rotation et compression. Rapide, sécurisé et 100% gratuit.
                <br>Aucune inscription requise – vos fichiers ne quittent jamais votre navigateur.
            </p>
            
            <!-- SUPPRESSION COMPLÈTE: Pub centrale supprimée -->
        </section>

        <!-- Tool Containers -->
        <div class="tool-container active" id="mergeTool">
            <div class="tool-header">
                <h3><i class="fas fa-object-group me-2"></i>Fusionner des fichiers PDF</h3>
                <p class="text-muted mb-0">Combine plusieurs PDF en un seul document organisé</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="mergeUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Glissez-déposez vos fichiers PDF</h4>
                        <p>ou cliquez pour sélectionner (max 10 fichiers, 50MB chacun)</p>
                    </div>
                    <input type="file" id="mergeFileInput" accept=".pdf" multiple style="display: none;">
                </div>
                
                <div class="file-list" id="mergeFileList"></div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processMerge()" id="mergeButton" disabled>
                        <i class="fas fa-magic me-2"></i>Fusionner les PDFs
                    </button>
                    <button class="btn btn-outline" onclick="clearMergeFiles()">
                        <i class="fas fa-trash me-2"></i>Effacer la liste
                    </button>
                </div>
            </div>
        </div>

        <div class="tool-container" id="splitTool">
            <div class="tool-header">
                <h3><i class="fas fa-cut me-2"></i>Diviser un fichier PDF</h3>
                <p class="text-muted mb-0">Extrayez des pages spécifiques ou divisez par plages</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="splitUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Sélectionnez un fichier PDF à diviser</h4>
                        <p>Glissez-déposez ou cliquez pour choisir</p>
                    </div>
                    <input type="file" id="splitFileInput" accept=".pdf" style="display: none;">
                </div>
                
                <div class="file-list" id="splitFileInfo"></div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label">Mode de division</label>
                            <select class="form-select" id="splitMode">
                                <option value="all">Chaque page séparément</option>
                                <option value="range">Plages de pages (ex: 1-3,5-7)</option>
                                <option value="selected">Pages spécifiques (ex: 1,4,8)</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label" id="splitArgLabel">Argument</label>
                            <input type="text" class="form-control" id="splitArg" 
                                   placeholder="Ex: 1-3, 5-7 ou 1,4,8">
                            <small class="text-muted" id="splitHelpText">
                                Laissez vide pour diviser toutes les pages
                            </small>
                        </div>
                    </div>
                </div>
                
                <div class="preview-container" id="splitPreview" style="display: none;">
                    <h5 class="preview-title"><i class="fas fa-eye me-2"></i>Aperçu des pages</h5>
                    <div class="preview-grid" id="splitPreviewGrid"></div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processSplit()" id="splitButton" disabled>
                        <i class="fas fa-cut me-2"></i>Diviser le PDF
                    </button>
                    <button class="btn btn-success" onclick="processSplitZip()" id="splitZipButton" disabled>
                        <i class="fas fa-file-archive me-2"></i>Télécharger en ZIP
                    </button>
                    <button class="btn btn-outline" onclick="generatePreview()" id="previewButton" disabled>
                        <i class="fas fa-eye me-2"></i>Aperçu
                    </button>
                </div>
            </div>
        </div>

        <div class="tool-container" id="rotateTool">
            <div class="tool-header">
                <h3><i class="fas fa-sync-alt me-2"></i>Tourner un fichier PDF</h3>
                <p class="text-muted mb-0">Faites pivoter des pages spécifiques ou l'ensemble du document</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="rotateUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Sélectionnez un fichier PDF à tourner</h4>
                        <p>Glissez-déposez ou cliquez pour choisir</p>
                    </div>
                    <input type="file" id="rotateFileInput" accept=".pdf" style="display: none;">
                </div>
                
                <div class="file-list" id="rotateFileInfo"></div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label">Pages à tourner</label>
                            <input type="text" class="form-control" id="rotatePages" 
                                   placeholder="Ex: 1,3-5 ou laissez 'all' pour toutes">
                            <small class="text-muted">
                                Format: numéros séparés par des virgules, plages avec tiret
                            </small>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="form-group">
                            <label class="form-label">Angle de rotation</label>
                            <select class="form-select" id="rotateAngle">
                                <option value="90">90° (Sens horaire)</option>
                                <option value="180">180° (Demi-tour)</option>
                                <option value="270">270° (Sens anti-horaire)</option>
                                <option value="-90">-90° (Sens anti-horaire)</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processRotate()" id="rotateButton" disabled>
                        <i class="fas fa-sync-alt me-2"></i>Tourner le PDF
                    </button>
                    <button class="btn btn-outline" onclick="resetRotateForm()">
                        <i class="fas fa-redo me-2"></i>Réinitialiser
                    </button>
                </div>
            </div>
        </div>

        <div class="tool-container" id="compressTool">
            <div class="tool-header">
                <h3><i class="fas fa-compress-alt me-2"></i>Compresser un fichier PDF</h3>
                <p class="text-muted mb-0">Réduisez la taille de vos PDFs sans perte de qualité notable</p>
            </div>
            <div class="tool-content">
                <div class="upload-zone" id="compressUploadZone">
                    <div class="upload-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <div class="upload-text">
                        <h4>Sélectionnez un fichier PDF à compresser</h4>
                        <p>Glissez-déposez ou cliquez pour choisir</p>
                    </div>
                    <input type="file" id="compressFileInput" accept=".pdf" style="display: none;">
                </div>
                
                <div class="file-list" id="compressFileInfo"></div>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    La compression réduit la taille du fichier en optimisant les images et en supprimant les métadonnées inutiles.
                    La qualité visuelle reste excellente pour la plupart des usages.
                </div>
                
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="processCompress()" id="compressButton" disabled>
                        <i class="fas fa-compress-alt me-2"></i>Compresser le PDF
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Ads Sidebar (Right) -->
    <div class="ads-sidebar">
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="9876543210"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
        
        <div class="ad-sidebar-item">
            <div class="ad-label">Publicité</div>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="{{ config.ADSENSE_PUBLISHER_ID }}"
                 data-ad-slot="8765432109"
                 data-ad-format="vertical"
                 data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
        
        <!-- Stats Widget -->
        <div class="ad-sidebar-item">
            <h6 class="mb-3"><i class="fas fa-chart-bar me-2"></i>Statistiques</h6>
            <div class="small">
                <div class="d-flex justify-content-between mb-2">
                    <span>Opérations totales:</span>
                    <span id="totalOps">0</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Fusions:</span>
                    <span id="mergeCount">0</span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span>Divisions:</span>
                    <span id="splitCount">0</span>
                </div>
                <div class="d-flex justify-content-between">
                    <span>Rotations:</span>
                    <span id="rotateCount">0</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="main-footer">
        <div class="container-fluid">
            <div class="footer-content">
                <a href="/" class="footer-logo">
                    <i class="fas fa-file-pdf me-2"></i>{{ config.NAME }}
                </a>
                
                <div class="footer-info">
                    <div>© {{ current_year }} {{ config.NAME }} • Version {{ config.VERSION }}</div>
                    <div class="mt-1">Développé par <strong>{{ config.DEVELOPER_NAME }}</strong> • {{ config.DEVELOPER_EMAIL }}</div>
                    <div class="mt-1">Hébergé sur <strong>{{ config.HOSTING }}</strong> • {{ config.DOMAIN }}</div>
                </div>
                
                <div class="footer-links">
                    <a href="/mentions-legales">Mentions légales</a>
                    <a href="/politique-confidentialite">Confidentialité</a>
                    <a href="/conditions-utilisation">Conditions</a>
                    <a href="/contact">Contact</a>
                    <a href="/a-propos">À propos</a>
                </div>
            </div>
        </div>
    </footer>

    <!-- Loader Overlay -->
    <div class="loader-overlay" id="loaderOverlay">
        <div class="loader">
            <div class="spinner"></div>
            <h4>Traitement en cours</h4>
            <p class="text-muted" id="loaderMessage">Veuillez patienter...</p>
        </div>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Configuration
        const CONFIG = {
            APP_NAME: "{{ config.NAME }}",
            VERSION: "{{ config.VERSION }}",
            DEVELOPER_NAME: "{{ config.DEVELOPER_NAME }}",
            DEVELOPER_EMAIL: "{{ config.DEVELOPER_EMAIL }}",
            HOSTING: "{{ config.HOSTING }}",
            DOMAIN: "{{ config.DOMAIN }}"
        };

        // State Management
        let state = {
            activeTool: 'merge',
            files: {
                merge: [],
                split: null,
                rotate: null,
                compress: null
            }
        };

        // DOM Elements
        const elements = {
            sidebarItems: document.querySelectorAll('.sidebar-item'),
            toolContainers: document.querySelectorAll('.tool-container'),
            themeToggle: document.getElementById('themeToggle'),
            mobileMenuToggle: document.getElementById('mobileMenuToggle'),
            sidebar: document.getElementById('sidebar'),
            loaderOverlay: document.getElementById('loaderOverlay'),
            loaderMessage: document.getElementById('loaderMessage'),
            toastContainer: document.getElementById('toastContainer'),
            stats: {
                totalOps: document.getElementById('totalOps'),
                mergeCount: document.getElementById('mergeCount'),
                splitCount: document.getElementById('splitCount'),
                rotateCount: document.getElementById('rotateCount')
            }
        };

        // Initialize Application
        document.addEventListener('DOMContentLoaded', function() {
            initTheme();
            initSidebar();
            initFileUploads();
            initStats();
            loadStats();
            optimizeAds();
        });

        // Theme Management
        function initTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
            updateThemeIcon(savedTheme);
            
            elements.themeToggle.addEventListener('click', toggleTheme);
        }

        function toggleTheme() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        }

        function updateThemeIcon(theme) {
            elements.themeToggle.innerHTML = theme === 'light' 
                ? '<i class="fas fa-moon"></i>' 
                : '<i class="fas fa-sun"></i>';
        }

        // Sidebar Management
        function initSidebar() {
            elements.sidebarItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    const tool = item.dataset.tool;
                    switchTool(tool);
                    
                    // Close mobile menu if open
                    if (window.innerWidth <= 768) {
                        elements.sidebar.classList.remove('open');
                    }
                });
            });

            // Mobile menu toggle
            elements.mobileMenuToggle.addEventListener('click', () => {
                elements.sidebar.classList.toggle('open');
            });

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (window.innerWidth <= 768 && 
                    !elements.sidebar.contains(e.target) && 
                    !elements.mobileMenuToggle.contains(e.target)) {
                    elements.sidebar.classList.remove('open');
                }
            });
        }

        function switchTool(tool) {
            // Update active sidebar item
            elements.sidebarItems.forEach(item => {
                item.classList.toggle('active', item.dataset.tool === tool);
            });

            // Update active container
            elements.toolContainers.forEach(container => {
                container.classList.toggle('active', container.id === `${tool}Tool`);
            });

            state.activeTool = tool;
        }

        // File Upload Management
        function initFileUploads() {
            // Merge Tool
            initUploadZone('merge', true);
            // Split Tool
            initUploadZone('split', false);
            // Rotate Tool
            initUploadZone('rotate', false);
            // Compress Tool
            initUploadZone('compress', false);

            // Split mode change handler
            document.getElementById('splitMode').addEventListener('change', updateSplitMode);
        }

        function initUploadZone(tool, multiple) {
            const zone = document.getElementById(`${tool}UploadZone`);
            const input = document.getElementById(`${tool}FileInput`);
            
            if (!zone || !input) return;

            // Click handler
            zone.addEventListener('click', () => input.click());

            // File input change handler
            input.addEventListener('change', (e) => handleFileSelect(tool, e.target.files, multiple));

            // Drag and drop handlers
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.add('drag-over'), false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.remove('drag-over'), false);
            });

            zone.addEventListener('drop', (e) => {
                handleFileSelect(tool, e.dataTransfer.files, multiple);
            }, false);
        }

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        function handleFileSelect(tool, files, multiple) {
            if (!files || files.length === 0) return;

            if (multiple) {
                // Add files to array
                const newFiles = Array.from(files).filter(file => 
                    file.type === 'application/pdf' && file.size <= 50 * 1024 * 1024
                );
                
                if (newFiles.length === 0) {
                    showToast('error', 'Format invalide', 'Seuls les fichiers PDF de moins de 50MB sont acceptés.');
                    return;
                }

                state.files[tool].push(...newFiles);
                if (state.files[tool].length > 10) {
                    state.files[tool] = state.files[tool].slice(0, 10);
                    showToast('warning', 'Limite atteinte', 'Maximum 10 fichiers autorisés.');
                }

                updateFileList(tool);
                updateMergeButton();
            } else {
                // Single file
                const file = files[0];
                
                if (file.type !== 'application/pdf') {
                    showToast('error', 'Format invalide', 'Veuillez sélectionner un fichier PDF.');
                    return;
                }

                if (file.size > 50 * 1024 * 1024) {
                    showToast('error', 'Fichier trop volumineux', 'La taille maximale est de 50MB.');
                    return;
                }

                state.files[tool] = file;
                updateFileInfo(tool);
                updateToolButton(tool);
                
                if (tool === 'split') {
                    document.getElementById('previewButton').disabled = false;
                }
            }
        }

        function updateFileList(tool) {
            const container = document.getElementById(`${tool}FileList`);
            if (!container) return;

            if (state.files[tool].length === 0) {
                container.innerHTML = '';
                return;
            }

            container.innerHTML = state.files[tool].map((file, index) => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-icon">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <div class="file-details">
                            <h6>${escapeHtml(file.name)}</h6>
                            <small>${formatFileSize(file.size)}</small>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline" onclick="removeFile('${tool}', ${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function updateFileInfo(tool) {
            const container = document.getElementById(`${tool}FileInfo`);
            if (!container || !state.files[tool]) {
                container.innerHTML = '';
                return;
            }

            const file = state.files[tool];
            container.innerHTML = `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-icon">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <div class="file-details">
                            <h6>${escapeHtml(file.name)}</h6>
                            <small>${formatFileSize(file.size)} • ${new Date(file.lastModified).toLocaleDateString()}</small>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-outline" onclick="clearFile('${tool}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        }

        function removeFile(tool, index) {
            state.files[tool].splice(index, 1);
            updateFileList(tool);
            updateMergeButton();
        }

        function clearFile(tool) {
            state.files[tool] = tool === 'merge' ? [] : null;
            if (tool === 'merge') {
                updateFileList(tool);
                updateMergeButton();
            } else {
                updateFileInfo(tool);
                updateToolButton(tool);
                if (tool === 'split') {
                    hideSplitPreview();
                    document.getElementById('previewButton').disabled = true;
                }
            }
        }

        function clearMergeFiles() {
            state.files.merge = [];
            updateFileList('merge');
            updateMergeButton();
        }

        function resetRotateForm() {
            document.getElementById('rotatePages').value = '';
            document.getElementById('rotateAngle').value = '90';
            clearFile('rotate');
        }

        // Button States
        function updateMergeButton() {
            const button = document.getElementById('mergeButton');
            button.disabled = state.files.merge.length === 0;
        }

        function updateToolButton(tool) {
            const button = document.getElementById(`${tool}Button`);
            if (button) {
                button.disabled = !state.files[tool];
            }
            
            if (tool === 'split') {
                const zipButton = document.getElementById('splitZipButton');
                if (zipButton) {
                    zipButton.disabled = !state.files[tool];
                }
            }
        }

        // Split Mode Handling
        function updateSplitMode() {
            const mode = document.getElementById('splitMode').value;
            const argLabel = document.getElementById('splitArgLabel');
            const argInput = document.getElementById('splitArg');
            const helpText = document.getElementById('splitHelpText');

            switch (mode) {
                case 'all':
                    argLabel.textContent = 'Argument (optionnel)';
                    argInput.placeholder = 'Laissez vide pour toutes les pages';
                    helpText.textContent = 'Laissez vide pour diviser toutes les pages';
                    argInput.disabled = false;
                    break;
                case 'range':
                    argLabel.textContent = 'Plages de pages';
                    argInput.placeholder = 'Ex: 1-3, 5-7, 10-12';
                    helpText.textContent = 'Séparez les plages par des virgules (ex: 1-3,5-7)';
                    argInput.disabled = false;
                    break;
                case 'selected':
                    argLabel.textContent = 'Pages spécifiques';
                    argInput.placeholder = 'Ex: 1, 4, 8, 12';
                    helpText.textContent = 'Séparez les numéros de page par des virgules';
                    argInput.disabled = false;
                    break;
            }
        }

        // Stats Management
        function initStats() {
            // Load initial stats
            loadStats();
            
            // Refresh stats every 30 seconds
            setInterval(loadStats, 30000);
        }

        async function loadStats() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                // Update stats display
                if (elements.stats.totalOps) {
                    elements.stats.totalOps.textContent = data.total_operations || '0';
                }
                if (elements.stats.mergeCount) {
                    elements.stats.mergeCount.textContent = data.merges || '0';
                }
                if (elements.stats.splitCount) {
                    elements.stats.splitCount.textContent = data.splits || '0';
                }
                if (elements.stats.rotateCount) {
                    elements.stats.rotateCount.textContent = data.rotations || '0';
                }
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }

        // Preview Generation
        async function generatePreview() {
            if (!state.files.split) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Génération de l\\'aperçu...');

            try {
                const base64 = await fileToBase64(state.files.split);
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 }
                    })
                });

                const result = await response.json();

                if (result.success) {
                    displayPreview(result.previews, result.total_pages);
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la génération de l\\'aperçu');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de générer l\\'aperçu');
                console.error('Preview error:', error);
            } finally {
                hideLoader();
            }
        }

        function displayPreview(previews, totalPages) {
            const container = document.getElementById('splitPreview');
            const grid = document.getElementById('splitPreviewGrid');

            if (!previews || previews.length === 0) {
                container.style.display = 'none';
                return;
            }

            grid.innerHTML = previews.map((preview, index) => `
                <div class="preview-item">
                    <iframe class="preview-frame" 
                            src="data:application/pdf;base64,${preview}">
                    </iframe>
                    <div class="preview-label">Page ${index + 1} / ${totalPages}</div>
                </div>
            `).join('');

            container.style.display = 'block';
        }

        function hideSplitPreview() {
            const container = document.getElementById('splitPreview');
            container.style.display = 'none';
        }

        // File Processing Functions
        async function processMerge() {
            if (state.files.merge.length === 0) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner au moins un fichier PDF.');
                return;
            }

            showLoader('Fusion des fichiers PDF...');

            try {
                const filesData = await Promise.all(
                    state.files.merge.map(async file => ({
                        data: await fileToBase64(file)
                    }))
                );

                const response = await fetch('/api/merge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ files: filesData })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/pdf');
                    showToast('success', 'Succès', `${result.pages} pages fusionnées avec succès`);
                    loadStats(); // Refresh stats
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la fusion');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de fusionner les fichiers');
                console.error('Merge error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processSplit() {
            if (!state.files.split) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Division du fichier PDF...');

            try {
                const base64 = await fileToBase64(state.files.split);
                const mode = document.getElementById('splitMode').value;
                const arg = document.getElementById('splitArg').value;

                const response = await fetch('/api/split', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 },
                        mode: mode,
                        arg: arg
                    })
                });

                const result = await response.json();

                if (result.success) {
                    if (result.files.length === 0) {
                        showToast('warning', 'Aucun résultat', 'Aucune page ne correspond aux critères de division');
                    } else {
                        // Download all files
                        result.files.forEach(file => {
                            downloadFile(file.data, file.filename, 'application/pdf');
                        });
                        showToast('success', 'Succès', `${result.count} fichiers générés avec succès`);
                        loadStats(); // Refresh stats
                    }
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la division');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de diviser le fichier');
                console.error('Split error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processSplitZip() {
            if (!state.files.split) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Création de l\\'archive ZIP...');

            try {
                const base64 = await fileToBase64(state.files.split);
                const mode = document.getElementById('splitMode').value;
                const arg = document.getElementById('splitArg').value;

                const response = await fetch('/api/split_zip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 },
                        mode: mode,
                        arg: arg
                    })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/zip');
                    showToast('success', 'Succès', `Archive ZIP avec ${result.count} fichiers créée`);
                    loadStats(); // Refresh stats
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la création du ZIP');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de créer l\\'archive ZIP');
                console.error('Split ZIP error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processRotate() {
            if (!state.files.rotate) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            const pages = document.getElementById('rotatePages').value.trim() || 'all';
            const angle = document.getElementById('rotateAngle').value;

            if (pages !== 'all' && !/^[\\d,\\-\\s]+$/.test(pages)) {
                showToast('error', 'Format invalide', 'Format des pages invalide. Utilisez: all, 1,3-5, ou 1,4,8');
                return;
            }

            showLoader('Rotation des pages PDF...');

            try {
                const base64 = await fileToBase64(state.files.rotate);

                const response = await fetch('/api/rotate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 },
                        pages: pages,
                        angle: parseInt(angle)
                    })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/pdf');
                    showToast('success', 'Succès', `${result.rotated} pages tournées sur ${result.pages} totales`);
                    loadStats(); // Refresh stats
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la rotation');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de tourner le fichier');
                console.error('Rotate error:', error);
            } finally {
                hideLoader();
            }
        }

        async function processCompress() {
            if (!state.files.compress) {
                showToast('error', 'Aucun fichier', 'Veuillez sélectionner un fichier PDF.');
                return;
            }

            showLoader('Compression du fichier PDF...');

            try {
                const base64 = await fileToBase64(state.files.compress);

                const response = await fetch('/api/compress', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file: { data: base64 }
                    })
                });

                const result = await response.json();

                if (result.success) {
                    downloadFile(result.data, result.filename, 'application/pdf');
                    showToast('success', 'Succès', `Fichier compressé avec ${result.pages} pages`);
                    loadStats(); // Refresh stats
                } else {
                    showToast('error', 'Erreur', result.error || 'Erreur lors de la compression');
                }
            } catch (error) {
                showToast('error', 'Erreur', 'Impossible de compresser le fichier');
                console.error('Compress error:', error);
            } finally {
                hideLoader();
            }
        }

        // Utility Functions
        function fileToBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => {
                    const base64 = reader.result.split(',')[1];
                    resolve(base64);
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        }

        function downloadFile(base64, filename, mimeType) {
            const link = document.createElement('a');
            link.href = `data:${mimeType};base64,${base64}`;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // UI Helpers
        function showLoader(message = 'Traitement en cours...') {
            elements.loaderMessage.textContent = message;
            elements.loaderOverlay.style.display = 'flex';
        }

        function hideLoader() {
            elements.loaderOverlay.style.display = 'none';
        }

        function showToast(type, title, message) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            const icons = {
                success: 'fas fa-check-circle',
                error: 'fas fa-exclamation-circle',
                warning: 'fas fa-exclamation-triangle',
                info: 'fas fa-info-circle'
            };

            toast.innerHTML = `
                <div class="toast-icon">
                    <i class="${icons[type]}"></i>
                </div>
                <div class="toast-content">
                    <div class="toast-title">${escapeHtml(title)}</div>
                    <div class="toast-message">${escapeHtml(message)}</div>
                </div>
                <button class="toast-close" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;

            elements.toastContainer.appendChild(toast);

            // Animate in
            setTimeout(() => toast.classList.add('show'), 10);

            // Auto remove after 5 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 5000);
        }

        // Optimiser le chargement des publicités
        function optimizeAds() {
            // Attendre que le DOM soit chargé
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initAds);
            } else {
                initAds();
            }
        }

        function initAds() {
            // Charger les pubs avec un léger délai pour améliorer les performances
            setTimeout(() => {
                const ads = document.querySelectorAll('.adsbygoogle');
                ads.forEach(ad => {
                    try {
                        if (!ad.getAttribute('data-adsbygoogle-status')) {
                            (adsbygoogle = window.adsbygoogle || []).push({});
                        }
                    } catch (e) {
                        console.log('Erreur de chargement pub:', e);
                    }
                });
            }, 1000);
        }

        // Global functions for onclick handlers
        window.processMerge = processMerge;
        window.processSplit = processSplit;
        window.processSplitZip = processSplitZip;
        window.processRotate = processRotate;
        window.processCompress = processCompress;
        window.clearMergeFiles = clearMergeFiles;
        window.resetRotateForm = resetRotateForm;
        window.generatePreview = generatePreview;
        window.removeFile = removeFile;
        window.clearFile = clearFile;
    </script>
</body>
</html>
"""

LEGAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | {{ config.NAME }}</title>
    
    <!-- Bootstrap 5.3 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-color: #4361ee;
            --secondary-color: #3a0ca3;
            --accent-color: #4cc9f0;
            --light-color: #f8f9fa;
            --dark-color: #212529;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
        }
        
        [data-bs-theme="dark"] {
            --light-color: #1a1d20;
            --dark-color: #f8f9fa;
            --gray-color: #adb5bd;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            color: var(--dark-color);
        }
        
        [data-bs-theme="dark"] body {
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        }
        
        .legal-container {
            max-width: 900px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            margin: 2rem auto;
        }
        
        [data-bs-theme="dark"] .legal-container {
            background: var(--light-color);
        }
        
        .legal-header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 2.5rem;
        }
        
        .legal-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 0.5rem 1.5rem;
            border-radius: 50px;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        .legal-content {
            padding: 2.5rem;
            line-height: 1.8;
        }
        
        .legal-content h2 {
            color: var(--secondary-color);
            font-weight: 700;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--light-color);
        }
        
        .legal-content h3 {
            color: var(--primary-color);
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }
        
        .legal-footer {
            background: var(--light-color);
            padding: 1.5rem 2.5rem;
            border-top: 1px solid rgba(0, 0, 0, 0.05);
            font-size: 0.9rem;
        }
        
        [data-bs-theme="dark"] .legal-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .nav-links a {
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            margin: 0 0.75rem;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: white;
        }
        
        .info-box {
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
            border-left: 4px solid var(--primary-color);
            padding: 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
        }
        
        [data-bs-theme="dark"] .info-box {
            background: linear-gradient(135deg, #2d3748, #4a5568);
        }
        
        .contact-info {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .contact-icon {
            width: 50px;
            height: 50px;
            background: var(--primary-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.25rem;
        }
        
        @media (max-width: 768px) {
            .legal-container {
                margin: 1rem;
                border-radius: 15px;
            }
            
            .legal-header, .legal-content {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="legal-container">
        <div class="legal-header">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <a href="/" class="text-white text-decoration-none">
                    <i class="fas fa-file-pdf fa-lg me-2"></i>
                    <span class="fw-bold">{{ config.NAME }}</span>
                </a>
                <div class="nav-links d-none d-md-block">
                    <a href="/"><i class="fas fa-home me-1"></i> Accueil</a>
                    <a href="/mentions-legales">Mentions</a>
                    <a href="/politique-confidentialite">Confidentialité</a>
                    <a href="/conditions-utilisation">Conditions</a>
                    <a href="/contact">Contact</a>
                </div>
            </div>
            <div class="legal-badge">{{ badge }}</div>
            <h1 class="display-6 fw-bold">{{ title }}</h1>
            <p class="opacity-90">{{ subtitle }}</p>
        </div>
        
        <div class="legal-content">
            {{ content|safe }}
        </div>
        
        <div class="legal-footer">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <p class="mb-0">
                        <i class="fas fa-copyright me-1"></i> {{ current_year }} {{ config.NAME }} 
                        • Développé par <strong>{{ config.DEVELOPER_NAME }}</strong> 
                        • Version {{ config.VERSION }}
                    </p>
                    <p class="mb-0 text-muted small mt-1">
                        <i class="fas fa-envelope me-1"></i> {{ config.DEVELOPER_EMAIL }}
                        • Hébergé sur <strong>{{ config.HOSTING }}</strong> • {{ config.DOMAIN }}
                    </p>
                </div>
                <div class="col-md-4 text-md-end mt-2 mt-md-0">
                    <a href="/" class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-arrow-left me-1"></i> Retour à l'accueil
                    </a>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Thème sombre/clair automatique
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-bs-theme', 'dark');
        }
    </script>
</body>
</html>
"""

# ============================================================
# VÉRIFICATION GOOGLE & ADS.TXT
# ============================================================

@app.route('/google6f0d847067bbd18a.html')
def google_verification():
    """Page de vérification Google Search Console"""
    verification_content = "google-site-verification: google6f0d847067bbd18a.html"
    return Response(verification_content, mimetype='text/html')

@app.route('/ads.txt')
def ads_txt():
    """Fichier ads.txt pour AdSense"""
    ads_content = "google.com, pub-8967416460526921, DIRECT, f08c47fec0942fa0"
    return Response(ads_content, mimetype='text/plain')

# ============================================================
# API ENDPOINTS (inchangés - garder votre code existant)
# ============================================================

@app.route("/api/merge", methods=["POST"])
def api_merge():
    """API pour fusionner des PDFs"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "files" not in data:
            return jsonify({"error": "Aucun fichier reçu"}), 400
        
        files_b64 = data["files"]
        if not isinstance(files_b64, list):
            return jsonify({"error": "Format de fichiers invalide"}), 400
        
        # Décodage des PDFs
        pdfs = []
        for file_data in files_b64:
            if "data" in file_data:
                try:
                    pdfs.append(base64.b64decode(file_data["data"]))
                except (base64.binascii.Error, TypeError):
                    return jsonify({"error": "Format Base64 invalide"}), 400
        
        if not pdfs:
            return jsonify({"error": "Aucun PDF valide fourni"}), 400
        
        # Fusion
        merged_pdf, page_count = PDFEngine.merge(pdfs)
        stats_manager.increment("merges")
        
        return jsonify({
            "success": True,
            "filename": f"fusion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(merged_pdf).decode()
        })
    
    except Exception as e:
        app.logger.error(f"Erreur lors de la fusion: {str(e)}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route("/api/split", methods=["POST"])
def api_split():
    """API pour diviser un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        # Division
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        
        # Préparation des résultats
        result_files = []
        for i, pdf_data in enumerate(split_files):
            result_files.append({
                "filename": f"split_{i+1:03d}.pdf",
                "data": base64.b64encode(pdf_data).decode()
            })
        
        return jsonify({
            "success": True,
            "count": len(split_files),
            "files": result_files
        })
    
    except Exception as e:
        app.logger.error(f"Erreur lors de la division: {str(e)}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route("/api/split_zip", methods=["POST"])
def api_split_zip():
    """API pour diviser un PDF et retourner un ZIP"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        mode = data.get("mode", "all")
        arg = data.get("arg", "")
        
        # Division
        split_files = PDFEngine.split(pdf_bytes, mode, arg)
        stats_manager.increment("splits")
        stats_manager.increment("zip_downloads")
        
        # Création du ZIP
        zip_data, zip_name = PDFEngine.create_zip(split_files)
        
        return jsonify({
            "success": True,
            "filename": zip_name,
            "count": len(split_files),
            "data": base64.b64encode(zip_data).decode()
        })
    
    except Exception as e:
        app.logger.error(f"Erreur lors de la création du ZIP: {str(e)}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route("/api/rotate", methods=["POST"])
def api_rotate():
    """API pour tourner les pages d'un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        angle = int(data.get("angle", 90))
        pages = data.get("pages", "all")
        
        # Rotation
        rotated_pdf, total_pages, rotated_count = PDFEngine.rotate(pdf_bytes, angle, pages)
        stats_manager.increment("rotations")
        
        return jsonify({
            "success": True,
            "filename": f"rotation_{angle}deg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": total_pages,
            "rotated": rotated_count,
            "data": base64.b64encode(rotated_pdf).decode()
        })
    
    except Exception as e:
        app.logger.error(f"Erreur lors de la rotation: {str(e)}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route("/api/compress", methods=["POST"])
def api_compress():
    """API pour compresser un PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        # Compression
        compressed_pdf, page_count = PDFEngine.compress(pdf_bytes)
        stats_manager.increment("compressions")
        
        return jsonify({
            "success": True,
            "filename": f"compressed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "pages": page_count,
            "data": base64.b64encode(compressed_pdf).decode()
        })
    
    except Exception as e:
        app.logger.error(f"Erreur lors de la compression: {str(e)}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route("/api/preview", methods=["POST"])
def api_preview():
    """API pour générer des aperçus de PDF"""
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "file" not in data:
            return jsonify({"error": "Fichier manquant"}), 400
        
        file_data = data["file"]
        if "data" not in file_data:
            return jsonify({"error": "Données du fichier manquantes"}), 400
        
        # Décodage
        try:
            pdf_bytes = base64.b64decode(file_data["data"])
        except (base64.binascii.Error, TypeError):
            return jsonify({"error": "Format Base64 invalide"}), 400
        
        # Génération des aperçus
        previews, total_pages = PDFEngine.preview(pdf_bytes)
        stats_manager.increment("previews")
        
        return jsonify({
            "success": True,
            "previews": previews,
            "total_pages": total_pages
        })
    
    except Exception as e:
        app.logger.error(f"Erreur lors de la génération d'aperçu: {str(e)}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

# ============================================================
# PAGES STATIQUES ET UTILITAIRES
# ============================================================

@app.route("/health")
def health_check():
    """Endpoint de santé de l'application"""
    stats = stats_manager.stats
    return jsonify({
        "status": "healthy",
        "app": AppConfig.NAME,
        "version": AppConfig.VERSION,
        "developer": AppConfig.DEVELOPER_NAME,
        "email": AppConfig.DEVELOPER_EMAIL,
        "hosting": AppConfig.HOSTING,
        "domain": AppConfig.DOMAIN,
        "timestamp": datetime.now().isoformat(),
        "total_operations": stats.get("total_operations", 0),
        "merges": stats.get("merges", 0),
        "splits": stats.get("splits", 0),
        "rotations": stats.get("rotations", 0),
        "compressions": stats.get("compressions", 0),
        "user_sessions": stats.get("user_sessions", 0)
    })

@app.route("/sitemap.xml")
def sitemap():
    """Génère un sitemap XML"""
    base_url = f"https://{AppConfig.DOMAIN}"
    pages = [
        ("/", datetime.now().strftime('%Y-%m-%d'), "daily", 1.0),
        ("/mentions-legales", "2024-01-15", "monthly", 0.8),
        ("/politique-confidentialite", "2024-01-15", "monthly", 0.8),
        ("/conditions-utilisation", "2024-01-15", "monthly", 0.8),
        ("/contact", "2024-01-15", "monthly", 0.7),
        ("/a-propos", "2024-01-15", "monthly", 0.7),
    ]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for path, lastmod, changefreq, priority in pages:
        xml += f'  <url>\n'
        xml += f'    <loc>{base_url}{path}</loc>\n'
        xml += f'    <lastmod>{lastmod}</lastmod>\n'
        xml += f'    <changefreq>{changefreq}</changefreq>\n'
        xml += f'    <priority>{priority}</priority>\n'
        xml += f'  </url>\n'
    
    xml += '</urlset>'
    
    return Response(xml, mimetype="application/xml")

@app.route("/robots.txt")
def robots():
    """Fichier robots.txt"""
    content = "User-agent: *\n"
    content += "Allow: /\n"
    content += f"Sitemap: https://{AppConfig.DOMAIN}/sitemap.xml\n"
    content += "\n"
    content += f"# {AppConfig.NAME} - Développé par {AppConfig.DEVELOPER_NAME}\n"
    
    return Response(content, mimetype="text/plain")

# ============================================================
# PAGES LÉGALES (inchangées - garder votre code existant)
# ============================================================

@app.route("/mentions-legales")
def legal_notices():
    content = f"""
    <div class="info-box">
        <i class="fas fa-info-circle me-2"></i>
        <strong>Information importante :</strong> Cette application traite vos fichiers PDF uniquement en mémoire.
        Aucun fichier n'est stocké de manière permanente sur nos serveurs.
    </div>
    
    <h2>Éditeur du service</h2>
    <p>Le service <strong>{AppConfig.NAME}</strong> est développé et maintenu par :</p>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-user-tie"></i>
        </div>
        <div>
            <strong>{AppConfig.DEVELOPER_NAME}</strong><br>
            <a href="mailto:{AppConfig.DEVELOPER_EMAIL}">{AppConfig.DEVELOPER_EMAIL}</a>
        </div>
    </div>
    
    <h2>Hébergement</h2>
    <p>Ce service est hébergé sur la plateforme <strong>{AppConfig.HOSTING}</strong> (<a href="https://{AppConfig.DOMAIN}" target="_blank">{AppConfig.DOMAIN}</a>).</p>
    <p>Les serveurs sont localisés dans des centres de données sécurisés et conformes aux normes européennes de protection des données.</p>
    
    <h2>Propriété intellectuelle</h2>
    <p>L'ensemble des contenus présents sur ce site (design, code source, interfaces, textes, graphismes) est protégé par les lois relatives à la propriété intellectuelle.</p>
    <p>Toute reproduction, modification, distribution ou exploitation non autorisée est strictement interdite.</p>
    
    <h2>Responsabilité</h2>
    <p>L'utilisateur reste l'unique responsable des fichiers PDF qu'il téléverse et traite via ce service.</p>
    <p>Il s'engage à ne pas utiliser le service pour des contenus illicites ou protégés par des droits d'auteur sans autorisation.</p>
    
    <h2>Disponibilité du service</h2>
    <p>Nous nous efforçons d'assurer une disponibilité continue du service, mais ne pouvons garantir un fonctionnement ininterrompu.</p>
    <p>Des périodes de maintenance technique peuvent être nécessaires pour améliorer le service.</p>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Mentions Légales",
        badge="Information légale",
        subtitle="Informations légales concernant l'utilisation du service PDF Fusion Pro",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )

@app.route("/politique-confidentialite")
def privacy_policy():
    content = f"""
    <h2>Respect de votre vie privée</h2>
    <p>Votre confidentialité est notre priorité. Cette politique explique comment nous collectons, utilisons et protégeons vos informations.</p>
    
    <div class="info-box">
        <i class="fas fa-shield-alt me-2"></i>
        <strong>Engagement de confidentialité :</strong> Nous ne stockons jamais le contenu de vos fichiers PDF.
        Tous les traitements sont effectués en mémoire vive et les fichiers sont supprimés immédiatement après traitement.
    </div>
    
    <h2>Données collectées</h2>
    <h3>Données techniques</h3>
    <p>Nous collectons des données techniques anonymes pour améliorer le service :</p>
    <ul>
        <li>Type d'opération effectuée (fusion, division, rotation, compression)</li>
        <li>Nombre de pages traitées</li>
        <li>Heure et date des opérations (anonymisées)</li>
        <li>Informations sur le navigateur et l'appareil (type, version)</li>
    </ul>
    
    <h3>Cookies</h3>
    <p>Nous utilisons uniquement des cookies techniques essentiels :</p>
    <ul>
        <li><strong>Session cookie :</strong> Pour maintenir votre session de travail</li>
        <li><strong>Préférences :</strong> Pour mémoriser vos paramètres d'interface</li>
    </ul>
    
    <h2>Publicité — Google AdSense</h2>
    <p>Ce site utilise <strong>Google AdSense</strong> (ID: {AppConfig.ADSENSE_CLIENT_ID}) pour afficher des publicités pertinentes.</p>
    <p>Google utilise des cookies pour personnaliser les annonces en fonction de votre navigation sur ce site et d'autres sites web.</p>
    <p>Vous pouvez désactiver la personnalisation des annonces via les <a href="https://adssettings.google.com" target="_blank">paramètres des annonces Google</a>.</p>
    
    <h2>Vos droits (RGPD)</h2>
    <p>Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des droits suivants :</p>
    <ul>
        <li>Droit d'accès à vos données</li>
        <li>Droit de rectification</li>
        <li>Droit à l'effacement</li>
        <li>Droit à la limitation du traitement</li>
        <li>Droit à la portabilité des données</li>
    </ul>
    
    <p>Pour exercer ces droits, contactez-nous à : <a href="mailto:{AppConfig.DEVELOPER_EMAIL}">{AppConfig.DEVELOPER_EMAIL}</a></p>
    
    <h2>Sécurité des données</h2>
    <p>Nous mettons en œuvre des mesures de sécurité techniques et organisationnelles appropriées pour protéger vos données contre tout accès non autorisé, altération ou destruction.</p>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Politique de Confidentialité",
        badge="Protection des données",
        subtitle="Comment nous protégeons et utilisons vos données",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )

@app.route("/conditions-utilisation")
def terms_of_service():
    content = f"""
    <h2>Acceptation des conditions</h2>
    <p>En utilisant le service <strong>{AppConfig.NAME}</strong>, vous acceptez pleinement et sans réserve les présentes conditions d'utilisation.</p>
    
    <div class="info-box">
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Avertissement important :</strong> Ce service est fourni "tel quel". 
        Nous déclinons toute responsabilité concernant les fichiers traités par l'utilisateur.
    </div>
    
    <h2>Usage autorisé</h2>
    <p>Vous vous engagez à utiliser le service de manière responsable et légale :</p>
    
    <h3>Interdictions</h3>
    <ul>
        <li>Téléverser des fichiers contenant des données illicites ou protégés par des droits d'auteur sans autorisation</li>
        <li>Utiliser le service pour des activités frauduleuses ou malveillantes</li>
        <li>Tenter de contourner les mesures de sécurité du service</li>
        <li>Surcharger délibérément le service (attaques DoS/DDoS)</li>
        <li>Réutiliser le contenu du service à des fins commerciales sans autorisation</li>
    </ul>
    
    <h3>Obligations</h3>
    <ul>
        <li>Respecter les droits de propriété intellectuelle des documents traités</li>
        <li>Assurer la confidentialité de vos propres fichiers</li>
        <li>Utiliser le service conformément à sa destination première</li>
    </ul>
    
    <h2>Limitation de responsabilité</h2>
    <p>Le service est fourni sans aucune garantie, expresse ou implicite, y compris, mais sans s'y limiter, les garanties de qualité marchande, d'adéquation à un usage particulier et de non-contrefaçon.</p>
    
    <p>En aucun cas, <strong>{AppConfig.DEVELOPER_NAME}</strong> ne pourra être tenu responsable :</p>
    <ul>
        <li>Des dommages directs ou indirects résultant de l'utilisation ou de l'impossibilité d'utiliser le service</li>
        <li>De la perte ou de l'altération des fichiers PDF traités</li>
        <li>Des conséquences de l'utilisation des fichiers générés par le service</li>
    </ul>
    
    <h2>Modifications des conditions</h2>
    <p>Nous nous réservons le droit de modifier ces conditions d'utilisation à tout moment.</p>
    <p>Les utilisateurs seront informés des changements significatifs via une notification sur le site.</p>
    
    <h2>Propriété intellectuelle</h2>
    <p>Le service, son code source, son design et son contenu sont la propriété exclusive de <strong>{AppConfig.DEVELOPER_NAME}</strong>.</p>
    <p>Toute reproduction, même partielle, est interdite sans autorisation préalable écrite.</p>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Conditions d'Utilisation",
        badge="Règles d'usage",
        subtitle="Règles et conditions d'utilisation du service PDF Fusion Pro",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )

@app.route("/contact")
def contact():
    content = f"""
    <h2>Nous contacter</h2>
    <p>Pour toute question, suggestion ou demande concernant le service, n'hésitez pas à nous écrire.</p>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-envelope"></i>
        </div>
        <div>
            <h3 class="h5 mb-1">Adresse email</h3>
            <a href="mailto:{AppConfig.DEVELOPER_EMAIL}" class="fs-5">{AppConfig.DEVELOPER_EMAIL}</a>
        </div>
    </div>
    
    <div class="info-box mt-4">
        <i class="fas fa-clock me-2"></i>
        <strong>Temps de réponse :</strong> Nous nous efforçons de répondre à tous les messages dans un délai de 48 heures.
    </div>
    
    <h2 class="mt-4">Types de demandes</h2>
    
    <h3><i class="fas fa-wrench me-2"></i> Support technique</h3>
    <p>Pour signaler un bug, un problème technique ou proposer une amélioration fonctionnelle.</p>
    
    <h3><i class="fas fa-shield-alt me-2"></i> Confidentialité / RGPD</h3>
    <p>Pour exercer vos droits relatifs à la protection des données personnelles.</p>
    
    <h3><i class="fas fa-ad me-2"></i> Publicité</h3>
    <p>Pour toute question concernant Google AdSense ou la publicité affichée.</p>
    
    <h3><i class="fas fa-handshake me-2"></i> Partenariats</h3>
    <p>Pour discuter d'opportunités de collaboration ou d'intégration.</p>
    
    <h2>Informations importantes</h2>
    <p>Lors de votre demande, merci de préciser :</p>
    <ul>
        <li>L'objet précis de votre demande</li>
        <li>Votre nom ou pseudonyme</li>
        <li>Toute information contextuelle utile</li>
    </ul>
    
    <div class="alert alert-warning mt-4">
        <i class="fas fa-exclamation-circle me-2"></i>
        <strong>Note :</strong> Pour des raisons de sécurité, nous ne traitons pas les demandes concernant des fichiers PDF spécifiques via email.
        Tous les traitements de fichiers doivent être effectués directement via l'interface web.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="Contact",
        badge="Support",
        subtitle="Comment nous contacter pour toute question ou demande",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )

@app.route("/a-propos")
def about():
    content = f"""
    <h2>À propos de PDF Fusion Pro</h2>
    
    <div class="contact-info">
        <div class="contact-icon">
            <i class="fas fa-rocket"></i>
        </div>
        <div>
            <h3 class="h5 mb-1">Notre mission</h3>
            <p>Offrir un outil PDF en ligne performant, intuitif et respectueux de votre vie privée.</p>
        </div>
    </div>
    
    <h2 class="mt-4">Caractéristiques principales</h2>
    
    <div class="row mt-3">
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-object-group text-primary me-2"></i>
                        Fusion PDF
                    </h4>
                    <p class="card-text">Combine plusieurs fichiers PDF en un seul document organisé.</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-cut text-success me-2"></i>
                        Division PDF
                    </h4>
                    <p class="card-text">Divisez vos PDF par page, par plage ou selon des pages spécifiques.</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-sync-alt text-warning me-2"></i>
                        Rotation PDF
                    </h4>
                    <p class="card-text">Faites pivoter des pages spécifiques ou l'ensemble du document.</p>
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <h4 class="card-title h5">
                        <i class="fas fa-compress-alt text-danger me-2"></i>
                        Compression PDF
                    </h4>
                    <p class="card-text">Réduisez la taille de vos fichiers PDF sans perte de qualité notable.</p>
                </div>
            </div>
        </div>
    </div>
    
    <h2 class="mt-4">Nos engagements</h2>
    
    <h3><i class="fas fa-lock text-success me-2"></i> Sécurité</h3>
    <p>Tous les traitements sont effectués en mémoire. Aucun fichier n'est stocké sur nos serveurs.</p>
    
    <h3><i class="fas fa-tachometer-alt text-primary me-2"></i> Performance</h3>
    <p>Interface optimisée pour une expérience utilisateur fluide et rapide.</p>
    
    <h3><i class="fas fa-eye-slash text-info me-2"></i> Confidentialité</h3>
    <p>Nous ne collectons pas de données personnelles liées au contenu de vos fichiers.</p>
    
    <h3><i class="fas fa-dollar-sign text-warning me-2"></i> Gratuité</h3>
    <p>Service entièrement gratuit, financé par des publicités discrètes et non intrusives.</p>
    
    <h2>Développeur</h2>
    <p><strong>{AppConfig.NAME}</strong> est développé et maintenu par <strong>{AppConfig.DEVELOPER_NAME}</strong>, un développeur passionné par la création d'outils web utiles et accessibles.</p>
    
    <div class="info-box mt-4">
        <i class="fas fa-code me-2"></i>
        <strong>Technologies utilisées :</strong> Python, Flask, PyPDF2, Bootstrap 5, JavaScript moderne.
    </div>
    """
    
    return render_template_string(
        LEGAL_TEMPLATE,
        title="À Propos",
        badge="Notre histoire",
        subtitle="Découvrez PDF Fusion Pro, notre mission et nos valeurs",
        content=content,
        current_year=datetime.now().year,
        config=AppConfig
    )

# ============================================================
# PAGE D'ACCUEIL
# ============================================================

@app.route("/")
def home():
    """Page d'accueil principale"""
    return render_template_string(
        HTML_TEMPLATE,
        title="PDF Fusion Pro – Outil PDF Moderne & Professionnel",
        description="Fusionnez, divisez, tournez et compressez vos fichiers PDF gratuitement. Interface moderne, rapide et sécurisée.",
        config=AppConfig,
        current_year=datetime.now().year
    )

# ============================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        threaded=True
    )