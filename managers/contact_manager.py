import json
from pathlib import Path
from datetime import datetime
from threading import Lock

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
            if not self.storage_file.exists() or self.storage_file.stat().st_size == 0:
                return []

            with self.storage_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Erreur lecture contacts: {e}")
            return []

    def _safe_write(self, data):
        with self.lock:
            try:
                with self.storage_file.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            except Exception as e:
                print(f"Erreur écriture contacts: {e}")

    # ========================
    # CRUD
    # ========================
    def save_message(self, **kwargs):
        """Enregistre un message de contact"""
        messages = self._safe_read()
        
        # Générer un ID unique
        if messages:
            new_id = max(msg.get("id", 0) for msg in messages) + 1
        else:
            new_id = 1
        
        new_msg = {
            "id": new_id,
            "first_name": kwargs.get("first_name", ""),
            "last_name": kwargs.get("last_name", ""),
            "email": kwargs.get("email", ""),
            "phone": kwargs.get("phone", ""),
            "subject": kwargs.get("subject", ""),
            "message": kwargs.get("message", ""),
            "timestamp": datetime.now().isoformat(),
            "seen": False,
            "archived": False
        }
        
        messages.append(new_msg)
        self._safe_write(messages)
        return True

    def get_all_sorted(self, archived=False):
        """Récupère tous les messages, triés par date"""
        messages = self._safe_read()
        filtered = [m for m in messages if m.get("archived", False) == archived]
        
        return sorted(
            filtered,
            key=lambda m: m.get("timestamp", ""),
            reverse=True
        )

    def get_unseen_count(self):
        """Compte les messages non lus"""
        messages = self._safe_read()
        return sum(1 for m in messages if not m.get("seen", False) and not m.get("archived", False))

    def mark_all_seen(self):
        """Marque tous les messages comme lus"""
        messages = self._safe_read()
        for m in messages:
            m["seen"] = True
        self._safe_write(messages)
        return True

    def mark_seen(self, message_id):
        """Marque un message spécifique comme lu"""
        messages = self._safe_read()
        for m in messages:
            if m.get("id") == message_id:
                m["seen"] = True
                break
        self._safe_write(messages)
        return True

    def archive_message(self, message_id):
        """Archive un message"""
        messages = self._safe_read()
        for m in messages:
            if m.get("id") == message_id:
                m["archived"] = True
                m["seen"] = True
                break
        self._safe_write(messages)
        return True

    def delete(self, message_id):
        """Supprime un message"""
        messages = self._safe_read()
        messages = [m for m in messages if m.get("id") != message_id]
        self._safe_write(messages)
        return True

    def get_stats(self):
        """Récupère les statistiques"""
        messages = self._safe_read()
        active = [m for m in messages if not m.get("archived", False)]
        
        return {
            "total": len(active),
            "unseen": sum(1 for m in active if not m.get("seen", False)),
            "archived": sum(1 for m in messages if m.get("archived", False))
        }

# =========================
# INSTANCE GLOBALE
# =========================
contact_manager = ContactManager()
