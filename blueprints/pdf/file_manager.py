import os
import uuid
import tempfile


class TempFileManager:
    """
    Gestion ultra safe des fichiers temporaires.
    Evite :
    - RAM spikes
    - workers killed
    - EOF
    """

    @staticmethod
    def save_upload(file):
        if not file or file.filename == "":
            raise ValueError("Fichier invalide")

        if not file.filename.lower().endswith(".pdf"):
            raise ValueError("Le fichier doit être un PDF")

        tmp_dir = tempfile.gettempdir()

        filename = f"{uuid.uuid4()}.pdf"
        path = os.path.join(tmp_dir, filename)

        file.save(path)

        if os.path.getsize(path) == 0:
            os.remove(path)
            raise ValueError("Fichier vide")

        return path

    @staticmethod
    def cleanup(paths):
        for p in paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
