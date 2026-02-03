import os
import uuid
from pathlib import Path

class AppConfig:
    """Configuration centralisée de l'application"""
    VERSION = "6.1-Material-Pro"
    NAME = "PDF Fusion Pro"
    DEVELOPER_NAME = "MYBSOW"
    DEVELOPER_EMAIL = "banousow@gmail.com"
    HOSTING = "Render Cloud Platform"

    _raw_domain = os.environ.get("APP_DOMAIN", "pdf-fusion-pro-ultimate.onrender.com")
    DOMAIN = _raw_domain.replace("https://", "").replace("http://", "").rstrip("/")

    # Paramètres de sécurité
    SECRET_KEY = os.environ.get("SECRET_KEY", str(uuid.uuid4()))
    MAX_CONTENT_SIZE = 50 * 1024 * 1024  # 50MB
    TEMP_FOLDER = Path("/tmp/pdf_fusion_pro")

    # AdSense
    ADSENSE_CLIENT_ID = "pub-8967416460526921"
    ADSENSE_PUBLISHER_ID = "ca-pub-8967416460526921"

    # Chemins
    STATS_FILE = "usage_stats.json"
    
    # ============================================================
    # CONFIGURATION DES CONVERSIONS (NOUVELLE SECTION)
    # ============================================================
    
    # Formats de fichiers supportés pour la conversion
    SUPPORTED_IMAGE_FORMATS = {
        'pdf': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'],
        'word': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.pdf', '.webp'],
        'excel': ['.jpg', '.jpeg', '.png', '.pdf', '.csv', '.xlsx', '.xls', '.ods'],
        'image': ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    }
    
    # Tailles maximales (en bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB par image
    MAX_PDF_SIZE = 20 * 1024 * 1024    # 20 MB pour les PDF
    MAX_DOC_SIZE = 5 * 1024 * 1024     # 5 MB pour les documents Word/Excel
    
    # Limites de fichiers
    MAX_IMAGES_PER_PDF = 20            # Max 20 images par PDF
    MAX_FILES_PER_CONVERSION = 10      # Max 10 fichiers par conversion batch
    
    # Délai d'expiration des fichiers temporaires (en secondes)
    TEMP_FILE_EXPIRY = 3600  # 1 heure
    
    # Configuration qualité
    PDF_QUALITY_OPTIONS = {
        'low': {'dpi': 150, 'quality': 75, 'max_size': (800, 800)},
        'medium': {'dpi': 200, 'quality': 85, 'max_size': (1200, 1200)},
        'high': {'dpi': 300, 'quality': 95, 'max_size': (2400, 2400)}
    }
    
    # Configuration OCR (si activé)
    OCR_ENABLED = os.environ.get("OCR_ENABLED", "false").lower() == "true"
    OCR_LANGUAGES = ['fra', 'eng', 'deu', 'spa', 'ita']
    OCR_DEFAULT_LANGUAGE = 'fra'
    
    # Dossiers spécifiques pour les conversions
    CONVERSION_FOLDER = "conversion_temp"
    UPLOADS_FOLDER = "uploads"
    LOGS_FOLDER = "logs"
    
    # Taux limite pour les conversions
    CONVERSION_RATE_LIMIT = "10/minute"  # 10 conversions par minute
    
    # Types MIME pour validation
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
    
    @classmethod
    def initialize(cls):
        """Initialise les répertoires nécessaires"""
        # Dossier temporaire principal
        cls.TEMP_FOLDER.mkdir(exist_ok=True)
        
        # Créer les sous-dossiers pour les conversions
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
        
        # Vérifier les variables critiques
        if cls.SECRET_KEY == str(uuid.uuid4()):
            print("⚠️  AVERTISSEMENT: SECRET_KEY utilise une valeur générée. Configurez SECRET_KEY en production.")
        
        # Afficher la configuration des conversions
        print(f"✅ Configuration des conversions initialisée:")
        print(f"   - Formats image supportés: {len(cls.SUPPORTED_IMAGE_FORMATS['pdf'])} formats")
        print(f"   - Taille max image: {cls.MAX_IMAGE_SIZE // (1024*1024)} MB")
        print(f"   - Images max par PDF: {cls.MAX_IMAGES_PER_PDF}")
        print(f"   - OCR activé: {cls.OCR_ENABLED}")
    
    @classmethod
    def get_mime_type(cls, filename: str) -> str:
        """
        Retourne le type MIME d'un fichier basé sur son extension.
        
        Args:
            filename: Nom du fichier
            
        Returns:
            Type MIME ou 'application/octet-stream' si inconnu
        """
        ext = Path(filename).suffix.lower()
        return cls.MIME_TYPES.get(ext, 'application/octet-stream')
    
    @classmethod
    def get_max_size_for_format(cls, format_type: str) -> int:
        """
        Retourne la taille maximale pour un type de format.
        
        Args:
            format_type: 'pdf', 'word', 'excel', ou 'image'
            
        Returns:
            Taille maximale en bytes
        """
        size_map = {
            'pdf': cls.MAX_PDF_SIZE,
            'word': cls.MAX_DOC_SIZE,
            'excel': cls.MAX_DOC_SIZE,
            'image': cls.MAX_IMAGE_SIZE
        }
        return size_map.get(format_type, cls.MAX_IMAGE_SIZE)
    
    @classmethod
    def get_conversion_temp_dir(cls, conversion_type: str = "general") -> Path:
        """
        Retourne le chemin du dossier temporaire pour un type de conversion.
        
        Args:
            conversion_type: 'images', 'pdf', 'word', 'excel'
            
        Returns:
            Chemin Path du dossier
        """
        if conversion_type in ['images', 'pdf', 'word', 'excel']:
            return cls.TEMP_FOLDER / "conversion_temp" / conversion_type
        return cls.TEMP_FOLDER / "conversion_temp"
    
    @classmethod
    def cleanup_old_files(cls, max_age_seconds: int = None):
        """
        Nettoie les fichiers temporaires plus vieux que max_age_seconds.
        
        Args:
            max_age_seconds: Âge max en secondes (défaut: TEMP_FILE_EXPIRY)
        """
        if max_age_seconds is None:
            max_age_seconds = cls.TEMP_FILE_EXPIRY
        
        import time
        current_time = time.time()
        
        # Nettoyer les dossiers de conversion
        conversion_dirs = [
            cls.get_conversion_temp_dir(),
            cls.get_conversion_temp_dir('images'),
            cls.get_conversion_temp_dir('pdf'),
            cls.get_conversion_temp_dir('word'),
            cls.get_conversion_temp_dir('excel'),
            cls.TEMP_FOLDER / cls.UPLOADS_FOLDER
        ]
        
        cleaned_count = 0
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
