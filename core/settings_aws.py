# Configuración Django para base AWS/RDS opcional.
# Uso: DJANGO_SETTINGS_MODULE=core.settings_aws (solo con AWS_DB_* en .env)

import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403

_required = ("AWS_DB_HOST", "AWS_DB_USER", "AWS_DB_PASSWORD", "AWS_DB_NAME")
missing = [k for k in _required if not os.environ.get(k)]
if missing:
    raise ImproperlyConfigured(
        f"settings_aws requiere en .env: {', '.join(missing)}"
    )

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["AWS_DB_NAME"],
        "USER": os.environ["AWS_DB_USER"],
        "PASSWORD": os.environ["AWS_DB_PASSWORD"],
        "HOST": os.environ["AWS_DB_HOST"],
        "PORT": os.environ.get("AWS_DB_PORT", "3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
        "CONN_MAX_AGE": 60,
    }
}

# Desarrollado por: hcastro
