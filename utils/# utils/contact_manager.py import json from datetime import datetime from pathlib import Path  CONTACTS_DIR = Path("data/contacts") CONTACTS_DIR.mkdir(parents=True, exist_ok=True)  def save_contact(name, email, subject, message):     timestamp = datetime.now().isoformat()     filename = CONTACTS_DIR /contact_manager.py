# utils/contact_manager.py
import json
from datetime import datetime
from pathlib import Path

CONTACTS_DIR = Path("data/contacts")
CONTACTS_DIR.mkdir(parents=True, exist_ok=True)

def save_contact(name, email, subject, message):
    timestamp = datetime.now().isoformat()
    filename = CONTACTS_DIR / f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    data = {
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "timestamp": timestamp
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
