"""
Middleware para depurar problemas con las sesiones.
"""
import logging
import traceback
import sys
import os
import json
from datetime import datetime
from django.contrib.sessions.exceptions import SuspiciousSession

logger = logging.getLogger('home.session_debug_middleware')

class SessionDebugMiddleware:
    """
    Middleware que intercepta errores de sesión y proporciona más información de depuración.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self._logged_init = False  # Para controlar mensajes repetitivos
        
        logger.info(f"SessionDebugMiddleware inicializado. PID: {os.getpid()}")
        
        # Registrar información básica de Python
        python_info = {
            'version': sys.version,
            'platform': sys.platform,
            'executable': sys.executable,
            'path': sys.path
        }
        logger.info(f"Información de Python: {python_info}")

    def __call__(self, request):
        # Extraer información de cookies - solo en nivel DEBUG para evitar spam de logs
        cookies_info = {}
        for key, value in request.COOKIES.items():
            if key == 'sessionid':
                cookies_info[key] = value
                # Cambio de INFO a DEBUG para reducir mensajes en la consola
                logger.debug(f"Session ID: {value}")
        
        # Verificar que la sesión ya esté inicializada (debe estarlo porque SessionMiddleware se ejecuta antes)
        if not hasattr(request, 'session'):
            logger.warning("La sesión no está inicializada en la solicitud. Posible problema de configuración de middleware.")
            return self.get_response(request)
            
        # Antes de procesar la vista, intentar acceder a la sesión
        try:
            # Registrar cabeceras importantes
            logger.debug(f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'No disponible')}")
            logger.debug(f"Cookies: {cookies_info}")
            
            # Forzar la carga de la sesión
            session_key = request.COOKIES.get('sessionid')
            if session_key:
                logger.debug(f"Intentando cargar sesión con clave: {session_key}")
            else:
                logger.debug("No hay cookie de sesión presente")
                
            request.session.load()
            
            # Si llegamos aquí, la sesión se cargó correctamente
            if not self._logged_init and request.session.session_key:
                logger.info(f"Sesión inicializada y funcionando correctamente.")
                self._logged_init = True
            
            logger.debug(f"Sesión cargada correctamente. Clave: {request.session.session_key}")
            
        except SuspiciousSession as e:
            # Registrar el error en detalle
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.error(f"SESIÓN CORRUPTA DETECTADA: {str(e)}")
            logger.error(f"Hora: {error_time}")
            logger.error(f"Session key: {request.COOKIES.get('sessionid', 'No session ID')}")
            logger.error(f"URL: {request.path}")
            logger.error(f"Método: {request.method}")
            logger.error(f"User Agent: {request.META.get('HTTP_USER_AGENT', 'No disponible')}")
            logger.error(f"Traza:\n{traceback.format_exc()}")
            
            # Intentar recolectar más información sobre la sesión
            try:
                from django.contrib.sessions.models import Session
                from django.contrib.sessions.backends.db import SessionStore
                
                session_key = request.COOKIES.get('sessionid')
                if session_key:
                    try:
                        # Intentar recuperar datos de la base de datos
                        db_session = Session.objects.filter(session_key=session_key).first()
                        if db_session:
                            logger.error(f"Datos de sesión en BD: {db_session.session_data[:100]}...")
                            logger.error(f"Expira: {db_session.expire_date}")
                    except Exception as db_error:
                        logger.error(f"Error al consultar sesión en BD: {str(db_error)}")
                        
                    try:
                        # Intentar decodificar manualmente
                        session_store = SessionStore(session_key=session_key)
                        raw_data = session_store.load()
                        logger.error(f"Datos crudos de sesión: {raw_data}")
                    except Exception as decode_error:
                        logger.error(f"Error al decodificar sesión: {str(decode_error)}")
            except Exception as session_debug_error:
                logger.error(f"Error al diagnosticar sesión: {str(session_debug_error)}")
            
            # Eliminar la cookie de sesión corrupta
            response = self.get_response(request)
            logger.info("Eliminando cookie de sesión corrupta")
            response.delete_cookie('sessionid')
            return response
            
        except Exception as e:
            # Capturar cualquier otro error relacionado con las sesiones
            logger.error(f"Error de sesión no esperado: {str(e)}")
            logger.error(f"Session key: {request.COOKIES.get('sessionid', 'No session ID')}")
            logger.error(f"URL: {request.path}")
            logger.error(f"Método: {request.method}")
            logger.error(f"Detalles:\n{traceback.format_exc()}")
        
        # Continuar con el flujo normal
        response = self.get_response(request)
        
        # Verificar si la respuesta incluye una redirección de sesión
        if response.status_code in (302, 301) and 'Location' in response:
            logger.debug(f"Redirección a: {response['Location']}")
        
        return response
