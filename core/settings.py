"""
Django settings for core project.

---
SindyBot v1.5 — configuración vía entorno (SCRUM-5/6)
Harold Castro (hcastro)
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
from str2bool import str2bool

load_dotenv()  # take environment variables from .env.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY no definida. Copia .env.example a .env y asigna un valor único."
    )

ALLOW_PUBLIC_REGISTRATION = str2bool(
    os.environ.get("ALLOW_PUBLIC_REGISTRATION", "False")
)
USE_SQLITE_DEMO = str2bool(os.environ.get("USE_SQLITE_DEMO", "False"))

# Enable/Disable DEBUG Mode
DEBUG = str2bool(os.environ.get('DEBUG', 'True'))

# Hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.30.241']
host_setting = os.environ.get('ALLOWED_HOSTS', '')
if host_setting:
    ALLOWED_HOSTS.extend(host_setting.split(','))

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000', 'http://0.0.0.0:8000', 'http://192.168.30.241:8000']
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
    "core.apps.CoreConfig",  # Añadir la aplicación core
    "home",
    "authentication",  
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",    
    "django.contrib.sessions.middleware.SessionMiddleware",  # PRIMERO debe estar el middleware de sesiones de Django
    # Middleware personalizado para depurar problemas con sesiones (DESPUÉS del SessionMiddleware)    
    "home.session_debug_middleware.SessionDebugMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "home.middleware.AdminRedirectMiddleware",  # Middleware actualizado
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
if USE_SQLITE_DEMO:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_demo.sqlite3",
        }
    }
else:
    db_password = os.environ.get("DB_PASSWORD")
    if not db_password:
        raise ImproperlyConfigured(
            "DB_PASSWORD no definida. Usa .env o USE_SQLITE_DEMO=True para demo local."
        )
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "auto_sbot"),
            "USER": os.environ.get("DB_USER", "adminsbot"),
            "PASSWORD": db_password,
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "charset": "utf8mb4",
            },
            "CONN_MAX_AGE": 60,
        }
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
LANGUAGE_CODE = "es-mx"
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

# Configuración de sesiones - usando almacenamiento en archivos por si hay problemas con la BD
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = os.path.join(BASE_DIR, 'temp', 'sessions')
if not os.path.exists(SESSION_FILE_PATH):
    os.makedirs(SESSION_FILE_PATH, exist_ok=True)
SESSION_COOKIE_AGE = 86400  # 24 horas en segundos
SESSION_COOKIE_SECURE = False  # No requerir HTTPS en desarrollo
SESSION_COOKIE_HTTPONLY = True  # Prevenir acceso JavaScript a la cookie
SESSION_SAVE_EVERY_REQUEST = False  # No guardar en cada petición para mejor rendimiento

# Configuración de logging mejorada para diagnosticar problemas de sesión
import logging.config

# Asegurarnos de que el directorio de logs existe
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Configuración de logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'WARNING',  # Cambio de INFO a WARNING para reducir mensajes
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'session_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'session_debug.log'),
            'formatter': 'verbose',
            'delay': False,  # No retrasar la creación del archivo
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'formatter': 'verbose',
            'delay': False,  # No retrasar la creación del archivo
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'error_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.contrib.sessions': {
            'handlers': ['console', 'session_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'home.session_debug_middleware': {
            'handlers': ['console', 'session_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Inicialización inmediata del logger para sesión
session_logger = logging.getLogger('home.session_debug_middleware')
session_logger.info('Configuración de logging inicializada')
