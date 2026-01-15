import json
from pathlib import Path
from threading import Lock

class ContactManager:
    def __init__(self):
        self.lock = Lock()
        self.contacts_dir = Path("data/contacts")
        self.archive_dir = self.contacts_dir / "archived"

        self.contacts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _read_dir(self, directory):
        messages = []
        for file in sorted(directory.glob("msg_*.json"), reverse=True):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["id"] = file.name
                    data.setdefault("seen", False)
                    messages.append(data)
            except Exception:
                continue
        return messages

    def get_all(self):
        return self._read_dir(self.contacts_dir)

    def get_archived(self):
        return self._read_dir(self.archive_dir)

    def get_unseen_count(self):
        return sum(1 for m in self.get_all() if not m.get("seen"))

    def mark_all_seen(self):
        for file in self.contacts_dir.glob("msg_*.json"):
            try:
                with open(file, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data["seen"] = True
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            except Exception:
                pass

    def archive(self, message_id):
        src = self.contacts_dir / message_id
        if src.exists():
            src.rename(self.archive_dir / message_id)

    def delete(self, message_id):
        for folder in (self.contacts_dir, self.archive_dir):
            file = folder / message_id
            if file.exists():
                file.unlink()

contact_manager = ContactManager()
