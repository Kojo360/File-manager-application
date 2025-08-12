# Dockerfile - OPTION B (backup if apt.txt doesn't work)
FROM python:3.13-slim

# Install apt packages including tesseract and poppler
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      poppler-utils \
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

# Expose port and run Gunicorn
ENV PORT 10000
CMD gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
