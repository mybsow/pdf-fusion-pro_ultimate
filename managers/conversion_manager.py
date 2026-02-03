#!/usr/bin/env python3
"""
Manager pour gérer les conversions de fichiers
"""

import os
import tempfile
import uuid
from pathlib import Path
from PIL import Image
import img2pdf
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import pandas as pd
from docx import Document
from docx.shared import Inches
import fitz  # PyMuPDF
import camelot

class ConversionManager:
    """Gère les conversions entre différents formats de fichiers."""
    
    def __init__(self, temp_dir='temp/conversion'):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_temp_file(self, extension=''):
        """Crée un fichier temporaire avec un nom unique."""
        filename = f"{uuid.uuid4().hex}{extension}"
        return self.temp_dir / filename
    
    def _cleanup_temp_files(self):
        """Nettoie les fichiers temporaires anciens."""
        for file in self.temp_dir.glob('*'):
            if file.stat().st_mtime < (time.time() - AppConfig.TEMP_FILE_EXPIRY):
                file.unlink()
    
    def images_to_pdf(self, image_files, orientation='portrait', margin=10, quality='medium'):
        """
        Convertit une liste d'images en PDF.
        
        Args:
            image_files: Liste de fichiers image
            orientation: 'portrait' ou 'landscape'
            margin: Marge en pixels
            quality: 'low', 'medium', 'high'
        
        Returns:
            Chemin vers le PDF généré
        """
        temp_images = []
        
        try:
            # Convertir chaque image
            for i, img_file in enumerate(image_files):
                temp_img_path = self._create_temp_file('.jpg')
                
                # Ouvrir et traiter l'image
                with Image.open(img_file) as img:
                    # Convertir en RGB si nécessaire
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Redimensionner selon la qualité
                    if quality == 'low':
                        img.thumbnail((800, 800))
                    elif quality == 'high':
                        # Garder la taille originale
                        pass
                    else:  # medium
                        img.thumbnail((1200, 1200))
                    
                    # Sauvegarder l'image temporaire
                    img.save(temp_img_path, 'JPEG', quality=95)
                    temp_images.append(temp_img_path)
            
            # Créer le PDF
            pdf_path = self._create_temp_file('.pdf')
            
            with open(pdf_path, 'wb') as f:
                # Options de mise en page
                layout_fun = img2pdf.get_layout_fun(
                    (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))  # A4
                )
                
                # Convertir les images en PDF
                f.write(img2pdf.convert(
                    [str(img) for img in temp_images],
                    layout_fun=layout_fun
                ))
            
            return pdf_path
            
        finally:
            # Nettoyer les images temporaires
            for img_path in temp_images:
                if img_path.exists():
                    img_path.unlink()
    
    def to_word(self, input_file, ocr_enabled=True, language='fra'):
        """
        Convertit une image ou PDF en document Word.
        
        Args:
            input_file: Fichier image ou PDF
            ocr_enabled: Activer la reconnaissance de texte
            language: Langue pour l'OCR
        
        Returns:
            Chemin vers le document Word
        """
        temp_docx = self._create_temp_file('.docx')
        doc = Document()
        
        try:
            filename = secure_filename(input_file.filename)
            ext = Path(filename).suffix.lower()
            
            if ext in ['.pdf']:
                # Convertir PDF en images
                temp_pdf = self._create_temp_file('.pdf')
                input_file.save(temp_pdf)
                
                # Convertir chaque page en image
                images = convert_from_path(str(temp_pdf), dpi=200)
                
                for i, image in enumerate(images):
                    # Ajouter l'image au document
                    temp_img = self._create_temp_file('.jpg')
                    image.save(temp_img, 'JPEG')
                    
                    # Ajouter au document Word
                    doc.add_picture(str(temp_img), width=Inches(6.5))
                    
                    # OCR si activé
                    if ocr_enabled:
                        text = pytesseract.image_to_string(image, lang=language)
                        if text.strip():
                            doc.add_paragraph(text)
                    
                    doc.add_page_break()
                
                # Nettoyer
                temp_pdf.unlink()
                
            else:
                # Traiter comme une image
                temp_img = self._create_temp_file(ext)
                input_file.save(temp_img)
                
                # Ajouter l'image
                doc.add_picture(str(temp_img), width=Inches(6.5))
                
                # OCR si activé
                if ocr_enabled:
                    image = Image.open(temp_img)
                    text = pytesseract.image_to_string(image, lang=language)
                    if text.strip():
                        doc.add_paragraph(text)
            
            # Sauvegarder le document
            doc.save(temp_docx)
            return temp_docx
            
        except Exception as e:
            raise Exception(f"Erreur lors de la conversion en Word: {str(e)}")
    
    def to_excel(self, input_file, detect_tables=True, language='fra'):
        """
        Convertit une image ou PDF en fichier Excel.
        
        Args:
            input_file: Fichier image ou PDF
            detect_tables: Détecter automatiquement les tableaux
            language: Langue pour l'OCR
        
        Returns:
            Chemin vers le fichier Excel
        """
        temp_excel = self._create_temp_file('.xlsx')
        writer = pd.ExcelWriter(temp_excel, engine='openpyxl')
        
        try:
            filename = secure_filename(input_file.filename)
            ext = Path(filename).suffix.lower()
            
            if ext == '.csv':
                # Convertir CSV directement en Excel
                df = pd.read_csv(input_file)
                df.to_excel(writer, sheet_name='Données', index=False)
                
            elif ext == '.pdf':
                # Traiter le PDF
                temp_pdf = self._create_temp_file('.pdf')
                input_file.save(temp_pdf)
                
                if detect_tables:
                    # Essayer d'extraire les tableaux avec Camelot
                    try:
                        tables = camelot.read_pdf(str(temp_pdf), pages='all')
                        for i, table in enumerate(tables):
                            if table.df.empty:
                                continue
                            table.df.to_excel(
                                writer, 
                                sheet_name=f'Tableau_{i+1}', 
                                index=False, 
                                header=False
                            )
                    except:
                        # Fallback: utiliser l'OCR
                        self._pdf_to_excel_ocr(temp_pdf, writer, language)
                
                else:
                    # Utiliser l'OCR uniquement
                    self._pdf_to_excel_ocr(temp_pdf, writer, language)
                
                temp_pdf.unlink()
                
            else:
                # Traiter comme une image
                temp_img = self._create_temp_file(ext)
                input_file.save(temp_img)
                
                # Utiliser OpenCV pour détecter les tableaux
                if detect_tables:
                    data = self._extract_tables_from_image(temp_img, language)
                else:
                    data = self._extract_text_from_image(temp_img, language)
                
                # Créer une feuille Excel
                for sheet_name, df in data.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            writer.save()
            return temp_excel
            
        except Exception as e:
            raise Exception(f"Erreur lors de la conversion en Excel: {str(e)}")
    
    def _pdf_to_excel_ocr(self, pdf_path, excel_writer, language):
        """Convertit un PDF en Excel via OCR."""
        # Implémenter la conversion PDF->Excel via OCR
        images = convert_from_path(str(pdf_path), dpi=200)
        
        all_data = []
        for i, image in enumerate(images):
            # Utiliser Tesseract pour extraire le texte
            text = pytesseract.image_to_string(image, lang=language)
            
            # Traiter le texte pour créer un DataFrame
            lines = text.split('\n')
            data = []
            for line in lines:
                if line.strip():
                    # Séparer par tabulations ou espaces multiples
                    row = [cell.strip() for cell in line.split('\t') if cell.strip()]
                    if row:
                        data.append(row)
            
            if data:
                # Créer un DataFrame
                max_cols = max(len(row) for row in data)
                for row in data:
                    while len(row) < max_cols:
                        row.append('')
                
                df = pd.DataFrame(data)
                df.to_excel(
                    excel_writer, 
                    sheet_name=f'Page_{i+1}', 
                    index=False, 
                    header=False
                )
    
    def _extract_tables_from_image(self, image_path, language):
        """Extrait les tableaux d'une image."""
        # Implémenter la détection de tableaux avec OpenCV
        image = cv2.imread(str(image_path))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Détection des contours
        edges = cv2.Canny(gray, 50, 150)
        
        # Recherche des lignes avec Hough Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                                minLineLength=100, maxLineGap=10)
        
        # Pour simplifier, retourner tout le texte
        return self._extract_text_from_image(image_path, language)
    
    def _extract_text_from_image(self, image_path, language):
        """Extrait le texte d'une image via OCR."""
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=language)
        
        # Convertir en DataFrame
        lines = text.split('\n')
        data = []
        for line in lines:
            if line.strip():
                row = [cell.strip() for cell in line.split('\t') if cell.strip()]
                if row:
                    data.append(row)
        
        df = pd.DataFrame(data) if data else pd.DataFrame()
        return {'Feuille1': df}
