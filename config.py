import os
import secrets
from pathlib import Path
from datetime import timedelta


class AppConfig:
    """
    Configuration centralisée de l'application.
    Compatible production / cloud (Render, Fly.io, etc.)
    Version étendue pour les conversions
    """

    # ============================================================
    # INFOS APP
    # ============================================================

    VERSION = "6.1-Material-Pro"
    NAME = "PDF Fusion Pro Ultimate"
    DEVELOPER_NAME = "MYBSOW"
    DEVELOPER_EMAIL = "banousow@gmail.com"
    HOSTING = "Render Cloud Platform"

    _raw_domain = os.environ.get(
        "APP_DOMAIN",
        "pdf-fusion-pro-ultimate-ltd.onrender.com"
    )

    DOMAIN = _raw_domain.replace("https://", "").replace("http://", "").rstrip("/")

    # ============================================================
    # SECURITE
    # ============================================================

    # ⚠️ IMPORTANT : définissez SECRET_KEY dans Render !
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    # Dans config.py, ajoutez si nécessaire :
    ADSENSE_CLIENT_ID = os.environ.get("ADSENSE_CLIENT_ID", "ca-pub-8967416460526921")  # Votre ID AdSense

    # cookies sécurisés (HTTPS)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # force https pour génération d'URL
    PREFERRED_URL_SCHEME = "https"

    # performance prod
    TEMPLATES_AUTO_RELOAD = False

    # ============================================================
    # UPLOADS (CRITIQUE POUR FLASK)
    # ============================================================

    # ⚠️ Flask utilise UNIQUEMENT cette variable
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB (augmenté pour les conversions)

    # alias interne (facultatif mais pratique)
    MAX_CONTENT_SIZE = MAX_CONTENT_LENGTH

    # tailles spécifiques
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50 MB (augmenté)
    MAX_PDF_SIZE = 50 * 1024 * 1024    # 50 MB
    MAX_DOC_SIZE = 50 * 1024 * 1024    # 50 MB
    MAX_EXCEL_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_PPT_SIZE = 50 * 1024 * 1024    # 50 MB

    MAX_IMAGES_PER_PDF = 50  # Augmenté
    MAX_FILES_PER_CONVERSION = 10  # Augmenté

    # ============================================================
    # DOSSIERS
    # ============================================================

    TEMP_FOLDER = Path("/tmp/pdf_fusion_pro")

    CONVERSION_FOLDER = "conversion_temp"
    UPLOADS_FOLDER = "uploads"
    LOGS_FOLDER = "logs"
    DATA_FOLDER = "data"

    STATS_FILE = "usage_stats.json"

    TEMP_FILE_EXPIRY = 3600  # 1 heure

    # ============================================================
    # FORMATS SUPPORTES
    # ============================================================

    SUPPORTED_FORMATS = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'],
        'pdf': ['.pdf'],
        'word': ['.doc', '.docx'],
        'excel': ['.xls', '.xlsx', '.xlsm', '.xlsb'],
        'powerpoint': ['.ppt', '.pptx'],
        'csv': ['.csv', '.txt'],
        'rtf': ['.rtf'],
        'odt': ['.odt'],
        'ods': ['.ods'],
        'odp': ['.odp']
    }

    MIME_TYPES = {
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.webp': 'image/webp',
        # Documents
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.rtf': 'application/rtf',
        '.odt': 'application/vnd.oasis.opendocument.text',
        # Spreadsheets
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12',
        '.xlsb': 'application/vnd.ms-excel.sheet.binary.macroEnabled.12',
        '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
        '.csv': 'text/csv',
        # Presentations
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.odp': 'application/vnd.oasis.opendocument.presentation',
        # Text
        '.txt': 'text/plain',
        # Archive
        '.zip': 'application/zip'
    }

    # ============================================================
    # QUALITE PDF
    # ============================================================

    PDF_QUALITY_OPTIONS = {
        'low': {'dpi': 150, 'quality': 75, 'max_size': (800, 800), 'compression': 'high'},
        'medium': {'dpi': 200, 'quality': 85, 'max_size': (1200, 1200), 'compression': 'medium'},
        'high': {'dpi': 300, 'quality': 95, 'max_size': (2400, 2400), 'compression': 'low'},
        'original': {'dpi': None, 'quality': 100, 'max_size': None, 'compression': 'none'}
    }

    # ============================================================
    # OCR CONFIGURATION
    # ============================================================

    OCR_ENABLED = os.environ.get("OCR_ENABLED", "true").lower() == "true"
    OCR_LANGUAGES = ['fra', 'eng', 'deu', 'spa', 'ita', 'por', 'rus', 'ara', 'chi_sim', 'chi_tra']
    OCR_DEFAULT_LANGUAGE = 'fra'
    
    # Chemins système pour OCR
    TESSERACT_CMD = "/usr/bin/tesseract"
    TESSDATA_PREFIX = os.environ.get("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/4.00/tessdata")
    
    # Configuration OCR
    OCR_ENGINE_MODE = 3  # LSTM seulement
    OCR_PAGE_SEG_MODE = 6  # Bloc uniforme de texte
    OCR_CONFIG = f'--oem {OCR_ENGINE_MODE} --psm {OCR_PAGE_SEG_MODE}'
    
    # Seuil de confiance OCR
    OCR_MIN_CONFIDENCE = 30
    OCR_HIGH_CONFIDENCE = 70

    # ============================================================
    # LIBREOFFICE / DOCUMENT CONVERSION
    # ============================================================

    LIBREOFFICE_ENABLED = True
    LIBREOFFICE_PATH = os.environ.get("LIBREOFFICE_PATH", "/usr/bin/libreoffice")
    UNOCONV_PATH = "/usr/bin/unoconv"
    
    # Timeout pour les conversions Office
    OFFICE_CONVERSION_TIMEOUT = 120  # secondes

    # ============================================================
    # CONVERSION SETTINGS
    # ============================================================

    # Format de sortie par défaut
    DEFAULT_OUTPUT_FORMATS = {
        'word': 'docx',
        'excel': 'xlsx',
        'powerpoint': 'pptx',
        'image': 'png',
        'pdf': 'pdf',
        'text': 'txt'
    }
    
    # Résolutions par défaut
    DEFAULT_IMAGE_DPI = 300
    DEFAULT_PDF_DPI = 200
    
    # Options de compression
    COMPRESSION_LEVELS = {
        'none': 0,
        'low': 1,
        'medium': 5,
        'high': 9
    }
    
    # Marges par défaut (en mm)
    DEFAULT_MARGINS = {
        'none': (0, 0, 0, 0),
        'small': (10, 10, 10, 10),
        'medium': (20, 20, 20, 20),
        'large': (30, 30, 30, 30),
        'normal': (25, 25, 25, 25)
    }

    # ============================================================
    # PAGE SIZES (en mm)
    # ============================================================

    PAGE_SIZES = {
        'A0': (841, 1189),
        'A1': (594, 841),
        'A2': (420, 594),
        'A3': (297, 420),
        'A4': (210, 297),
        'A5': (148, 210),
        'A6': (105, 148),
        'Letter': (216, 279),
        'Legal': (216, 356),
        'Tabloid': (279, 432)
    }

    # ============================================================
    # PERFORMANCE & LIMITS
    # ============================================================

    CONVERSION_RATE_LIMIT = "20/minute"
    API_RATE_LIMIT = "100/hour"
    
    # Timeouts
    CONVERSION_TIMEOUT = 300  # 5 minutes
    OCR_TIMEOUT = 180  # 3 minutes
    UPLOAD_TIMEOUT = 120  # 2 minutes
    
    # Worker threads
    WORKER_THREADS = 4
    MAX_CONCURRENT_CONVERSIONS = 10

    # ============================================================
    # CACHE CONFIGURATION
    # ============================================================

    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_THRESHOLD = 100
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ============================================================
    # FEATURE FLAGS
    # ============================================================

    FEATURES = {
        'conversion': True,
        'ocr': OCR_ENABLED,
        'office_conversion': LIBREOFFICE_ENABLED,
        'batch_processing': True,
        'api': True,
        'stats': True,
        'admin': True,
        'multi_language': True
    }

    # ============================================================
    # EMAIL CONFIGURATION (optional)
    # ============================================================

    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "false").lower() == "true"
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "banousow@gmail.com")

    # ============================================================
    # LOGGING
    # ============================================================

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5

    # ============================================================
    # INITIALISATION
    # ============================================================

    @classmethod
    def initialize(cls):
        """
        Initialise les dossiers nécessaires.
        À appeler UNE fois au démarrage Flask.
        """

        # Créer le dossier temporaire principal
        cls.TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

        # Dossiers de conversion
        conversion_dirs = [
            cls.TEMP_FOLDER / cls.CONVERSION_FOLDER,
            cls.TEMP_FOLDER / cls.UPLOADS_FOLDER,
            cls.TEMP_FOLDER / cls.LOGS_FOLDER,
            # Dossiers spécifiques par type
            cls.TEMP_FOLDER / "conversion_temp/images",
            cls.TEMP_FOLDER / "conversion_temp/pdf",
            cls.TEMP_FOLDER / "conversion_temp/word",
            cls.TEMP_FOLDER / "conversion_temp/excel",
            cls.TEMP_FOLDER / "conversion_temp/powerpoint",
            cls.TEMP_FOLDER / "conversion_temp/ocr",
            cls.TEMP_FOLDER / "conversion_temp/office",
            # Dossiers de données
            Path("data"),
            Path("data/contacts"),
            Path("data/stats"),
            Path("data/ratings"),
            Path("data/logs")
        ]

        for directory in conversion_dirs:
            directory.mkdir(parents=True, exist_ok=True)

        # Vérification des dépendances système
        cls._check_system_dependencies()
        
        # Vérification OCR
        if cls.OCR_ENABLED:
            cls._check_ocr_availability()

        # Vérification LibreOffice
        if cls.LIBREOFFICE_ENABLED:
            cls._check_libreoffice_availability()

        print("✅ Configuration initialisée")
        print(f"   - Taille max upload : {cls.MAX_CONTENT_LENGTH // (1024*1024)} MB")
        print(f"   - OCR activé : {cls.OCR_ENABLED}")
        print(f"   - LibreOffice : {cls.LIBREOFFICE_ENABLED}")
        print(f"   - Langues OCR : {', '.join(cls.OCR_LANGUAGES)}")

        # Warning sécurité
        if "SECRET_KEY" not in os.environ:
            print("⚠️  WARNING: SECRET_KEY non définie — à configurer en production.")

    # ============================================================
    # HELPERS & UTILITIES
    # ============================================================

    @classmethod
    def get_mime_type(cls, filename: str) -> str:
        """Retourne le type MIME d'un fichier"""
        ext = Path(filename).suffix.lower()
        return cls.MIME_TYPES.get(ext, 'application/octet-stream')

    @classmethod
    def get_max_size_for_format(cls, format_type: str) -> int:
        """Retourne la taille max pour un format spécifique"""
        size_map = {
            'pdf': cls.MAX_PDF_SIZE,
            'word': cls.MAX_DOC_SIZE,
            'excel': cls.MAX_EXCEL_SIZE,
            'powerpoint': cls.MAX_PPT_SIZE,
            'image': cls.MAX_IMAGE_SIZE,
            'csv': cls.MAX_DOC_SIZE,
            'rtf': cls.MAX_DOC_SIZE
        }
        return size_map.get(format_type.lower(), cls.MAX_CONTENT_SIZE)

    @classmethod
    def get_conversion_temp_dir(cls, conversion_type: str = "general") -> Path:
        """Retourne le dossier temporaire pour un type de conversion"""
        if conversion_type in ['images', 'pdf', 'word', 'excel', 'powerpoint', 'ocr', 'office']:
            return cls.TEMP_FOLDER / "conversion_temp" / conversion_type
        return cls.TEMP_FOLDER / "conversion_temp"

    @classmethod
    def get_supported_extensions(cls, conversion_type: str) -> list:
        """Retourne les extensions supportées pour un type de conversion"""
        return cls.SUPPORTED_FORMATS.get(conversion_type.lower(), [])

    @classmethod
    def is_format_supported(cls, filename: str, conversion_type: str) -> bool:
        """Vérifie si un format est supporté pour une conversion"""
        ext = Path(filename).suffix.lower()
        supported = cls.get_supported_extensions(conversion_type)
        return ext in supported

    @classmethod
    def get_pdf_quality_settings(cls, quality: str) -> dict:
        """Retourne les paramètres de qualité PDF"""
        return cls.PDF_QUALITY_OPTIONS.get(quality.lower(), cls.PDF_QUALITY_OPTIONS['medium'])

    @classmethod
    def get_page_size(cls, size_name: str) -> tuple:
        """Retourne les dimensions d'un format de page"""
        return cls.PAGE_SIZES.get(size_name, cls.PAGE_SIZES['A4'])

    @classmethod
    def get_compression_level(cls, level: str) -> int:
        """Retourne le niveau de compression"""
        return cls.COMPRESSION_LEVELS.get(level.lower(), 5)

    @classmethod
    def get_margins(cls, margin_type: str) -> tuple:
        """Retourne les marges"""
        return cls.DEFAULT_MARGINS.get(margin_type.lower(), cls.DEFAULT_MARGINS['normal'])

    @classmethod
    def _check_system_dependencies(cls):
        """Vérifie les dépendances système"""
        import shutil
        
        dependencies = {
            'tesseract': cls.TESSERACT_CMD,
            'libreoffice': cls.LIBREOFFICE_PATH,
            'unoconv': cls.UNOCONV_PATH,
            'pdftoppm': 'pdftoppm',
            'pdftocairo': 'pdftocairo'
        }
        
        print("🔍 Vérification des dépendances système:")
        for name, path in dependencies.items():
            if shutil.which(path if '/' not in path else path.split('/')[-1]):
                print(f"   ✅ {name}")
            else:
                print(f"   ⚠️  {name} (non trouvé)")

    @classmethod
    def _check_ocr_availability(cls):
        """Vérifie la disponibilité de l'OCR"""
        if not cls.OCR_ENABLED:
            return
            
        try:
            import pytesseract # type: ignore
            import subprocess
            
            # Vérifier Tesseract
            pytesseract.pytesseract.tesseract_cmd = cls.TESSERACT_CMD
            
            # Vérifier les langues disponibles
            result = subprocess.run(
                ["tesseract", "--list-langs"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                available_langs = result.stdout.strip().split('\n')[1:]
                missing_langs = [lang for lang in cls.OCR_LANGUAGES if lang not in available_langs]
                
                if missing_langs:
                    print(f"   ⚠️  Langues OCR manquantes: {', '.join(missing_langs)}")
                else:
                    print(f"   ✅ OCR: {len(available_langs)} langues disponibles")
            else:
                print("   ⚠️  Impossible de vérifier les langues OCR")
                
        except Exception as e:
            print(f"   ⚠️  Erreur vérification OCR: {e}")

    @classmethod
    def _check_libreoffice_availability(cls):
        """Vérifie la disponibilité de LibreOffice"""
        if not cls.LIBREOFFICE_ENABLED:
            return
            
        try:
            import subprocess
            
            result = subprocess.run(
                [cls.LIBREOFFICE_PATH, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"   ✅ LibreOffice: {version}")
            else:
                print("   ⚠️  LibreOffice non fonctionnel")
                
        except Exception as e:
            print(f"   ⚠️  Erreur vérification LibreOffice: {e}")

    @classmethod
    def cleanup_old_files(cls, max_age_seconds: int = None):
        """Nettoie les fichiers temporaires anciens"""
        import time
        
        if max_age_seconds is None:
            max_age_seconds = cls.TEMP_FILE_EXPIRY

        current_time = time.time()
        cleaned_count = 0

        # Dossiers à nettoyer
        conversion_dirs = [
            cls.get_conversion_temp_dir(),
            cls.get_conversion_temp_dir('images'),
            cls.get_conversion_temp_dir('pdf'),
            cls.get_conversion_temp_dir('word'),
            cls.get_conversion_temp_dir('excel'),
            cls.get_conversion_temp_dir('powerpoint'),
            cls.get_conversion_temp_dir('ocr'),
            cls.get_conversion_temp_dir('office'),
            cls.TEMP_FOLDER / cls.UPLOADS_FOLDER
        ]

        for directory in conversion_dirs:
            if directory.exists():
                for file_path in directory.glob('*'):
                    if file_path.is_file():
                        try:
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > max_age_seconds:
                                file_path.unlink()
                                cleaned_count += 1
                        except (OSError, PermissionError):
                            continue

        if cleaned_count > 0:
            print(f"🧹 Nettoyage: {cleaned_count} fichiers temporaires supprimés")

    @classmethod
    def get_ocr_languages_display(cls):
        """Retourne les langues OCR avec leur nom d'affichage"""
        language_names = {
            'fra': 'Français',
            'eng': 'Anglais',
            'deu': 'Allemand',
            'spa': 'Espagnol',
            'ita': 'Italien',
            'por': 'Portugais',
            'rus': 'Russe',
            'ara': 'Arabe',
            'chi_sim': 'Chinois simplifié',
            'chi_tra': 'Chinois traditionnel'
        }
        
        return {code: language_names.get(code, code) for code in cls.OCR_LANGUAGES}

    @classmethod
    def get_quality_options_display(cls):
        """Retourne les options de qualité pour l'affichage"""
        return {
            'low': 'Basse (rapide)',
            'medium': 'Moyenne (équilibrée)',
            'high': 'Haute (qualité)',
            'original': 'Originale (sans perte)'
        }

    @classmethod
    def get_compression_options_display(cls):
        """Retourne les options de compression pour l'affichage"""
        return {
            'none': 'Aucune compression',
            'low': 'Faible compression',
            'medium': 'Compression moyenne',
            'high': 'Forte compression'
        }
