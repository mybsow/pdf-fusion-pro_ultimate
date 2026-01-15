import json
from datetime import datetime
from pathlib import Path
from threading import Lock

class ContactManager:
    def __init__(self):
        self.lock = Lock()
        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"

        # Création des dossiers si inexistants
        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    # =======================================
    # Sauvegarde d'un message de contact
    # =======================================
    def save_contact_to_json(self, first_name, last_name, email, subject, message):
        timestamp = datetime.now().isoformat()
        filename = self.contacts_dir / f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip().lower(),
            "subject": subject.strip(),
            "message": message.strip(),
            "timestamp": timestamp,
            "seen": False  # marqueur non lu
        }
        try:
            with self.lock:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("Erreur sauvegarde message:", e)
            return False

    # =======================================
    # Récupérer tous les messages
    # =======================================
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

    # =======================================
    # Nombre de messages non lus
    # =======================================
    def get_unseen_count(self):
        return sum(1 for m in self.get_all() if not m.get("seen", False))

    # =======================================
    # Marquer tous les messages comme lus
    # =======================================
    def mark_all_seen(self):
        for file in self.contacts_dir.glob("msg_*.json"):
            try:
                with self.lock:
                    with open(file, "r+", encoding="utf-8") as f:
                        data = json.load(f)
                        data["seen"] = True
                        f.seek(0)
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.truncate()
            except Exception:
                continue

    # =======================================
    # Supprimer un message
    # =======================================
    def delete(self, message_id):
        file = self.contacts_dir / message_id
        if file.exists():
            file.unlink()

    # =======================================
    # Archiver un message
    # =======================================
    def archive(self, message_id):
        src = self.contacts_dir / message_id
        if src.exists():
            dst = self.archive_dir / message_id
            src.rename(dst)


# =======================================
# Instance globale
# =======================================
contact_manager = ContactManager()
