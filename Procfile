release: python manage.py migrate && python manage.py create_admin
web: gunicorn backend.wsgi --log-file -
