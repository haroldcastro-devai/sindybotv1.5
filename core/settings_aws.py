"""
Compatibilidad: DJANGO_SETTINGS_MODULE=core.settings_aws (SCRUM-30).

Preferir core.settings con USE_AWS_DATABASE=True y variables AWS_DB_* en .env.
"""

import os

os.environ.setdefault("USE_AWS_DATABASE", "True")

from .settings import *  # noqa: F403

# Desarrollado por: hcastro
