def encode_image_to_pil(image_data):
    """Convertit toute entrée en PIL.Image de façon sûre."""
    try:
        # ✅ 1. Déjà une image PIL → ne rien faire
        if isinstance(image_data, Image.Image):
            return image_data

        # ✅ 2. Bytes
        if isinstance(image_data, (bytes, bytearray)):
            img = Image.open(BytesIO(image_data))
            img.load()
            return img

        # ✅ 3. Fichier (Flask, file upload)
        if hasattr(image_data, "read"):
            image_data.seek(0)
            img = Image.open(image_data)
            img.load()
            return img

        # ✅ 4. Chemin fichier
        if isinstance(image_data, str):
            img = Image.open(image_data)
            img.load()
            return img

        raise ValueError("Format non supporté: " + str(type(image_data)))

    except Exception as e:
        logger.error("Impossible d'ouvrir l'image: " + str(e))
        return None
