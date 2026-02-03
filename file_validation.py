#!/usr/bin/env python3
"""
Validation des fichiers uploadés
"""

import os
from werkzeug.utils import secure_filename
from PIL import Image
import fitz

ALLOWED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'],
    'pdf': ['.pdf'],
    'document': ['.doc', '.docx', '.odt'],
    'spreadsheet': ['.xls', '.xlsx', '.ods', '.csv']
}

def allowed_file(filename, allowed_extensions):
    """
    Vérifie si le fichier a une extension autorisée.
    
    Args:
        filename: Nom du fichier
        allowed_extensions: Liste des extensions autorisées
    
    Returns:
        bool: True si l'extension est autorisée
    """
    if '.' not in filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

def validate_file(file, allowed_extensions, max_size=None):
    """
    Valide un fichier uploadé.
    
    Args:
        file: Fichier uploadé
        allowed_extensions: Extensions autorisées
        max_size: Taille maximale en bytes
    
    Returns:
        bool: True si le fichier est valide
    """
    if not file or file.filename == '':
        return False
    
    if not allowed_file(file.filename, allowed_extensions):
        return False
    
    if max_size:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > max_size:
            return False
    
    # Vérifier que c'est un fichier valide
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext in ALLOWED_EXTENSIONS['image']:
            # Vérifier que c'est une image valide
            file.seek(0)
            img = Image.open(file)
            img.verify()
            file.seek(0)
            
        elif ext == '.pdf':
            # Vérifier que c'est un PDF valide
            file.seek(0)
            pdf = fitz.open(stream=file.read(), filetype="pdf")
            pdf.close()
            file.seek(0)
            
    except Exception:
        return False
    
    return True

def get_file_type(filename):
    """
    Détermine le type de fichier.
    
    Args:
        filename: Nom du fichier
    
    Returns:
        str: Type de fichier
    """
    ext = os.path.splitext(filename)[1].lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    
    return 'unknown'
