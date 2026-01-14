"""
Gestionnaire centralisé des évaluations
"""

import json
from pathlib import Path
from datetime import datetime

class RatingsManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.ratings_file = self.data_dir / "ratings.json"
        self.data_dir.mkdir(exist_ok=True)

    def get_all_ratings(self):
        if not self.ratings_file.exists():
            return []
        try:
            with open(self.ratings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_rating(self, rating_data: dict) -> bool:
        try:
            ratings = self.get_all_ratings()

            rating_data["id"] = f"rating_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            rating_data["timestamp"] = datetime.now().isoformat()
            rating_data["seen"] = False  # 👈 badge “nouveau”

            ratings.append(rating_data)

            ratings = ratings[-1000:]  # limite sécurité

            with open(self.ratings_file, "w", encoding="utf-8") as f:
                json.dump(ratings, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print("❌ save_rating:", e)
            return False

    def mark_all_seen(self):
        ratings = self.get_all_ratings()
        for r in ratings:
            r["seen"] = True

        with open(self.ratings_file, "w", encoding="utf-8") as f:
            json.dump(ratings, f, indent=2, ensure_ascii=False)

    def get_stats(self):
        ratings = self.get_all_ratings()
        total = len(ratings)

        distribution = {i: 0 for i in range(1, 6)}
        for r in ratings:
            distribution[r["rating"]] += 1

        avg = round(sum(r["rating"] for r in ratings) / total, 1) if total else 0
        unseen = sum(1 for r in ratings if not r.get("seen"))

        return {
            "total": total,
            "average": avg,
            "distribution": distribution,
            "unseen": unseen
        }

ratings_manager = RatingsManager()
