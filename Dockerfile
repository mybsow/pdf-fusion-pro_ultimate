# Dockerfile - Version corrigée
FROM python:3.11-slim

# 1. INSTALLER TESSERACT (sans libgl1-mesa-glx obsolète)
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 2. VÉRIFIER L'INSTALLATION
RUN which tesseract && tesseract --version
RUN which pdftoppm && pdftoppm -v 2>&1 | head -1

# 3. VÉRIFIER LES LANGUES
RUN tesseract --list-langs

# 4. CRÉER L'ENVIRONNEMENT
WORKDIR /app

# 5. COPIER ET INSTALLER PYTHON
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. COPIER L'APP
COPY . .

# 7. PORT
EXPOSE 10000

# 8. COMMANDE
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2"]
