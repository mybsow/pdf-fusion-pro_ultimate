# managers/contact_manager.py

import json
from pathlib import Path
from datetime import datetime
from threading import Lock


class ContactManager:
    def __init__(self):
        self.lock = Lock()
        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"

        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    # ================================
    # 1️⃣ Sauvegarde d'un nouveau message de contact
    # ================================
    def save_contact_to_json(self, form_data):
        """
        form_data = {
            'first_name': str,
            'last_name': str,
            'email': str,
            'subject': str,
            'message': str
        }
        """
        timestamp = datetime.now().isoformat()
        filename = self.contacts_dir / f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.json"
        data = form_data.copy()
        data["timestamp"] = timestamp
        data["seen"] = False  # Nouveau message non lu

        try:
            with self.lock, open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du message: {e}")
            return False

    # ================================
    # 2️⃣ Récupérer tous les messages
    # ================================
    def get_all(self):
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
        return messages

    # ================================
    # 3️⃣ Nombre de messages non lus
    # ================================
    def get_unseen_count(self):
        return sum(1 for m in self.get_all() if not m.get("seen"))

    # ================================
    # 4️⃣ Marquer tous les messages comme lus
    # ================================
    def mark_all_seen(self):
        for file in self.contacts_dir.glob("msg_*.json"):
            try:
                with self.lock, open(file, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data["seen"] = True
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            except Exception:
                continue

    # ================================
    # 5️⃣ Supprimer un message
    # ================================
    def delete(self, message_id):
        file = self.contacts_dir / message_id
        if file.exists():
            file.unlink()

    # ================================
    # 6️⃣ Archiver un message
    # ================================
    def archive(self, message_id):
        src = self.contacts_dir / message_id
        if src.exists():
            dst = self.archive_dir / message_id
            src.rename(dst)


# ================================
# Instance globale à utiliser partout
# ================================
contact_manager = ContactManager()
