web: gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
release: python manage.py collectstatic --noinput && python manage.py migrate
