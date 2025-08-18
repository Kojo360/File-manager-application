# 🚀 File Manager Application - Deployment Guide

A comprehensive Django-based file management system with OCR capabilities, document processing, and secure file management.

## 📋 Pre-Deployment Checklist

✅ **Application Status:**
- Django 5.2.4 with clean architecture
- Core apps: backend, core, ocr
- Login system working (fixed namespace issues)
- OCR processing functional
- Search and download features working
- Admin dashboard accessible

✅ **Files Ready:**
- `requirements.txt` - Optimized dependencies (15 packages)
- `Procfile` - Heroku/Railway web process
- `Dockerfile` - Container deployment
- `railway.yaml` - Railway configuration
- `deploy.bat` - Windows deployment script
- Production settings configured

## 🌐 Deployment Options

### Option 1: 🚂 Railway (Recommended - Easy & Free)

**Steps:**
1. **Connect Repository:**
   ```bash
   # Your repo is at: https://github.com/Kojo360/File-manager-application
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `Kojo360/File-manager-application`
   - Railway will auto-detect Django and deploy

3. **Environment Variables:**
   ```
   DJANGO_SETTINGS_MODULE=backend.settings_production
   DEBUG=false
   SECRET_KEY=your-secret-key-here
   ```

4. **Database:** Railway provides PostgreSQL automatically

### Option 2: 🎨 Render (Alternative Free Option)

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Deploy Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure Deployment**
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command:** `gunicorn backend.wsgi`
   - **Environment:** Python 3
   - **Instance Type:** Free tier

4. **Set Environment Variables**
   ```
   DJANGO_SETTINGS_MODULE=backend.settings_production
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ```

5. **Add PostgreSQL Database**
   - In Render dashboard: "New +" → "PostgreSQL"
   - Connect it to your web service
   - Database URL will be automatically added

### Option 3: 🐳 Docker (Self-Hosted)

**Steps:**
```bash
# Build and run locally
docker build -t file-manager .
docker run -p 8000:8000 -e PORT=8000 file-manager

# Or use docker-compose
docker-compose up --build
```

### Option 4: ☁️ Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from heroku.com/cli
   ```

### Option 4: ☁️ Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from heroku.com/cli
   ```

2. **Deploy**
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku addons:create heroku-postgresql:hobby-dev
   heroku config:set DJANGO_SETTINGS_MODULE=backend.settings_production
   heroku config:set SECRET_KEY=your-secret-key
   ```

## 🔧 Environment Variables

**Required for Production:**
```env
DJANGO_SETTINGS_MODULE=backend.settings_production
DEBUG=false
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgres://... (provided by platform)
```

**Optional:**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure-admin-password
```

## 📁 File Structure (Production Ready)

```
File-manager-application/
├── backend/                 # Django configuration
│   ├── settings.py         # Development settings
│   ├── settings_production.py  # Production settings
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI application
├── core/                   # Authentication & landing
├── ocr/                    # File processing & OCR
├── media/                  # User uploads
├── static/                 # Static assets
├── staticfiles/            # Collected static files
├── requirements.txt        # Dependencies (15 packages)
├── Procfile               # Process configuration
├── Dockerfile             # Container configuration
├── railway.yaml           # Railway deployment
├── deploy.bat             # Windows deployment
└── manage.py              # Django management
```

## 🛡️ Security Features

✅ **Production Security:**
- DEBUG=False in production
- Secure secret key management
- HTTPS redirect configuration
- CSRF protection enabled
- XSS protection headers
- Content type nosniff headers
- Secure cookie settings

## 🔍 Testing Deployment

**After deployment, test these features:**
1. **Home Page:** Landing page loads correctly
2. **Login System:** Admin login works without namespace errors
3. **File Upload:** OCR processing functions
4. **Search:** Document search returns results
5. **Download:** File download works correctly
6. **Admin Panel:** Django admin accessible

## 📞 Support & Monitoring

**Health Check Endpoint:** `/health/` (if configured)
**Admin Panel:** `/admin/`
**API Status:** All core endpoints functional

## 🎯 Quick Deploy Commands

**Railway:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

**Local Testing:**
```bash
# Test production settings locally
python manage.py runserver --settings=backend.settings_production
```

## ✅ Post-Deployment

1. **Create Admin User:**
   - Access `/admin/`
   - Use: `admin` / `admin123` (change in production!)

2. **Upload Test Files:**
   - Test OCR processing
   - Verify search functionality

3. **Configure DNS:**
   - Point your domain to deployment URL
   - Update ALLOWED_HOSTS in production settings

## 📱 Access Your App

Once deployed, you'll get a URL like:
- **Railway:** `https://your-app-name.up.railway.app`
- **Render:** `https://your-app-name.onrender.com`
- **Heroku:** `https://your-app-name.herokuapp.com`
- **Docker:** `http://localhost:8000` (local)

