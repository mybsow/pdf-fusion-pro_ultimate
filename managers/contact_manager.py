import json
import os
from threading import Lock
from datetime import datetime

"""
Gestionnaire centralisé des messages de contact
"""


class ContactManager:
    def __init__(self):
        self._lock = Lock()
        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"

        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self._cache = None  # lazy cache

    # ================================
    # Cache interne
    # ================================
    def _load_cache(self):
        messages = []

        for file in sorted(self.contacts_dir.glob("msg_*.json"), reverse=True):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["id"] = file.name
                    data.setdefault("seen", False)
                    messages.append(data)
            except Exception:
                continue

        self._cache = messages

    def _invalidate_cache(self):
        self._cache = None

    # ================================
    # Lecture
    # ================================
    def get_all(self):
        if self._cache is None:
            self._load_cache()
        return self._cache

    def get_unseen_count(self):
        if self._cache is None:
            self._load_cache()
        return sum(1 for m in self._cache if not m.get("seen", False))

    # ================================
    # Écriture
    # ================================
    def mark_all_seen(self):
        with self._lock:
            for file in self.contacts_dir.glob("msg_*.json"):
                try:
                    with open(file, "r+", encoding="utf-8") as f:
                        data = json.load(f)
                        data["seen"] = True
                        f.seek(0)
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.truncate()
                except Exception:
                    continue

            self._invalidate_cache()

    def delete(self, message_id: str):
        with self._lock:
            file = self.contacts_dir / message_id
            if file.exists():
                file.unlink()
            self._invalidate_cache()

    def archive(self, message_id: str):
        with self._lock:
            src = self.contacts_dir / message_id
            if src.exists():
                dst = self.archive_dir / message_id
                src.rename(dst)
            self._invalidate_cache()


# ================================
# Singleton applicatif
# ================================
contact_manager = ContactManager()
