"""
Gestionnaire centralisé des évaluations (SINGLETON)
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock

class RatingManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.file_path = self.data_dir / "ratings.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

        if not self.file_path.exists():
            self._save([])

    # -----------------------
    # I/O interne
    # -----------------------
    def _load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, ratings):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(ratings, f, indent=2, ensure_ascii=False)

    # -----------------------
    # API publique
    # -----------------------
    def get_all_ratings(self):
        return self._load()

    def add_rating(self, rating: int, comment="", user="anonymous"):
        with self._lock:
            ratings = self._load()
            ratings.append({
                "id": f"rating_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
                "rating": rating,
                "comment": comment,
                "user": user,
                "seen": False,
                "timestamp": datetime.utcnow().isoformat()
            })
            self._save(ratings[-1000:])  # sécurité

    def delete_rating(self, rating_id):
        with self._lock:
            ratings = [r for r in self._load() if r["id"] != rating_id]
            self._save(ratings)

    def mark_all_seen(self):
        with self._lock:
            ratings = self._load()
            for r in ratings:
                r["seen"] = True
            self._save(ratings)

    # -----------------------
    # Stats
    # -----------------------
    def get_stats(self):
        ratings = self._load()
        total = len(ratings)

        distribution = {i: 0 for i in range(1, 6)}
        for r in ratings:
            distribution[r["rating"]] += 1

        avg = round(sum(r["rating"] for r in ratings) / total, 1) if total else 0
        unseen = sum(1 for r in ratings if not r["seen"])

        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent = sum(
            1 for r in ratings
            if datetime.fromisoformat(r["timestamp"]) > recent_cutoff
        )

        return {
            "total": total,
            "average": avg,
            "distribution": distribution,
            "unseen": unseen,
            "recent_count": recent,
            "recent_percentage": round((recent / total * 100), 1) if total else 0
        }

# Singleton unique
rating_manager = RatingManager()
