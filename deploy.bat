@echo off
echo 🚀 Deploying File Manager Application...

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo 📁 Collecting static files...
python manage.py collectstatic --noinput

echo 🗄️ Running migrations...
python manage.py migrate

echo 👤 Setting up admin user...
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@filemanager.app', 'admin123')"

echo ✅ Deployment complete!
echo 🌐 Application ready for production!

pause
