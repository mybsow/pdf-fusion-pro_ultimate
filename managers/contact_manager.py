import json
from pathlib import Path
from threading import Lock
from datetime import datetime
# Avant (si utils)
from utils.contact_manager import contact_manager

# Après (correct si tu utilises la version manager)
#from managers.contact_manager import contact_manager


from pathlib import Path
from datetime import datetime
import json

class ContactManager:
    def __init__(self):
        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"
        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self._cache = None

    def save_contact_to_json(self, form_data, flask_request=None):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_email = form_data['email'].split('@')[0][:20] \
                .replace('.', '_').replace('+', '_')

            filename = f"contact_{timestamp}_{safe_email}.json"
            filepath = self.contacts_dir / filename

            contact_data = {
                **form_data,
                "received_at": datetime.now().isoformat(),
                "ip_address": flask_request.remote_addr if flask_request else None,
                "user_agent": flask_request.user_agent.string if flask_request else None,
                "status": "pending"
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(contact_data, f, ensure_ascii=False, indent=2)

            self._cache = None  # invalider cache
            return True

        except Exception as e:
            print(f"❌ Erreur sauvegarde contact: {e}")
            return False

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
