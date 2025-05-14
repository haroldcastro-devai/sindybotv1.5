#!/usr/bin/env python
"""
Script para depurar problemas con las sesiones de Django.
"""

import os
import sys
import django
import logging
import traceback
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('session_direct_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('session_debug')

def main():
    """Función principal."""
    logger.info("Iniciando diagnóstico de sesiones")
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    # Importar después de configurar Django
    from django.conf import settings
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore
    from django.contrib.sessions.backends.file import SessionStore as FileSessionStore
    
    # Registrar información de configuración
    logger.info(f"SECRET_KEY (primeros 5 caracteres): {settings.SECRET_KEY[:5]}...")
    logger.info(f"SESSION_ENGINE: {settings.SESSION_ENGINE}")
    logger.info(f"SESSION_COOKIE_NAME: {getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')}")
    
    # Verificar el motor de sesiones
    if settings.SESSION_ENGINE == 'django.contrib.sessions.backends.db':
        logger.info("Usando almacenamiento de sesiones en base de datos")
        
        try:
            # Contar sesiones activas
            sessions_count = Session.objects.count()
            logger.info(f"Sesiones activas en la base de datos: {sessions_count}")
            
            # Analizar algunas sesiones recientes
            recent_sessions = Session.objects.all().order_by('-expire_date')[:5]
            logger.info(f"Sesiones recientes encontradas: {recent_sessions.count()}")
            
            for session in recent_sessions:
                try:
                    logger.info(f"Session key: {session.session_key}")
                    logger.info(f"Expira: {session.expire_date}")
                    
                    # Intentar decodificar
                    try:
                        session_store = SessionStore(session_key=session.session_key)
                        session_data = session_store.load()
                        logger.info(f"Datos de sesión: {session_data}")
                    except Exception as e:
                        logger.error(f"Error decodificando sesión {session.session_key}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error analizando sesión: {str(e)}")
        except Exception as e:
            logger.error(f"Error accediendo a sesiones en la base de datos: {str(e)}")
            logger.error(traceback.format_exc())
    
    elif settings.SESSION_ENGINE == 'django.contrib.sessions.backends.file':
        logger.info("Usando almacenamiento de sesiones en archivos")
        
        try:
            # Verificar directorio de sesiones
            session_dir = getattr(settings, 'SESSION_FILE_PATH', None)
            if session_dir:
                logger.info(f"Directorio de sesiones: {session_dir}")
                
                # Verificar que el directorio existe
                if os.path.exists(session_dir):
                    logger.info(f"El directorio de sesiones existe")
                    
                    # Contar archivos de sesión
                    session_files = [f for f in os.listdir(session_dir) if os.path.isfile(os.path.join(session_dir, f))]
                    logger.info(f"Archivos de sesión encontrados: {len(session_files)}")
                    
                    # Analizar algunos archivos de sesión
                    for session_file in session_files[:5]:
                        try:
                            session_key = session_file
                            logger.info(f"Analizando archivo de sesión: {session_key}")
                            
                            # Verificar ruta completa
                            full_path = os.path.join(session_dir, session_file)
                            file_size = os.path.getsize(full_path)
                            modified_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                            
                            logger.info(f"Tamaño: {file_size} bytes")
                            logger.info(f"Modificado: {modified_time}")
                            
                            # Intentar cargar la sesión
                            try:
                                session_store = FileSessionStore(session_key=session_key)
                                session_data = session_store.load()
                                logger.info(f"Datos de sesión: {session_data}")
                            except Exception as e:
                                logger.error(f"Error cargando sesión {session_key}: {str(e)}")
                        except Exception as e:
                            logger.error(f"Error analizando archivo de sesión {session_file}: {str(e)}")
                else:
                    logger.error(f"El directorio de sesiones no existe: {session_dir}")
            else:
                logger.error("SESSION_FILE_PATH no está configurado")
        except Exception as e:
            logger.error(f"Error accediendo a sesiones en archivos: {str(e)}")
            logger.error(traceback.format_exc())
    
    else:
        logger.info(f"Usando motor de sesiones: {settings.SESSION_ENGINE}")
        logger.warning("Diagnóstico no implementado para este motor de sesiones")
    
    # Intentar crear una sesión de prueba
    logger.info("Intentando crear una sesión de prueba")
    try:
        if settings.SESSION_ENGINE == 'django.contrib.sessions.backends.db':
            session = SessionStore()
            session['test_key'] = 'test_value'
            session.create()
            logger.info(f"Sesión de prueba creada con clave: {session.session_key}")
            
            # Verificar que se puede recuperar
            loaded_session = SessionStore(session_key=session.session_key)
            loaded_data = loaded_session.load()
            logger.info(f"Datos de sesión cargados: {loaded_data}")
            
            # Limpiar
            loaded_session.delete()
            logger.info("Sesión de prueba eliminada correctamente")
        
        elif settings.SESSION_ENGINE == 'django.contrib.sessions.backends.file':
            session = FileSessionStore()
            session['test_key'] = 'test_value'
            session.create()
            logger.info(f"Sesión de prueba creada con clave: {session.session_key}")
            
            # Verificar que se puede recuperar
            loaded_session = FileSessionStore(session_key=session.session_key)
            loaded_data = loaded_session.load()
            logger.info(f"Datos de sesión cargados: {loaded_data}")
            
            # Limpiar
            loaded_session.delete()
            logger.info("Sesión de prueba eliminada correctamente")
    
    except Exception as e:
        logger.error(f"Error creando sesión de prueba: {str(e)}")
        logger.error(traceback.format_exc())
    
    logger.info("Diagnóstico de sesiones completado")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
        logger.error(traceback.format_exc())
