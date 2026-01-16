import json
import os
from datetime import datetime
from threading import Lock
from utils.rating_manager import rating_manager

class RatingManager:
    """
    Gestion des notes / évaluations
    """
    def __init__(self, storage_file="data/ratings.json"):
        self.storage_file = storage_file
        self._lock = Lock()
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, "w") as f:
                json.dump([], f)

    def _read_all(self):
        with open(self.storage_file, "r") as f:
            return json.load(f)

    def _write_all(self, data):
        with open(self.storage_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_rating(self, user, score, comment=""):
        with self._lock:
            ratings = self._read_all()
            ratings.append({
                "id": len(ratings)+1,
                "user": user,
                "score": score,
                "comment": comment,
                "seen": False,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            self._write_all(ratings)

    def get_all_ratings(self):
        return self._read_all()

    def get_stats(self):
        ratings = self.get_all_ratings()
        total = len(ratings)
        avg = round(sum(r["score"] for r in ratings)/total,2) if total else 0
        comments = sum(1 for r in ratings if r.get("comment"))
        return {"total": total, "avg": avg, "comments": comments}

    def mark_all_seen(self):
        with self._lock:
            ratings = self.get_all_ratings()
            for r in ratings:
                r["seen"] = True
            self._write_all(ratings)

    def delete_rating(self, rating_id):
        with self._lock:
            ratings = [r for r in self.get_all_ratings() if str(r["id"]) != str(rating_id)]
            self._write_all(ratings)

# Singleton
rating_manager = RatingManager()

