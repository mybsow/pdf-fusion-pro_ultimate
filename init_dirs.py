# init_dirs.py
import os
from pathlib import Path

def init_app_directories():
    """
    Crée les répertoires nécessaires pour l'application
    À appeler au démarrage de l'application
    """
    directories = [
        'data/contacts',    # Pour les messages de contact
        'uploads',          # Pour les uploads temporaires
        'temp',             # Pour les fichiers temporaires
        'logs'              # Pour les logs d'application
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Dossier créé/vérifié: {directory}")
        except Exception as e:
            print(f"⚠️ Erreur création dossier {directory}: {e}")
    
    return True

# Test
if __name__ == "__main__":
    init_app_directories()