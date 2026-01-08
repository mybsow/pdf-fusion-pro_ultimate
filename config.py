"""
Configuration centrale de l'application PDF Fusion Pro
"""

import os
from pathlib import Path

class AppConfig:
    # Attributs simples (pas de Path ici)
    VERSION = "6.1-Material-Pro"
    NAME = "PDF Fusion Pro"
    DEVELOPER_NAME = "MYBSOW"
    DEVELOPER_EMAIL = "banousow@gmail.com"
    HOSTING = "Render Cloud Platform"
    DOMAIN = "pdf-fusion-pro-ultimate.onrender.com"
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-123")
    MAX_CONTENT_SIZE = 50 * 1024 * 1024
    
    ADSENSE_CLIENT_ID = "pub-8967416460526921"
    ADSENSE_PUBLISHER_ID = "ca-pub-8967416460526921"
    
    STATS_FILE = "usage_stats.json"
    
    # TEMP_FOLDER sera défini dans initialize()
    TEMP_FOLDER = None
    
    @classmethod
    def initialize(cls):
        """Initialise les répertoires nécessaires"""
        cls.TEMP_FOLDER = Path("/tmp/pdf_fusion_pro")
        cls.TEMP_FOLDER.mkdir(exist_ok=True)