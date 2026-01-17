import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
import time

class RatingManager:
    def __init__(self):
        self.lock = Lock()
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.ratings_dir = BASE_DIR / "data" / "ratings"
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        self._cache = None
        self._cache_time = 0

    # ================================
    # Lecture avec cache (5 secondes)
    # ================================
    def _load(self, force_refresh=False):
        current_time = time.time()
        
        if force_refresh or self._cache is None or current_time - self._cache_time > 5:
            ratings = []
            try:
                for file in sorted(self.ratings_dir.glob("rating_*.json"), reverse=True):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            
                            # Champs par défaut
                            data.setdefault("seen", False)
                            data.setdefault("rating", 0)
                            data.setdefault("feedback", "")
                            data.setdefault("page", "/")
                            
                            # ID fichier
                            data["file_id"] = file.name
                            
                            # Date lisible
                            try:
                                dt = datetime.fromisoformat(data.get("timestamp", "").replace('Z', '+00:00'))
                                data["display_date"] = dt.strftime("%d/%m/%Y %H:%M")
                            except Exception:
                                data["display_date"] = "-"
                            
                            ratings.append(data)
                    except Exception as e:
                        print(f"Erreur lecture rating {file}: {e}")
                        continue
            except Exception as e:
                print(f"Erreur glob ratings: {e}")
            
            self._cache = ratings
            self._cache_time = current_time
        
        return self._cache

    def get_all_ratings(self, force_refresh=False):
        return self._load(force_refresh)

    def save_rating(self, data: dict):
        with self.lock:
            try:
                # Créer un nom de fichier unique
                timestamp = datetime.utcnow()
                filename = f"rating_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
                filepath = self.ratings_dir / filename
                
                payload = {
                    "id": filename.replace('.json', ''),
                    "timestamp": timestamp.isoformat() + "Z",
                    "rating": int(data.get("rating", 0)),
                    "feedback": data.get("feedback", ""),
                    "page": data.get("page", "/"),
                    "user_agent": data.get("user_agent", ""),
                    "ip": data.get("ip", ""),
                    "seen": False
                }
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                
                # Invalider le cache
                self._cache = None
                
                print(f"Rating enregistré: {filepath}")
                return True
                
            except Exception as e:
                print(f"Erreur enregistrement rating: {e}")
                return False

    def mark_all_seen(self):
        """Marque toutes les évaluations comme vues"""
        ratings = self._load()
        for r in ratings:
            if not r.get("seen", False):
                file_id = r.get("file_id")
                if file_id:
                    try:
                        filepath = self.ratings_dir / file_id
                        with open(filepath, "r+", encoding="utf-8") as f:
                            data = json.load(f)
                            data["seen"] = True
                            f.seek(0)
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            f.truncate()
                    except Exception:
                        continue
        
        self._cache = None
        return True

    def delete_rating(self, rating_id):
        """Supprime une évaluation"""
        filepath = self.ratings_dir / f"{rating_id}.json"
        if filepath.exists():
            filepath.unlink()
        
        # Invalider le cache
        self._cache = None
        return True

    # -----------------------
    # Stats
    # -----------------------
    def get_stats(self):
        ratings = self._load()
        total = len(ratings)
        
        if total == 0:
            return {
                "total": 0,
                "average": 0,
                "distribution": {i: 0 for i in range(1, 6)},
                "unseen": 0,
                "recent_count": 0,
                "recent_percentage": 0,
                "comments": 0
            }
        
        # Distribution des notes
        distribution = {i: 0 for i in range(1, 6)}
        total_comments = 0
        unseen = 0
        
        for r in ratings:
            rating_value = r.get("rating", 0)
            if 1 <= rating_value <= 5:
                distribution[rating_value] += 1
            
            if r.get("feedback", "").strip():
                total_comments += 1
            
            if not r.get("seen", False):
                unseen += 1
        
        # Moyenne
        avg = sum(r.get("rating", 0) for r in ratings) / total
        
        # Récent (7 derniers jours)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent = 0
        for r in ratings:
            try:
                timestamp = datetime.fromisoformat(r.get("timestamp", "").replace('Z', '+00:00'))
                if timestamp > recent_cutoff:
                    recent += 1
            except Exception:
                continue
        
        return {
            "total": total,
            "average": round(avg, 1),
            "distribution": distribution,
            "unseen": unseen,
            "recent_count": recent,
            "recent_percentage": round((recent / total * 100), 1) if total else 0,
            "comments": total_comments
        }

# ================================
# Instance globale
# ================================
rating_manager = RatingManager()
