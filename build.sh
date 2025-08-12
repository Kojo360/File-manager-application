#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🚀 Starting build process..."

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📂 Collecting static files..."
python manage.py collectstatic --no-input --clear

echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

echo "✅ Build completed successfully!"
