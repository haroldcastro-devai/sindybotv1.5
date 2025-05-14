"""
Comando 'runserver' personalizado que reemplaza al comando estándar de Django.
"""

from core.custom_runserver import Command

# No es necesario hacer nada más. Django automáticamente usará esta
# implementación en lugar de la original cuando se ejecute:
# python manage.py runserver
