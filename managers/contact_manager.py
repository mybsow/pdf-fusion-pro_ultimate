import json
from pathlib import Path
from datetime import datetime
from threading import Lock

class ContactManager:
    def __init__(self, storage_file="data/contacts.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        
        # S'assurer que le fichier existe et est valide
        self._ensure_valid_file()

    def _ensure_valid_file(self):
        """S'assure que le fichier contacts.json existe et est valide"""
        if not self.storage_file.exists():
            self._safe_write([])
            print(f"✅ Fichier contacts.json créé: {self.storage_file}")
            return True
        
        # Vérifier si le fichier est valide
        try:
            if self.storage_file.stat().st_size == 0:
                self._safe_write([])
                print("✅ Fichier contacts.json réinitialisé (était vide)")
                return True
                
            with self.storage_file.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self._safe_write([])
                    print("✅ Fichier contacts.json réinitialisé (contenu vide)")
                    return True
                    
                # Tester si le JSON est valide
                json.loads(content)
                print(f"✅ Fichier contacts.json valide: {len(json.loads(content))} messages")
                return True
                
        except json.JSONDecodeError as e:
            print(f"❌ Fichier contacts.json invalide. Réparation... Erreur: {e}")
            # Créer une sauvegarde
            backup = self.storage_file.with_suffix('.json.backup')
            try:
                self.storage_file.rename(backup)
                print(f"📁 Backup créé: {backup}")
            except:
                pass
            
            # Créer un nouveau fichier
            self._safe_write([])
            print("✅ Nouveau fichier contacts.json créé")
            return True
            
        except Exception as e:
            print(f"⚠️  Erreur vérification fichier contacts: {e}")
            return False

    # ========================
    # IO sécurisées
    # ========================
    def _safe_read(self):
        try:
            if not self.storage_file.exists() or self.storage_file.stat().st_size == 0:
                return []

            with self.storage_file.open("r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                
                data = json.loads(content)
                return data if isinstance(data, list) else []
                
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON dans contacts.json. Réinitialisation. Erreur: {e}")
            # Réinitialiser le fichier
            try:
                self._safe_write([])
            except:
                pass
            return []
        except Exception as e:
            print(f"Erreur lecture contacts: {e}")
            return []

    def _safe_write(self, data):
        with self.lock:
            try:
                with self.storage_file.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                return True
            except Exception as e:
                print(f"Erreur écriture contacts: {e}")
                return False

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
        if self._safe_write(messages):
            print(f"✅ Message enregistré: ID {new_id}, de {new_msg['first_name']} {new_msg['last_name']}")
            return True
        else:
            print(f"❌ Erreur enregistrement message")
            return False

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
        return self._safe_write(messages)

    def mark_seen(self, message_id):
        """Marque un message spécifique comme lu"""
        messages = self._safe_read()
        updated = False
        for m in messages:
            if m.get("id") == message_id:
                m["seen"] = True
                updated = True
                break
        if updated:
            return self._safe_write(messages)
        return False

    def archive_message(self, message_id):
        """Archive un message"""
        messages = self._safe_read()
        updated = False
        for m in messages:
            if m.get("id") == message_id:
                m["archived"] = True
                m["seen"] = True
                updated = True
                break
        if updated:
            return self._safe_write(messages)
        return False

    def delete(self, message_id):
        """Supprime un message"""
        messages = self._safe_read()
        original_count = len(messages)
        messages = [m for m in messages if m.get("id") != message_id]
        
        if len(messages) < original_count:
            if self._safe_write(messages):
                print(f"✅ Message {message_id} supprimé")
                return True
        
        return False

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
