from django.apps import AppConfig

class AdminGradientConfig(AppConfig):
    name = 'admin_gradient'
    verbose_name = 'Admin Personalizado SBOT'

    def ready(self):
        # Código a ejecutar cuando la aplicación está lista
        pass
