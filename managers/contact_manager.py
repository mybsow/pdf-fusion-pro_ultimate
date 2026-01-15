import json
from pathlib import Path
from threading import Lock
from datetime import datetime

class ContactManager:
    def __init__(self):
        self.lock = Lock()
        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"
        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self._cache = None  # cache en mémoire

    # ================================
    # Lecture messages
    # ================================
    def get_all(self, limit=None):
        """Retourne tous les messages triés par date (latest first). limit=int pour pagination"""
        messages = []
        files = sorted(self.contacts_dir.glob("msg_*.json"), reverse=True)
        if limit:
            files = files[:limit]
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["id"] = file.name
                    data.setdefault("seen", False)
                    messages.append(data)
            except Exception:
                continue
        return messages

    def get_unseen_count(self):
        return sum(1 for m in self.get_all() if not m.get("seen"))

    # ================================
    # Ajout / sauvegarde
    # ================================
    def save_message(self, message):
        """Enregistre un nouveau message"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = self.contacts_dir / f"msg_{timestamp}.json"
        with self.lock:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(message, f, ensure_ascii=False, indent=2)

    # ================================
    # Mise à jour
    # ================================
    def mark_all_seen(self):
        """Marque tous les messages comme lus"""
        for file in self.contacts_dir.glob("msg_*.json"):
            try:
                with self.lock, open(file, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data["seen"] = True
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            except Exception:
                pass

    def mark_seen(self, message_id):
        """Marque un message spécifique comme lu"""
        file = self.contacts_dir / message_id
        if file.exists():
            with self.lock, open(file, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["seen"] = True
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.truncate()

    # ================================
    # Suppression / Archivage
    # ================================
    def delete(self, message_id):
        file = self.contacts_dir / message_id
        if file.exists():
            file.unlink()

    def archive(self, message_id):
        src = self.contacts_dir / message_id
        if src.exists():
            dst = self.archive_dir / message_id
            src.rename(dst)

# Instance globale
contact_manager = ContactManager()
