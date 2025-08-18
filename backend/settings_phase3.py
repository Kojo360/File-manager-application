"""
Phase 3 Advanced Settings
Enterprise features and configurations
"""
import os
from .settings import *
from decouple import config

# ===================================
# PHASE 3: ADVANCED CONFIGURATIONS
# ===================================

# Installed Apps - Phase 3 Extensions
INSTALLED_APPS += [
    # Real-time & WebSockets
    'channels',
    
    # Background Tasks
    'django_celery_beat',
    'django_celery_results',
    
    # Advanced Authentication
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.microsoft',
    
    # Analytics & Monitoring
    'django_extensions',
    'silk',
    
    # Security & Permissions
    'guardian',
    
    # File Processing
    'storages',
    
    # Phase 3 Apps (cleaned up)
    # Removed: analytics, workflows, ai_features (unused)
]

# ===================================
# CELERY CONFIGURATION
# ===================================
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ===================================
# CHANNELS CONFIGURATION (WebSockets)
# ===================================
ASGI_APPLICATION = 'backend.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [config('REDIS_URL', default='redis://localhost:6379/0')],
        },
    },
}

# ===================================
# CACHING CONFIGURATION
# ===================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ===================================
# ELASTICSEARCH CONFIGURATION
# ===================================
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': config('ELASTICSEARCH_URL', default='localhost:9200')
    },
}

# ===================================
# AI & ML CONFIGURATION
# ===================================
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
TENSORFLOW_MODEL_PATH = BASE_DIR / 'ai_models'

# OCR Enhancement Settings
OCR_LANGUAGES = ['eng', 'fra', 'deu', 'spa', 'ita', 'por', 'rus', 'chi_sim', 'chi_tra', 'jpn', 'kor']
OCR_CONFIDENCE_THRESHOLD = 0.7
HANDWRITING_RECOGNITION_ENABLED = True

# ===================================
# FILE STORAGE & PROCESSING
# ===================================
# AWS S3 Configuration (Optional)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')

# File Processing Limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_BULK_OPERATIONS = 1000
BATCH_PROCESSING_SIZE = 50

# ===================================
# SECURITY ENHANCEMENTS
# ===================================
# Multi-Factor Authentication
OTP_TOTP_ISSUER = 'File Manager Enterprise'
OTP_LOGIN_URL = '/auth/login/'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
]

# OAuth Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'github': {
        'SCOPE': ['user:email'],
    },
    'microsoft': {
        'SCOPE': ['User.Read'],
    }
}

# ===================================
# ANALYTICS & MONITORING
# ===================================
# Django Silk (Performance Monitoring)
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True

# Custom Analytics Settings
ANALYTICS_RETENTION_DAYS = 365
REAL_TIME_ANALYTICS = True
PERFORMANCE_MONITORING = True

# ===================================
# WORKFLOW CONFIGURATION
# ===================================
WORKFLOW_EMAIL_NOTIFICATIONS = True
WORKFLOW_APPROVAL_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds

# ===================================
# API RATE LIMITING
# ===================================
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle'
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour'
}

# ===================================
# LOGGING CONFIGURATION
# ===================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'ocr': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'analytics': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'workflows': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ===================================
# EMAIL CONFIGURATION
# ===================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@filemanager.com')

# ===================================
# INTERNATIONALIZATION
# ===================================
LANGUAGE_CODE = 'en-us'
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
    ('ru', 'Russian'),
    ('zh', 'Chinese'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
]

USE_I18N = True
USE_L10N = True

# ===================================
# CUSTOM SETTINGS
# ===================================
# Feature Flags
ENABLE_AI_CLASSIFICATION = config('ENABLE_AI_CLASSIFICATION', default=True, cast=bool)
ENABLE_REAL_TIME_COLLABORATION = config('ENABLE_REAL_TIME_COLLABORATION', default=True, cast=bool)
ENABLE_ADVANCED_ANALYTICS = config('ENABLE_ADVANCED_ANALYTICS', default=True, cast=bool)
ENABLE_WORKFLOW_ENGINE = config('ENABLE_WORKFLOW_ENGINE', default=True, cast=bool)

# Performance Settings
DATABASE_CONNECTION_POOLING = True
ASYNC_PROCESSING_ENABLED = True
REAL_TIME_UPDATES_ENABLED = True

print("Phase 3 Advanced Settings Loaded Successfully! 🚀")
