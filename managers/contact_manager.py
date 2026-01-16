# managers/contact_manager.py
import json
from pathlib import Path
from datetime import datetime

class ContactManager:
    def __init__(self, storage_file="data/contacts.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_file.exists():
            self._write([])

    def _read(self):
        with self.storage_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with self.storage_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # -----------------------
    # CRUD Méthodes
    # -----------------------

    def save_message(self, name, email, subject, message):
        """Enregistre un message"""
        all_messages = self._read()
        new_msg = {
            "id": len(all_messages) + 1,
            "name": name,
            "email": email,
            "subject": subject,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "seen": False,
        }
        all_messages.append(new_msg)
        self._write(all_messages)
        return new_msg

    def get_all(self):
        return self._read()

    def get_all_sorted(self, reverse=True):
        """Retourne tous les messages triés par date descendante"""
        return sorted(self.get_all(), key=lambda m: m.get("timestamp", ""), reverse=reverse)

    def get_unseen_count(self):
        return sum(1 for m in self.get_all() if not m.get("seen", False))

    def mark_all_seen(self):
        messages = self.get_all()
        for m in messages:
            m["seen"] = True
        self._write(messages)

    def delete_message(self, message_id):
        messages = [m for m in self.get_all() if m["id"] != message_id]
        self._write(messages)

    def archive_message(self, message_id, archive_file="data/contacts_archive.json"):
        archive_path = Path(archive_file)
        if not archive_path.exists():
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            archive_path.write_text("[]")
        archived = []
        messages = self.get_all()
        remaining = []
        for m in messages:
            if m["id"] == message_id:
                archived.append(m)
            else:
                remaining.append(m)
        if archived:
            old_data = json.loads(archive_path.read_text())
            old_data.extend(archived)
            archive_path.write_text(json.dumps(old_data, indent=2, ensure_ascii=False))
        self._write(remaining)

# =========================
# INSTANCE GLOBALE EXPORTÉE
# =========================
contact_manager = ContactManager()
