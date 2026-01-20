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
    DOMAIN = os.environ.get("APP_DOMAIN", "localhost:5000")

   
    
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
