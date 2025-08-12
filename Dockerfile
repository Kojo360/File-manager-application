# Use official Python image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils gcc && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Run migrations
RUN python manage.py migrate --noinput

# Expose port
EXPOSE 10000

# Start the app
CMD ["gunicorn", "backend.wsgi:application", "--bind", ":10000"]
