# Dockerfile - Railway deployment with PostgreSQL support
FROM python:3.13-slim

# Install system dependencies including PostgreSQL dev libraries
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      poppler-utils \
      libpq-dev \
      gcc \
      build-essential \
 && rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /opt/app

# Copy requirements then install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files and run migrations
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate --noinput

# Expose port and run Gunicorn with proper PORT binding
ENV PORT=8000
CMD python manage.py migrate && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
