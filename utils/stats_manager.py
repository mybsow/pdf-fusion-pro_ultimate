"""
Gestionnaire des statistiques d'utilisation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from config import AppConfig

class StatisticsManager:
    """Gestionnaire des statistiques d'utilisation"""
    
    def __init__(self):
        AppConfig.initialize()
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