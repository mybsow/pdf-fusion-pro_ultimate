import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

class RatingManager:
    def __init__(self):
        self.lock = Lock()
        self.ratings_dir = Path("data/ratings")
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
                        data.setdefault("seen", False)
                        data.setdefault("rating", 0)
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
            ts = datetime.utcnow().isoformat()
    
            payload = {
                "rating": int(data.get("rating", 0)),
                "feedback": data.get("feedback", ""),
                "page": data.get("page", "/"),
                "timestamp": ts,
                "seen": False,
                "user_agent": data.get("user_agent", ""),
                "ip": data.get("ip", "")
            }
    
            filename = f"rating_{ts.replace(':', '').replace('.', '')}.json"
            file_path = self.ratings_dir / filename
    
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
    
            # Invalider le cache
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




