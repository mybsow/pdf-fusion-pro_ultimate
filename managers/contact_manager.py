import json
from pathlib import Path
from threading import Lock
from datetime import datetime
# Avant (si utils)
from utils.contact_manager import contact_manager

# Après (correct si tu utilises la version manager)
#from managers.contact_manager import contact_manager



import uuid


class ContactManager:
    def __init__(self):
        self.lock = Lock()

        self.base_dir = Path("data/contacts")
        self.archive_dir = self.base_dir / "archived"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    # =====================================================
    # SAUVEGARDE
    # =====================================================
    def save_contact_to_json(self, form_data: dict, request=None) -> bool:
        """
        Sauvegarde un message de contact dans un fichier JSON.
        """
        try:
            message_id = f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
            filepath = self.base_dir / message_id

            payload = {
                "id": message_id,
                "first_name": form_data.get("first_name"),
                "last_name": form_data.get("last_name"),
                "email": form_data.get("email"),
                "phone": form_data.get("phone"),
                "subject": form_data.get("subject"),
                "message": form_data.get("message"),
                "seen": False,
                "archived": False,
                "created_at": datetime.utcnow().isoformat(),
                "meta": {
                    "ip": request.remote_addr if request else None,
                    "user_agent": request.user_agent.string if request else None,
                },
            }

            with self.lock:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

            return True

        except Exception:
            return False

    # =====================================================
    # LECTURE
    # =====================================================
    def get_all(self, include_archived: bool = False) -> list:
        """
        Retourne tous les messages (non archivés par défaut).
        """
        messages = []

        directory = self.base_dir if not include_archived else None
        files = self.base_dir.glob("msg_*.json")

        for file in sorted(files, reverse=True):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not include_archived and data.get("archived"):
                        continue
                    messages.append(data)
            except Exception:
                continue

        return messages

    def get_unseen_count(self) -> int:
        """
        Retourne le nombre de messages non lus.
        """
        return sum(1 for m in self.get_all() if not m.get("seen", False))

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
