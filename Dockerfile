# Use official Python image
FROM python:3.13-slim

# Install system dependencies including tesseract and poppler
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-script-latn \
    poppler-utils \
    gcc \
    g++ \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Verify tesseract installation during build
RUN tesseract --version
RUN which tesseract
RUN ls -la /usr/bin/tesseract*

# Set environment variables for tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/
ENV PATH="/usr/bin:${PATH}"

# Set work directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles uploads

# Expose port
EXPOSE 10000

# Create comprehensive startup script
RUN echo '#!/bin/bash\n\
echo "=== Starting Django App ==="\n\
echo "Environment PATH: $PATH"\n\
echo "TESSDATA_PREFIX: $TESSDATA_PREFIX"\n\
echo "Tesseract installation check:"\n\
which tesseract || echo "tesseract not found in which"\n\
ls -la /usr/bin/tesseract* || echo "no tesseract files in /usr/bin"\n\
echo "Tesseract version:"\n\
tesseract --version || echo "tesseract --version failed"\n\
echo "Tesseract list languages:"\n\
tesseract --list-langs || echo "tesseract --list-langs failed"\n\
echo "Python tesseract test:"\n\
python -c "import pytesseract; print(f\"pytesseract tesseract_cmd: {pytesseract.pytesseract.tesseract_cmd}\"); from PIL import Image; img = Image.new(\"RGB\", (100, 50), \"white\"); print(f\"OCR test: {pytesseract.image_to_string(img)}\")" || echo "Python tesseract test failed"\n\
echo "Poppler utilities:"\n\
which pdftoppm || echo "pdftoppm not found"\n\
which pdfinfo || echo "pdfinfo not found"\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput --clear\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
echo "Starting Gunicorn..."\n\
exec gunicorn backend.wsgi:application --bind 0.0.0.0:10000 --workers 2 --timeout 120\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start the app
CMD ["/app/start.sh"]
