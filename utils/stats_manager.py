"""
Gestionnaire des statistiques d'utilisation
"""

import json
from datetime import datetime
from pathlib import Path

# Version indépendante de config.py
class StatisticsManager:
    def __init__(self):
        # Valeurs par défaut
        self.TEMP_FOLDER = Path("/tmp/pdf_fusion_pro")
        self.STATS_FILE = "usage_stats.json"
        
        # Initialiser
        self.TEMP_FOLDER.mkdir(exist_ok=True)
        self.file_path = self.TEMP_FOLDER / self.STATS_FILE
        self.stats = self._load_stats()
    
    def _load_stats(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_operations": 0,
            "first_use": datetime.now().isoformat(),
            "last_use": datetime.now().isoformat()
        }
    
    def save(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except:
            pass

# Instance globale
stats_manager = StatisticsManager()