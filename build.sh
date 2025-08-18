#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "📦 Installing system dependencies for OCR..."
echo "Updating package lists..."
apt-get update

echo "Installing tesseract-ocr and poppler-utils..."
apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils

echo "Verifying tesseract installation..."
tesseract --version || echo "⚠️ Tesseract not found in PATH"

echo "Verifying poppler installation..."
pdftoppm -h > /dev/null 2>&1 && echo "✅ Poppler installed" || echo "⚠️ Poppler not found"

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📂 Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

echo "👤 Creating admin user..."
python manage.py create_admin

echo "✅ Build completed successfully!"
