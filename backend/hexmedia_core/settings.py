import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-hexmedia-super-secret-key-audio-drama'

DEBUG = True

ALLOWED_HOSTS = [
    '*',
    'hexmedia.169.58.32.179.nip.io',
    'hexmedia-assets.169.58.32.179.nip.io',
    '169.58.32.179',
    'localhost',
    '127.0.0.1',
]

# Reverse Proxy & SSL Configuration
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'core',
    'book_drama',
    'story_writer',
    'image_video',
    'tts',
    'stt',
    'ai_studio',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hexmedia_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hexmedia_core.wsgi.application'
ASGI_APPLICATION = 'hexmedia_core.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'hexmedia'),
        'USER': os.getenv('POSTGRES_USER', 'hexmedia_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'hexmedia_secret_password'),
        'HOST': os.getenv('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.getenv('POSTGRES_PORT', '5439'),
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'ar-eg'
TIME_ZONE = 'Africa/Cairo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://hexmedia.169.58.32.179.nip.io',
    'http://hexmedia.169.58.32.179.nip.io',
    'https://hexmedia-assets.169.58.32.179.nip.io',
    'http://hexmedia-assets.169.58.32.179.nip.io',
    'http://localhost:8100',
    'http://127.0.0.1:8100',
    'http://169.58.32.179:8100',
]

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    'https://hexmedia.169.58.32.179.nip.io',
    'http://hexmedia.169.58.32.179.nip.io',
    'https://hexmedia-assets.169.58.32.179.nip.io',
    'http://hexmedia-assets.169.58.32.179.nip.io',
    'https://*.169.58.32.179.nip.io',
    'http://*.169.58.32.179.nip.io',
    'http://localhost:8100',
    'http://127.0.0.1:8100',
    'http://169.58.32.179:8100',
    'http://169.58.32.179:9101',
    'http://169.58.32.179:8388',
]

# MinIO / S3 Storage Settings
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'http://127.0.0.1:9100')
MINIO_PUBLIC_ENDPOINT = os.getenv('MINIO_PUBLIC_ENDPOINT', 'https://hexmedia-assets.169.58.32.179.nip.io')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadminpassword')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'hexmedia-assets')

# Inngest Settings
INNGEST_DEV_SERVER = os.getenv('INNGEST_DEV_SERVER', 'http://127.0.0.1:8388')
