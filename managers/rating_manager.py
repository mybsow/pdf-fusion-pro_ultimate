import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

class RatingManager:
    def __init__(self):
        self.lock = Lock()
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.ratings_dir = BASE_DIR / "data" / "ratings"
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        self._cache = None  # Cache interne

    # ================================
    # Lecture avec cache
    # ================================
    def _load(self):
        if self._cache is None:
            ratings = []
            for file in sorted(self.ratings_dir.glob("rating_*.json"), reverse=True):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
    
                        # Champs par défaut
                        data.setdefault("seen", False)
                        data.setdefault("rating", 0)
    
                        # ➕ ID fichier (utile admin)
                        data["id"] = file.name
    
                        # ➕ Date lisible pour dashboard
                        try:
                            dt = datetime.fromisoformat(data.get("timestamp"))
                            data["display_date"] = dt.strftime("%d/%m/%Y %H:%M")
                        except Exception:
                            data["display_date"] = "-"
    
                        ratings.append(data)
                except Exception:
                    continue
    
            self._cache = ratings
    
        return self._cache


    def get_all_ratings(self):
        return self._load()

    def mark_all_seen(self):
        for file in self.ratings_dir.glob("rating_*.json"):
            try:
                with open(file, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data["seen"] = True
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            except Exception:
                continue
        self._cache = None
        
    def save_rating(self, data: dict):
        with self.lock:
            timestamp = datetime.utcnow().isoformat()
            filename = f"rating_{timestamp.replace(':', '').replace('.', '')}.json"
            filepath = self.ratings_dir / filename
    
            payload = {
                "timestamp": timestamp,
                "rating": data.get("rating"),
                "feedback": data.get("feedback"),
                "page": data.get("page"),
                "user_agent": data.get("user_agent"),
                "ip": data.get("ip"),
                "seen": False
            }
    
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
    
            self._cache = None




    def delete_rating(self, rating_id):
        file = self.ratings_dir / rating_id
        if file.exists():
            file.unlink()
        self._cache = None

    # -----------------------
    # Stats
    # -----------------------
    def get_stats(self):
        ratings = self._load()
        total = len(ratings)
        distribution = {i: 0 for i in range(1, 6)}
        total_comments = 0
        for r in ratings:
            rating_value = r.get("rating", 0)
            if 1 <= rating_value <= 5:
                distribution[rating_value] += 1
            if r.get("feedback"):
                total_comments += 1
    
        avg = round(sum(r.get("rating", 0) for r in ratings) / total, 1) if total else 0
        unseen = sum(1 for r in ratings if not r.get("seen", False))
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent = sum(
            1 for r in ratings
            if datetime.fromisoformat(r.get("timestamp", "1970-01-01T00:00:00")) > recent_cutoff
        )
    
        return {
            "total": total,
            "average": avg,
            "distribution": distribution,
            "unseen": unseen,
            "recent_count": recent,
            "recent_percentage": round((recent / total * 100), 1) if total else 0,
            "comments": total_comments  # <-- ajouté
        }


# ================================
# Instance globale
# ================================
rating_manager = RatingManager()






