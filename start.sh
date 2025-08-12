#!/bin/bash
set -e

# Set default port if PORT is not set
export PORT=${PORT:-8000}

echo "Starting Django application on port $PORT"

# Run migrations
python manage.py migrate --noinput

# Start gunicorn
exec gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
