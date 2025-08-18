@echo off
echo 🚀 Deploying File Manager Application...

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo 📁 Collecting static files...
python manage.py collectstatic --noinput

echo 🗄️ Running migrations...
python manage.py migrate

echo 👤 Setting up admin user...
python manage.py create_admin

echo ✅ Deployment complete!
echo 🌐 Application ready for production!

pause
