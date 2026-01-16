import json
from pathlib import Path
from datetime import datetime
from threading import Lock
import uuid

class ContactManager:
    def __init__(self, storage_file="data/contacts.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

        if not self.storage_file.exists():
            self._safe_write([])

    # ========================
    # IO sécurisées
    # ========================
    def _safe_read(self):
        try:
            if self.storage_file.stat().st_size == 0:
                return []

            with self.storage_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _safe_write(self, data):
        with self.lock:
            with self.storage_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # ========================
    # CRUD
    # ========================
    def save_message(self, first_name, last_name, email, phone, subject, message):
        """Enregistre un message de contact"""
        all_messages = self._safe_read()
    
        new_msg = {
            "id": len(all_messages) + 1,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "subject": subject,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "seen": False,
        }
    
        all_messages.append(new_msg)
        self._safe_write(all_messages)
        return new_msg



    def get_all(self):
        return self._safe_read()

    def get_all_sorted(self, reverse=True):
        return sorted(
            self.get_all(),
            key=lambda m: m.get("timestamp", ""),
            reverse=reverse,
        )

    def get_unseen_count(self):
        return sum(1 for m in self.get_all() if not m.get("seen", False))

    def mark_all_seen(self):
        messages = self.get_all()
        for m in messages:
            m["seen"] = True
        self._safe_write(messages)

    def delete_message(self, message_id):
        messages = [m for m in self.get_all() if m.get("id") != message_id]
        self._safe_write(messages)

    def archive_message(self, message_id, archive_file="data/contacts_archive.json"):
        archive_path = Path(archive_file)
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        archived = []
        remaining = []

        for m in self.get_all():
            if m.get("id") == message_id:
                archived.append(m)
            else:
                remaining.append(m)

        if archived:
            try:
                old_data = json.loads(archive_path.read_text(encoding="utf-8"))
                if not isinstance(old_data, list):
                    old_data = []
            except Exception:
                old_data = []

            old_data.extend(archived)
            archive_path.write_text(
                json.dumps(old_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        self._safe_write(remaining)

    def get_stats(self):
        messages = self.get_all()
        total = len(messages)
        unseen = sum(1 for m in messages if not m.get("seen", False))
    
        return {
            "total": total,
            "unseen": unseen,
        }



# =========================
# INSTANCE GLOBALE
# =========================
contact_manager = ContactManager()
