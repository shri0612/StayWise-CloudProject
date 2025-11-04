"""
Django settings for smarthost project.
"""

from pathlib import Path
import os
from datetime import timedelta

# ====================================
# BASE SETTINGS
# ====================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-&jji!=w9t7#ew82drb@2#r)0z(f(b)w&&j%^1(ir8oh_w5!1l+'
DEBUG = True

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'https://9427716c9da34b16b4494ea76dd318b0.vfs.cloud9.us-east-1.amazonaws.com',
]


# ====================================
# APPLICATIONS
# ====================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accommodation',
    'accounts',
    'widget_tweaks',
    'storages',
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}


# ====================================
# MIDDLEWARE
# ====================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ====================================
# URLS & WSGI
# ====================================
ROOT_URLCONF = 'smarthost.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smarthost.wsgi.application'


# ====================================
# DATABASE
# ====================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ====================================
# PASSWORD VALIDATION
# ====================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ====================================
# INTERNATIONALIZATION
# ====================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ====================================
# STATIC & MEDIA
# ====================================
STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ====================================
# AUTH SETTINGS
# ====================================
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True


# ====================================
# SESSION SETTINGS (Fixed)
# ====================================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Use default DB backend
SESSION_COOKIE_NAME = 'smarthost_session'  # Base session cookie
CSRF_COOKIE_NAME = "smarthost_csrftoken"


# ====================================
# AWS S3 STORAGE CONFIG
# ====================================
AWS_ACCESS_KEY_ID = "ASIA23YMKQV5SCHPM5UE"
AWS_SECRET_ACCESS_KEY = "8j+k0eK83uzvCa2qYuoTvxfEabUI1awDuPsCYi6k"
AWS_STORAGE_BUCKET_NAME = "studentaccommodation-media-shridharan"
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"


# ====================================
# JWT AUTH (for REST APIs)
# ====================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# 📧 Email (Gmail SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "shri2178499@gmail.com"
EMAIL_HOST_PASSWORD = "reynldypshnzrxfr"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
