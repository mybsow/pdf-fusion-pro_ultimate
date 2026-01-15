import json
from pathlib import Path
from datetime import datetime
from threading import Lock

class RatingManager:
    def __init__(self):
        self.lock = Lock()
        self.ratings_dir = Path("data/ratings")
        self.ratings_file = self.ratings_dir / "ratings.json"
        self.ratings_dir.mkdir(parents=True, exist_ok=True)
        if not self.ratings_file.exists():
            with open(self.ratings_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    # ================================
    # Lecture
    # ================================
    def get_all_ratings(self):
        with self.lock:
            try:
                with open(self.ratings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for r in data:
                        r.setdefault("seen", False)
                    return data
            except Exception:
                return []

    def get_stats(self):
        ratings = self.get_all_ratings()
        total = len(ratings)
        unseen = sum(1 for r in ratings if not r.get("seen"))
        average = round(sum(r.get("rating", 0) for r in ratings)/total, 2) if total else 0
        return {"total": total, "unseen": unseen, "average": average}

    # ================================
    # Écriture
    # ================================
    def save_rating(self, rating_data):
        with self.lock:
            ratings = self.get_all_ratings()
            rating_data.setdefault("timestamp", datetime.now().isoformat())
            rating_data.setdefault("seen", False)
            ratings.append(rating_data)
            with open(self.ratings_file, "w", encoding="utf-8") as f:
                json.dump(ratings, f, ensure_ascii=False, indent=2)
        return True

    # ================================
    # Gestion
    # ================================
    def mark_all_seen(self):
        with self.lock:
            ratings = self.get_all_ratings()
            for r in ratings:
                r["seen"] = True
            with open(self.ratings_file, "w", encoding="utf-8") as f:
                json.dump(ratings, f, ensure_ascii=False, indent=2)

    def delete_rating(self, timestamp):
        with self.lock:
            ratings = self.get_all_ratings()
            ratings = [r for r in ratings if r.get("timestamp") != timestamp]
            with open(self.ratings_file, "w", encoding="utf-8") as f:
                json.dump(ratings, f, ensure_ascii=False, indent=2)

# Instance globale
ratings_manager = RatingManager()
