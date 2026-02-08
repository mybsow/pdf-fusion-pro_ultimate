# Dockerfile
FROM python:3.11-slim

# 1. Installer Tesseract OCR (AU BUILD TIME - avec permissions root)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Vérifier l'installation
RUN which tesseract && tesseract --version
RUN which pdftoppm && pdftoppm -v 2>&1 | head -1

# 3. Installer les packages Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copier l'application
COPY . .

# 5. Port et commande
EXPOSE 10000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2"]
