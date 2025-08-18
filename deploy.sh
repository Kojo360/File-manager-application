#!/bin/bash

echo "🚀 Preparing File Manager for Deployment..."

# Make build script executable
chmod +x build.sh
chmod +x build_files.sh

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Create admin user
echo "👤 Creating admin user..."
python manage.py create_admin

echo "✅ Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Push to GitHub: git add . && git commit -m 'Deploy to production' && git push"
echo "2. Deploy to Render: Connect your GitHub repo at https://render.com"
echo "3. Deploy to Vercel: Run 'vercel --prod' in terminal"
echo ""
echo "🌐 Your app will be accessible from any device once deployed!"
