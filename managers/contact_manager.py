# managers/contact_manager.py

import json
import os
import time
from threading import Lock
from typing import List, Dict, Optional

CONTACT_DATA_FILE = "data/contacts.json"
CACHE_TTL_SECONDS = 30  # cache mémoire léger

class ContactManager:
    def __init__(self):
        self._lock = Lock()
        self._cache = {}
        self._cache_ts = {}

        os.makedirs(os.path.dirname(CONTACT_DATA_FILE), exist_ok=True)
        if not os.path.exists(CONTACT_DATA_FILE):
            with open(CONTACT_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

    # =========================
    # Utils internes
    # =========================

    def _load_all(self) -> List[Dict]:
        with self._lock:
            with open(CONTACT_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

    def _save_all(self, messages: List[Dict]) -> None:
        with self._lock:
            with open(CONTACT_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
        self._invalidate_cache()

    def _invalidate_cache(self):
        self._cache.clear()
        self._cache_ts.clear()

    def _get_cached(self, key: str, compute_fn):
        now = time.time()
        if key in self._cache and now - self._cache_ts[key] < CACHE_TTL_SECONDS:
            return self._cache[key]

        value = compute_fn()
        self._cache[key] = value
        self._cache_ts[key] = now
        return value

    # =========================
    # CRUD Messages
    # =========================

    def save_message(self, name: str, email: str, message: str) -> None:
        messages = self._load_all()
        messages.append({
            "id": int(time.time() * 1000),
            "name": name,
            "email": email,
            "message": message,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "seen": False,
            "archived": False
        })
        self._save_all(messages)

    def get_all(self, include_archived: bool = False) -> List[Dict]:
        messages = self._load_all()
        if not include_archived:
            messages = [m for m in messages if not m.get("archived")]
        return sorted(messages, key=lambda x: x["created_at"], reverse=True)

    def delete(self, message_id: int) -> bool:
        messages = self._load_all()
        new_messages = [m for m in messages if m["id"] != message_id]
        if len(new_messages) == len(messages):
            return False
        self._save_all(new_messages)
        return True

    def archive(self, message_id: int) -> bool:
        messages = self._load_all()
        for m in messages:
            if m["id"] == message_id:
                m["archived"] = True
                self._save_all(messages)
                return True
        return False

    def mark_all_seen(self) -> None:
        messages = self._load_all()
        for m in messages:
            m["seen"] = True
        self._save_all(messages)

    # =========================
    # Compteurs (ADMIN)
    # =========================

    def count_all(self) -> int:
        return self._get_cached(
            "count_all",
            lambda: len(self._load_all())
        )

    def get_unseen_count(self) -> int:
        return self._get_cached(
            "unseen_count",
            lambda: sum(1 for m in self._load_all() if not m.get("seen", False))
        )

    def get_unseen_count_cached(self) -> int:
        """
        Alias explicite pour admin.py (lisibilité + sécurité)
        """
        return self.get_unseen_count()


# Singleton
contact_manager = ContactManager()
