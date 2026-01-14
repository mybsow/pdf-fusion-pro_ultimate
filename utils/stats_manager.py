"""
Gestionnaire des statistiques d'utilisation
"""

import json
from datetime import datetime
from pathlib import Path

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
        
        # Structure complète des statistiques
        return {
            "app_name": "PDF Fusion Pro",
            "version": "6.1",
            "total_operations": 0,
            "merges": 0,
            "splits": 0,
            "rotations": 0,
            "compressions": 0,
            "user_sessions": 0,
            "zip_downloads": 0,
            "previews": 0,
            "first_use": datetime.now().isoformat(),
            "last_use": datetime.now().isoformat(),
            "daily_stats": {},
            "monthly_stats": {},
        }
    
    def save(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except:
            pass
    
    def new_session(self):
        """Enregistre une nouvelle session utilisateur"""
        self.stats["user_sessions"] += 1
        self.stats["last_use"] = datetime.now().isoformat()
        self.save()
    
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

    def get_stat(self, key: str, default=0):
        """Récupère une statistique de manière sécurisée"""
        return self.stats.get(key, default)


# Instance globale
stats_manager = StatisticsManager()
