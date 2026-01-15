import json
from pathlib import Path
from datetime import datetime
from threading import Lock
import uuid


class RatingManager:
    def __init__(self):
        self.lock = Lock()

        self.base_dir = Path("data/ratings")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # =========================================
    # SAUVEGARDE
    # =========================================
    def save_rating(self, rating: int, comment: str = None) -> bool:
        try:
            rating_id = f"rating_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.json"
            filepath = self.base_dir / rating_id

            payload = {
                "id": rating_id,
                "rating": int(rating),
                "comment": comment,
                "created_at": datetime.utcnow().isoformat()
            }

            with self.lock:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            return False

    # =========================================
    # LECTURE
    # =========================================
    def get_all(self) -> list:
        ratings = []

        for file in self.base_dir.glob("rating_*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    ratings.append(json.load(f))
            except Exception:
                continue

        return ratings

    # =========================================
    # STATS
    # =========================================
    def get_stats(self) -> dict:
        ratings = self.get_all()

        if not ratings:
            return {
                "total": 0,
                "avg": 0,
                "comments": 0
            }

        total = len(ratings)
        avg = round(sum(r["rating"] for r in ratings) / total, 2)
        comments = sum(1 for r in ratings if r.get("comment"))

        return {
            "total": total,
            "avg": avg,
            "comments": comments
        }


rating_manager = RatingManager()