## 🔧 Local Development

1. **Clone and Setup**
   ```bash
   git clone https://github.com/Kojo360/File-manager-application.git
   cd File-manager-application
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

3. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

## 📋 Core Features

- 📁 **File Upload & Management** - Secure file upload with OCR processing
- 🔍 **Document Search** - Full-text search across processed files
- 📊 **Processing Statistics** - Track OCR processing and user activity
- 🔒 **Authentication System** - Secure login with role-based access
- 📱 **Mobile Responsive** - Works on all devices
- 🎯 **Clean Interface** - Simplified navigation and user experience

## 🛠️ Troubleshooting

### Common Issues

1. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic --clear
   ```

2. **Database Issues**
   ```bash
   python manage.py migrate --run-syncdb
   ```

3. **OCR Not Working**
   - Ensure Tesseract is installed on your deployment platform
   - Check deployment logs for OCR library errors

4. **Login Errors**
   - Verify namespace references are removed
   - Check Django settings configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | Database connection | SQLite |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost` |

## 🔄 Updates

To update your deployed app:
1. Push changes to GitHub
2. Deployment will automatically trigger
3. Check deployment logs for any issues

## 📞 Support

For issues or questions:
- Check the deployment logs first
- Review Django documentation
- Test locally with production settings
- Verify environment variables are set correctly

---

**🎉 Your File Manager Application is ready for production deployment!**

Choose your preferred platform and follow the steps above. The application is optimized, secure, and ready to handle real-world usage.

## 📱 Access Your App

Once deployed, you'll get a URL like:
- **Render:** `https://your-app-name.onrender.com`
- **Vercel:** `https://your-app-name.vercel.app`
- **Railway:** `https://your-app-name.up.railway.app`

## 🔧 Local Development

1. **Clone and Setup**
   ```bash
   git clone https://github.com/Kojo360/File-manager-application.git
   cd File-manager-application
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

4. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

## 📋 Features

- 📁 **File Upload & Management** - Multiple file upload with OCR processing
- 🔍 **Advanced Search & Filtering** - Filter by status, type, date, size
- 📊 **Comprehensive Statistics** - Processing metrics and analytics
- 🎯 **Smart Navigation** - Clickable cards with smooth scrolling
- 📱 **Mobile Responsive** - Works on all devices
- 🔒 **Secure** - Production-ready security settings

## 🛠️ Troubleshooting

### Common Issues

1. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic --clear
   ```

2. **Database Issues**
   ```bash
   python manage.py migrate --run-syncdb
   ```

3. **OCR Not Working**
   - Install Tesseract on your deployment platform
   - For Render: Add to `build.sh`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `False` |
| `DATABASE_URL` | Database connection | SQLite |
| `ALLOWED_HOST` | Allowed hosts | `localhost` |

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check the deployment logs
- Review Django documentation

## 🔄 Updates

To update your deployed app:
1. Push changes to GitHub
2. Deployment will automatically trigger
3. Check deployment logs for any issues

---

**Happy Deploying! 🎉**
