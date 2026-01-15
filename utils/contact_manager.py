# utils/contact_manager.py
import json
from pathlib import Path
from datetime import datetime

# Dossier pour stocker les messages
CONTACTS_DIR = Path("data/contacts")
CONTACTS_DIR.mkdir(parents=True, exist_ok=True)

def save_contact_to_json(form_data, request=None):
    """
    Enregistre le message de contact en JSON.
    form_data : dict contenant 'first_name', 'last_name', 'email', 'subject', 'message'
    request : objet Flask request (optionnel, pour IP / User-Agent)
    """
    timestamp = datetime.now().isoformat()
    filename = CONTACTS_DIR / f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    data = form_data.copy()
    data['timestamp'] = timestamp
    if request:
        data['ip'] = request.remote_addr
        data['user_agent'] = request.headers.get("User-Agent")
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement du message: {e}")
        return False
