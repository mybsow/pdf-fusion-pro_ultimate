# Dockerfile
FROM python:3.11-slim

# 1. INSTALLER TESSERACT
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 2. VÉRIFIER L'INSTALLATION
RUN which tesseract && tesseract --version
RUN which pdftoppm && pdftoppm -v 2>&1 | head -1

# 3. CRÉER L'ENVIRONNEMENT
WORKDIR /app

# 4. COPIER ET INSTALLER PYTHON
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. COPIER L'APP
COPY . .

# 6. PORT
EXPOSE 10000

# 7. COMMANDE
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2"]
