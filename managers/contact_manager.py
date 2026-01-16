import json
import os
from threading import Lock
from datetime import datetime

class ContactManager:
    """
    Gestion des messages contact
    """
    def __init__(self, storage_file="data/messages.json"):
        self.storage_file = storage_file
        self._lock = Lock()
        self._cache_unseen = None

        # Création du dossier si nécessaire
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

    def save_message(self, first_name, last_name, email, phone, subject, message):
        try:
            with self._lock:
                messages = self._read_all()
                messages.append({
                    "id": len(messages)+1,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "subject": subject,
                    "message": message,
                    "seen": False,
                    "archived": False,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
                self._write_all(messages)
                self._cache_unseen = None
            return True
        except Exception:
            return False

    def get_all(self):
        return self._read_all()

    def get_all_sorted(self):
        return sorted(self.get_all(), key=lambda x: x.get("timestamp",""), reverse=True)

    def get_unseen_count(self):
        messages = self.get_all()
        return sum(1 for m in messages if not m.get("seen", False))

    def get_unseen_count_cached(self):
        if self._cache_unseen is None:
            self._cache_unseen = self.get_unseen_count()
        return self._cache_unseen

    def mark_all_seen(self):
        with self._lock:
            messages = self.get_all()
            for m in messages:
                m["seen"] = True
            self._write_all(messages)
            self._cache_unseen = 0

    def archive(self, message_id):
        with self._lock:
            messages = self.get_all()
            for m in messages:
                if str(m["id"]) == str(message_id):
                    m["archived"] = True
            self._write_all(messages)

    def delete(self, message_id):
        with self._lock:
            messages = [m for m in self.get_all() if str(m["id"]) != str(message_id)]
            self._write_all(messages)
            self._cache_unseen = None

# Singleton
contact_manager = ContactManager()
