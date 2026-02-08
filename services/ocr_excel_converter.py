import tempfile
import os
import gc

from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract

from openpyxl import Workbook
from PIL import Image