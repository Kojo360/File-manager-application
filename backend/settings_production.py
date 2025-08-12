"""
Production settings for deployment
"""
import os
from .settings import *
import dj_database_url

# Override settings for production
DEBUG = False

# Allow all hosts for now (you can restrict this later)
ALLOWED_HOSTS = [
    '.render.com',
    '.vercel.app',
    'localhost',
    '127.0.0.1',
    '*'  # Remove this in production and add your specific domains
]

# SECURITY WARNING: Change this secret key in production
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-^yin+e7k-*5^$5=%s#91_yw0^it21)zp@)a93ss_!7!=kv(#et')

# Database configuration for production
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    # Fallback to SQLite for local testing
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional static files directories
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_SSL_REDIRECT = False  # Set to True if using HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CORS settings (if needed)
CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Disable browsable API in production
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
}
