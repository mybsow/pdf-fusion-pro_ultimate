#!/usr/bin/env python3
"""
Validation des fichiers uploadés
"""

import os
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF

class FileValidation:
    """Classe pour valider les fichiers uploadés."""
    
    @staticmethod
    def validate_file(file, allowed_extensions, max_size=None):
        """
        Valide un fichier uploadé.
        
        Args:
            file: Fichier uploadé
            allowed_extensions: Liste des extensions autorisées
            max_size: Taille maximale en bytes
        
        Returns:
            bool: True si le fichier est valide
        """
        if not file or file.filename == '':
            return False
        
        # Vérifier l'extension
        filename = file.filename
        if '.' not in filename:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            return False
        
        # Vérifier la taille
        if max_size:
            # Sauvegarder la position actuelle
            current_position = file.tell()
            file.seek(0, 2)  # Aller à la fin
            size = file.tell()
            file.seek(current_position)  # Revenir à la position initiale
            
            if size > max_size:
                return False
        
        # Vérifier que c'est un fichier valide
        try:
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']:
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
                
            elif ext in ['.doc', '.docx', '.xls', '.xlsx', '.csv', '.ods']:
                # Pour les documents, juste vérifier qu'on peut les lire
                file.seek(0)
                content = file.read(1024)  # Lire les premiers bytes
                file.seek(0)
                
        except Exception as e:
            print(f"Erreur de validation du fichier {filename}: {e}")
            return False
        
        return True
    
    @staticmethod
    def get_file_type(filename):
        """
        Détermine le type de fichier.
        
        Args:
            filename: Nom du fichier
        
        Returns:
            str: Type de fichier
        """
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']:
            return 'image'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.doc', '.docx']:
            return 'word'
        elif ext in ['.xls', '.xlsx', '.csv', '.ods']:
            return 'excel'
        else:
            return 'unknown'
    
    @staticmethod
    def get_mime_type(filename):
        """
        Retourne le type MIME d'un fichier.
        
        Args:
            filename: Nom du fichier
        
        Returns:
            str: Type MIME
        """
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.ods': 'application/vnd.oasis.opendocument.spreadsheet'
        }
        
        ext = os.path.splitext(filename)[1].lower()
        return mime_map.get(ext, 'application/octet-stream')

# Fonction utilitaire pour la compatibilité
def validate_file(file, allowed_extensions, max_size=None):
    """Fonction wrapper pour la compatibilité."""
    return FileValidation.validate_file(file, allowed_extensions, max_size)
