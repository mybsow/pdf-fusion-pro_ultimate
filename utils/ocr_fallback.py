"""
Fallback pour l'OCR quand Tesseract n'est pas disponible
"""

from config import AppConfig
import logging

logger = logging.getLogger(__name__)

class OCRFallback:
    """Gestion du fallback OCR"""
    
    @staticmethod
    def is_ocr_available():
        """Vérifie si l'OCR est disponible"""
        try:
            import pytesseract
            import shutil
            
            # Vérifier Tesseract
            if not shutil.which("tesseract"):
                logger.warning("Tesseract non trouvé dans PATH")
                return False
            
            # Vérifier pytesseract
            pytesseract.get_tesseract_version()
            return True
            
        except ImportError:
            logger.warning("pytesseract non installé")
            return False
        except Exception as e:
            logger.error(f"Erreur vérification OCR: {e}")
            return False
    
    @staticmethod
    def extract_text_from_image(image_path, languages=None):
        """
        Extrait le texte d'une image avec OCR ou fallback
        """
        if not AppConfig.OCR_ENABLED:
            return "OCR désactivé dans la configuration"
        
        if not OCRFallback.is_ocr_available():
            return "OCR non disponible. Tesseract n'est pas installé."
        
        try:
            import pytesseract
            from PIL import Image
            
            if languages is None:
                languages = AppConfig.OCR_LANGUAGES
            
            # Ouvrir l'image
            img = Image.open(image_path)
            
            # Configurer pytesseract
            pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")
            
            # Extraire le texte
            lang_str = '+'.join(languages[:3])  # Max 3 langues
            text = pytesseract.image_to_string(img, lang=lang_str)
            
            return text.strip() if text.strip() else "Aucun texte détecté"
            
        except Exception as e:
            logger.error(f"Erreur OCR: {e}")
            return f"Erreur lors de l'extraction OCR: {str(e)}"
