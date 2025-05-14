"""
WSGI config for core project.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
from django.core.handlers.wsgi import WSGIHandler

# Verificar si estamos en un entorno donde se puede mostrar la salida
if os.environ.get('WSGI_SHOW_BANNER', 'false').lower() == 'true':
    # Añadir el directorio raíz al path para importar el banner
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Intentar importar el banner
    try:
        from banner import get_banner, get_colored_text
        print(get_banner())
        print(get_colored_text("SBOT iniciado en modo producción\n"))
    except ImportError:
        pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

class BrokenPipeErrorWSGIHandler(WSGIHandler):
    def handle_uncaught_exception(self, request, resolver, exc_info):
        import socket
        if isinstance(exc_info[1], socket.error) and '[Errno 32]' in str(exc_info[1]):
            return None  # Maneja silenciosamente el error de Broken Pipe
        return super().handle_uncaught_exception(request, resolver, exc_info)

application = BrokenPipeErrorWSGIHandler()