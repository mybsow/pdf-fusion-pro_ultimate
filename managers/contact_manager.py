import json
from datetime import datetime
from pathlib import Path
from threading import Lock


class ContactManager:
    def __init__(self):
        self.lock = Lock()

        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"

        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self._cache = None  # cache interne des messages

    # ================================
    # Chargement avec cache
    # ================================
    def get_all_sorted(self, reverse=True):
        """
        Retourne tous les messages triés par date (timestamp) descendante par défaut.
        """
        return sorted(self.get_all(), key=lambda m: m.get("timestamp", ""), reverse=reverse)
    
    def _load_cache(self):
        messages = []

        for file in sorted(self.contacts_dir.glob("msg_*.json"), reverse=True):
            try:
                with file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                data["id"] = file.name
                data.setdefault("seen", False)
                messages.append(data)

            except Exception:
                continue

        self._cache = messages

    def get_all(self):
        if self._cache is None:
            self._load_cache()
        return self._cache

    def get_unseen_count(self):
        if self._cache is None:
            self._load_cache()
        return sum(1 for m in self._cache if not m.get("seen", False))

    # ================================
    # Actions
    # ================================
    def mark_all_seen(self):
        with self.lock:
            for file in self.contacts_dir.glob("msg_*.json"):
                try:
                    with file.open("r+", encoding="utf-8") as f:
                        data = json.load(f)
                        data["seen"] = True
                        f.seek(0)
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.truncate()
                except Exception:
                    continue

            self._cache = None

    def delete(self, message_id: str):
        file = self.contacts_dir / message_id
        if file.exists():
            file.unlink()
        self._cache = None

    def archive(self, message_id: str):
        src = self.contacts_dir / message_id
        if src.exists():
            dst = self.archive_dir / message_id
            src.rename(dst)
        self._cache = None


# ================================
# Instance globale
# ================================
contact_manager = ContactManager()
