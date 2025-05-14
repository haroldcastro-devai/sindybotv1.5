"""
Middleware para asegurar que el banner SBOT se muestre durante la ejecución del servidor.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from .banner import display_banner

# Configurar logger
logger = logging.getLogger(__name__)

class BannerMiddleware(MiddlewareMixin):
    """
    Middleware que mostraría el banner SBOT, pero ahora está desactivado 
    para evitar múltiples banners.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def process_request(self, request):
        """
        No hacemos nada aquí para evitar múltiples banners.
        """
        return None
