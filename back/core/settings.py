"""
Django settings for core project.
"""

import os, random, string
from pathlib import Path
from dotenv import load_dotenv
from str2bool import str2bool
from datetime import timedelta

load_dotenv()  # take environment variables from .env.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = ''.join(random.choice( string.ascii_lowercase  ) for i in range( 32 ))

# Enable/Disable DEBUG Mode
DEBUG = str2bool(os.environ.get('DEBUG', 'True'))

# Hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
host_setting = os.environ.get('ALLOWED_HOSTS', '')
if host_setting:
    ALLOWED_HOSTS.extend(host_setting.split(','))

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000', 'http://0.0.0.0:8000']
csrf_setting = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if csrf_setting:
    CSRF_TRUSTED_ORIGINS.extend(csrf_setting.split(','))

X_FRAME_OPTIONS = "SAMEORIGIN"

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition
INSTALLED_APPS = [
    'admin_gradient.apps.AdminGradientConfig',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "home",
    "authentication",  
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",    
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "home.middleware.AdminRedirectMiddleware",  # Middleware actualizado
    # El middleware de banner ha sido eliminado para evitar duplicaciones
]

ROOT_URLCONF = "core.urls"


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

HOME_TEMPLATES = os.path.join(BASE_DIR, 'templates')
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HOME_TEMPLATES],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'auto_sbot'),
        'USER': os.environ.get('DB_USER', 'adminsbot'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '&-4GWwgiw9UfFfOp'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 60,
    },
    # AWS Database comentada
    # 'aws': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': os.environ.get('AWS_DB_NAME', 'sindybot_dev'),
    #     'USER': os.environ.get('AWS_DB_USER', 'dev_user'),
    #     'PASSWORD': os.environ.get('AWS_DB_PASSWORD', 'DevPassword123!'),
    #     'HOST': os.environ.get('AWS_DB_HOST', '34.229.113.3'),
    #     'PORT': os.environ.get('AWS_DB_PORT', '3306'),
    #     'OPTIONS': {
    #         'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    #         'charset': 'utf8mb4',
    #     },
    #     'CONN_MAX_AGE': 60,
    # }
}

# Configuración de router
DATABASE_ROUTERS = ['home.routers.DatabaseRouter']

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = '/accounts/auth-signin/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/auth-signin/'
LOGOUT_URL = '/logout/'  # Configurar la URL de logout para todo el sistema
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración para archivos temporales
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)