# Dockerfile - Version corrigée
FROM python:3.11-slim

<<<<<<< HEAD
=======
# 1. INSTALLER TESSERACT (sans libgl1-mesa-glx obsolète)
>>>>>>> 259f28d5e4e4eb85876f4f22f67234bbbf18059c
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

<<<<<<< HEAD
RUN which tesseract && tesseract --version
RUN tesseract --list-langs

=======
# 2. VÉRIFIER L'INSTALLATION
RUN which tesseract && tesseract --version
RUN tesseract --list-langs
RUN which pdftoppm && pdftoppm -v 2>&1 | head -1

# 3. VÉRIFIER LES LANGUES
RUN tesseract --list-langs

# 4. CRÉER L'ENVIRONNEMENT
>>>>>>> 259f28d5e4e4eb85876f4f22f67234bbbf18059c
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

<<<<<<< HEAD
COPY . .

EXPOSE 10000
=======
# 5. COPIER ET INSTALLER PYTHON
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. COPIER L'APP
COPY . .

# 7. PORT
EXPOSE 10000

# 8. COMMANDE
>>>>>>> 259f28d5e4e4eb85876f4f22f67234bbbf18059c
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2"]
