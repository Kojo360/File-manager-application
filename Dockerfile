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

# Copy and make startup script executable
COPY start.sh .
RUN chmod +x start.sh

# Collect static files (build time)
RUN python manage.py collectstatic --noinput

# Expose port (Railway sets PORT at runtime)
EXPOSE 8000

# Use startup script
CMD ["./start.sh"]
