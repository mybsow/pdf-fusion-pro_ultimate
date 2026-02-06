import os
import secrets
from pathlib import Path


class AppConfig:
    """
    Configuration centralisée de l'application.
    Compatible production / cloud (Render, Fly.io, etc.)
    """

    # ============================================================
    # INFOS APP
    # ============================================================

    VERSION = "6.1-Material-Pro"
    NAME = "PDF Fusion Pro"
    DEVELOPER_NAME = "MYBSOW"
    DEVELOPER_EMAIL = "banousow@gmail.com"
    HOSTING = "Render Cloud Platform"

    _raw_domain = os.environ.get(
        "APP_DOMAIN",
        "pdf-fusion-pro-ultimate.onrender.com"
    )

    DOMAIN = _raw_domain.replace("https://", "").replace("http://", "").rstrip("/")

    # ============================================================
    # SECURITE
    # ============================================================

    # ⚠️ IMPORTANT : définissez SECRET_KEY dans Render !
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # cookies sécurisés (HTTPS)
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # force https pour génération d’URL
    PREFERRED_URL_SCHEME = "https"

    # performance prod
    TEMPLATES_AUTO_RELOAD = False

    # ============================================================
    # UPLOADS (CRITIQUE POUR FLASK)
    # ============================================================

    # ⚠️ Flask utilise UNIQUEMENT cette variable
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    # alias interne (facultatif mais pratique)
    MAX_CONTENT_SIZE = MAX_CONTENT_LENGTH

    # tailles spécifiques
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_PDF_SIZE = 20 * 1024 * 1024    # 20 MB
    MAX_DOC_SIZE = 5 * 1024 * 1024     # 5 MB

    MAX_IMAGES_PER_PDF = 20
    MAX_FILES_PER_CONVERSION = 10

    # ============================================================
    # DOSSIERS
    # ============================================================

    TEMP_FOLDER = Path("/tmp/pdf_fusion_pro")

    CONVERSION_FOLDER = "conversion_temp"
    UPLOADS_FOLDER = "uploads"
    LOGS_FOLDER = "logs"

    STATS_FILE = "usage_stats.json"

    TEMP_FILE_EXPIRY = 3600  # 1 heure

    # ============================================================
    # FORMATS SUPPORTES
    # ============================================================

    SUPPORTED_IMAGE_FORMATS = {
        'pdf': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'],
        'word': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.pdf', '.webp'],
        'excel': ['.jpg', '.jpeg', '.png', '.pdf', '.csv', '.xlsx', '.xls', '.ods'],
        'image': ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    }

    MIME_TYPES = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.csv': 'text/csv',
        '.ods': 'application/vnd.oasis.opendocument.spreadsheet'
    }

    # ============================================================
    # QUALITE PDF
    # ============================================================

    PDF_QUALITY_OPTIONS = {
        'low': {'dpi': 150, 'quality': 75, 'max_size': (800, 800)},
        'medium': {'dpi': 200, 'quality': 85, 'max_size': (1200, 1200)},
        'high': {'dpi': 300, 'quality': 95, 'max_size': (2400, 2400)}
    }

    # ============================================================
    # OCR
    # ============================================================

    OCR_ENABLED = os.environ.get("OCR_ENABLED", "true").lower() == "true"
    OCR_LANGUAGES = ['fra', 'eng', 'deu', 'spa', 'ita']
    OCR_DEFAULT_LANGUAGE = 'fra'

    # ============================================================
    # RATE LIMIT
    # ============================================================

    CONVERSION_RATE_LIMIT = "10/minute"

    # ============================================================
    # INITIALISATION
    # ============================================================

    @classmethod
    def initialize(cls):
        """
        Initialise les dossiers nécessaires.
        À appeler UNE fois au démarrage Flask.
        """

        cls.TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

        conversion_dirs = [
            cls.TEMP_FOLDER / cls.CONVERSION_FOLDER,
            cls.TEMP_FOLDER / cls.UPLOADS_FOLDER,
            cls.TEMP_FOLDER / cls.LOGS_FOLDER,
            cls.TEMP_FOLDER / "conversion_temp/images",
            cls.TEMP_FOLDER / "conversion_temp/pdf",
            cls.TEMP_FOLDER / "conversion_temp/word",
            cls.TEMP_FOLDER / "conversion_temp/excel",
            Path("data"),
            Path("data/contacts"),
            Path("data/stats")
        ]

        for directory in conversion_dirs:
            directory.mkdir(parents=True, exist_ok=True)

        # warning réel (corrigé)
        if "SECRET_KEY" not in os.environ:
            print("⚠️  WARNING: SECRET_KEY non définie — à configurer en production.")

        print("✅ Configuration initialisée")
        print(f"   - Taille max upload Flask : {cls.MAX_CONTENT_LENGTH // (1024*1024)} MB")
        print(f"   - Taille max image : {cls.MAX_IMAGE_SIZE // (1024*1024)} MB")
        print(f"   - OCR activé : {cls.OCR_ENABLED}")

    # ============================================================
    # HELPERS
    # ============================================================

    @classmethod
    def get_mime_type(cls, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        return cls.MIME_TYPES.get(ext, 'application/octet-stream')

    @classmethod
    def get_max_size_for_format(cls, format_type: str) -> int:
        size_map = {
            'pdf': cls.MAX_PDF_SIZE,
            'word': cls.MAX_DOC_SIZE,
            'excel': cls.MAX_DOC_SIZE,
            'image': cls.MAX_IMAGE_SIZE
        }
        return size_map.get(format_type, cls.MAX_IMAGE_SIZE)

    @classmethod
    def get_conversion_temp_dir(cls, conversion_type: str = "general") -> Path:
        if conversion_type in ['images', 'pdf', 'word', 'excel']:
            return cls.TEMP_FOLDER / "conversion_temp" / conversion_type
        return cls.TEMP_FOLDER / "conversion_temp"

    @classmethod
    def cleanup_old_files(cls, max_age_seconds: int = None):

        import time

        if max_age_seconds is None:
            max_age_seconds = cls.TEMP_FILE_EXPIRY

        current_time = time.time()
        cleaned_count = 0

        conversion_dirs = [
            cls.get_conversion_temp_dir(),
            cls.get_conversion_temp_dir('images'),
            cls.get_conversion_temp_dir('pdf'),
            cls.get_conversion_temp_dir('word'),
            cls.get_conversion_temp_dir('excel'),
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
            print(f"🧹 Nettoyage: {cleaned_count} fichiers supprimés")
