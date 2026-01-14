"""
Gestionnaire centralisé des évaluations
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

class RatingsManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.file_path = self.data_dir / "ratings.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------
    # Chargement / sauvegarde interne
    # -------------------------------
    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("❌ _load:", e)
                return []
        return []

    def _save(self, ratings):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(ratings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("❌ _save:", e)

    # -------------------------------
    # Public methods
    # -------------------------------
    def get_all_ratings(self):
        """Retourne toutes les évaluations"""
        return self._load()

    def save_rating(self, rating_data: dict) -> bool:
        """Ajoute une évaluation"""
        try:
            ratings = self._load()

            rating_data.update({
                "id": f"rating_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "timestamp": datetime.now().isoformat(),
                "seen": False
            })

            ratings.append(rating_data)

            # Limite de sécurité : conserver max 1000
            ratings = ratings[-1000:]

            self._save(ratings)
            return True
        except Exception as e:
            print("❌ save_rating:", e)
            return False

    def mark_all_seen(self):
        """Marque toutes les évaluations comme vues"""
        ratings = self._load()
        for r in ratings:
            r["seen"] = True
        self._save(ratings)

    def delete_rating(self, rating_id: str) -> bool:
        """Supprime une évaluation par ID"""
        try:
            ratings = self._load()
            new_ratings = [r for r in ratings if r.get("id") != rating_id]
            if len(new_ratings) == len(ratings):
                return False  # Rien supprimé
            self._save(new_ratings)
            return True
        except Exception as e:
            print("❌ delete_rating:", e)
            return False

    def get_stats(self):
        """Retourne les statistiques des évaluations"""
        ratings = self._load()
        total = len(ratings)
        distribution = {i: 0 for i in range(1, 6)}
        for r in ratings:
            distribution[r["rating"]] += 1

        average = round(sum(r["rating"] for r in ratings) / total, 1) if total else 0
        unseen = sum(1 for r in ratings if not r.get("seen"))

        # Récents 7 jours
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_count = sum(
            1 for r in ratings
            if datetime.fromisoformat(r["timestamp"]) > recent_cutoff
        )
        recent_percentage = round((recent_count / total * 100), 1) if total else 0

        return {
            "total": total,
            "average": average,
            "distribution": distribution,
            "unseen": unseen,
            "recent_count": recent_count,
            "recent_percentage": recent_percentage
        }

# Singleton pour l'application
ratings_manager = RatingsManager()
