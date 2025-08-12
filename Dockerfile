# Use official Python image
FROM python:3.13-slim

# Install system dependencies including tesseract and poppler
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Verify tesseract installation
RUN tesseract --version

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

# Create startup script
RUN echo '#!/bin/bash\n\
echo "=== Starting Django App ==="\n\
echo "Tesseract version:"\n\
tesseract --version\n\
echo "Python path for tesseract:"\n\
python -c "import pytesseract; print(pytesseract.pytesseract.tesseract_cmd)"\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput --clear\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
echo "Starting Gunicorn..."\n\
exec gunicorn backend.wsgi:application --bind 0.0.0.0:10000 --workers 2 --timeout 120\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start the app
CMD ["/app/start.sh"]
