"""
Gestionnaire centralisé des évaluations
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

class RatingsManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.file_path = self.data_dir / "ratings.json"
        self.data_dir.mkdir(exist_ok=True)

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self, ratings):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(ratings, f, indent=2, ensure_ascii=False)

    def save_rating(self, rating_data):
        ratings = self._load()

        rating_data.update({
            "id": f"rating_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat()
        })

        ratings.append(rating_data)

        if len(ratings) > 1000:
            ratings = ratings[-1000:]

        self._save(ratings)

    def get_all(self):
        return self._load()

    def get_stats(self):
        ratings = self._load()
        total = len(ratings)

        distribution = {i: 0 for i in range(1, 6)}
        for r in ratings:
            distribution[r["rating"]] += 1

        average = round(
            sum(r["rating"] for r in ratings) / total, 1
        ) if total else 0

        recent_cutoff = datetime.now() - timedelta(days=1)
        recent_count = sum(
            1 for r in ratings
            if datetime.fromisoformat(r["timestamp"]) > recent_cutoff
        )

        return {
            "total": total,
            "average": average,
            "distribution": distribution,
            "recent_count": recent_count
        }

ratings_manager = RatingsManager()
