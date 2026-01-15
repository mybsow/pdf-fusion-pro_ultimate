import json
from pathlib import Path
from datetime import datetime
from threading import Lock


class RatingManager:
    def __init__(self):
        self.lock = Lock()

        # Compatibilité avec TES deux emplacements existants
        self.data_file = Path("data/ratings.json")
        self.legacy_dir = Path("data/ratings")
        self.legacy_file = self.legacy_dir / "ratings.json"

        # Créer dossiers si absents
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.legacy_dir.mkdir(parents=True, exist_ok=True)

        # Initialisation si fichiers inexistants
        if not self.data_file.exists():
            self._write([])
        if not self.legacy_file.exists():
            self._write([], legacy=True)

    # ======================================================
    # Internes
    # ======================================================
    def _read(self):
        """Lecture prioritaire data/ratings.json"""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write(self, data, legacy=False):
        target = self.legacy_file if legacy else self.data_file
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ======================================================
    # API publique
    # ======================================================
    def save_rating(self, rating_data: dict) -> bool:
        """Ajoute une évaluation"""
        with self.lock:
            ratings = self._read()

            rating_data["id"] = str(int(datetime.now().timestamp() * 1000))
            rating_data["timestamp"] = datetime.now().isoformat()
            rating_data["seen"] = False

            ratings.append(rating_data)

            self._write(ratings)
            self._write(ratings, legacy=True)

            return True

    def get_all_ratings(self):
        return self._read()

    def delete_rating(self, rating_id: str):
        with self.lock:
            ratings = self._read()
            ratings = [r for r in ratings if r.get("id") != rating_id]
            self._write(ratings)
            self._write(ratings, legacy=True)

    def mark_all_seen(self):
        with self.lock:
            ratings = self._read()
            for r in ratings:
                r["seen"] = True
            self._write(ratings)
            self._write(ratings, legacy=True)

    def get_stats(self):
        ratings = self._read()

        total = len(ratings)
        unseen = sum(1 for r in ratings if not r.get("seen"))
        avg = (
            round(sum(r.get("rating", 0) for r in ratings) / total, 2)
            if total > 0
            else 0
        )

        return {
            "total": total,
            "average": avg,
            "unseen": unseen
        }


# ======================================================
# Singleton utilisé partout dans l'app
# ======================================================
rating_manager = RatingManager()
