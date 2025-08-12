# File Manager Application - Deployment Guide

A comprehensive Django-based file management system with OCR capabilities, statistics tracking, and filtering features.

## 🚀 Quick Deploy Options

### Option 1: Deploy to Render (Recommended)

1. **Create a Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

2. **Connect Your Repository**
   - Push your code to GitHub
   - In Render dashboard, click "New +" → "Web Service"
   - Connect your GitHub repository

3. **Configure Deployment**
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn backend.wsgi:application`
   - **Environment:** Python 3
   - **Instance Type:** Free tier

4. **Set Environment Variables**
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   PYTHONPATH=/opt/render/project/src
   ```

5. **Add PostgreSQL Database**
   - In Render dashboard: "New +" → "PostgreSQL"
   - Connect it to your web service
   - Database URL will be automatically added

### Option 2: Deploy to Vercel

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd your-project-directory
   vercel --prod
   ```

3. **Set Environment Variables**
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ```

### Option 3: Deploy to Railway

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Deploy**
   ```bash
   railway login
   railway init
   railway up
   ```

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
