from django.apps import AppConfig
import logging

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Configuración adicional que se ejecuta cuando la aplicación está lista.
        """
        # Inicializar cualquier cosa que sea necesaria al iniciar la aplicación
        pass
