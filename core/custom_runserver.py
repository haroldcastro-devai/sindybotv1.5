"""
Servidor de desarrollo personalizado con logging profesional.
"""

import os
import sys
import re
import threading
import time
import random
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.servers.basehttp import WSGIRequestHandler
from core.server_logger import professional_logger

class CustomWSGIRequestHandler(WSGIRequestHandler):
    """
    Manejador personalizado para peticiones WSGI con logs profesionales.
    """
    def log_message(self, format, *args):
        """
        Método personalizado para manejar los mensajes de log.
        """
        try:
            # Extraer información de la solicitud
            request_line = args[0].split()
            
            if len(request_line) >= 2:
                method = request_line[0]  # GET, POST, etc.
                path = request_line[1]
                status_code = args[1]
                
                # Intentar extraer tiempo si está disponible (no siempre está presente)
                duration = None
                if len(args) > 2:
                    # Para Django 3.2+, el tiempo se incluye en un formato específico
                    duration_match = re.search(r'(\d+.\d+)ms', format % args)
                    if duration_match:
                        duration = float(duration_match.group(1))
                
                # Usar el logger profesional
                professional_logger.log_request(method, path, status_code, duration)
            else:
                # Si no podemos extraer la información necesaria, usar el formato estándar
                sys.__stdout__.write(f"{format % args}\n")
        except Exception as e:
            # En caso de error, volver al log estándar
            sys.__stdout__.write(f"Error en log personalizado: {e}\n")
            sys.__stdout__.write(f"{format % args}\n")

class Command(RunserverCommand):
    """
    Versión personalizada del comando runserver con logging profesional.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def get_handler(self, *args, **options):
        """
        Retorna el manejador personalizado para usar con el servidor.
        """
        return CustomWSGIRequestHandler
        
    def inner_run(self, *args, **options):
        """
        Método sobrecargado para configurar el logging antes de iniciar el servidor.
        """
        # Iniciar el logger profesional
        from core.server_logger import start_logger
        start_logger()
        
        # Iniciar simulador de actividad en modo demo si está habilitado
        if os.environ.get('SBOT_DEMO_MODE', 'false').lower() == 'true':
            self._start_demo_activity()
            
        # Llamar al método original
        super().inner_run(*args, **options)
        
    def _start_demo_activity(self):
        """
        Inicia un hilo que simula actividad para demostración.
        """
        class DemoActivityThread(threading.Thread):
            def __init__(self):
                super().__init__(daemon=True)
                self.logger = professional_logger
                
            def run(self):
                # Esperar a que el servidor esté listo
                time.sleep(10)
                
                while True:
                    # Cada 45-90 segundos, simular procesamiento de archivos
                    time.sleep(random.randint(45, 90))
                    self._simulate_file_processing()
                    
            def _simulate_file_processing(self):
                """Simula el procesamiento de un archivo de audio."""
                filename = f"audio-{random.randint(10000, 99999)}.gsm"
                size = random.uniform(0.8, 2.5)  # MB
                text_size = size * 20  # KB
                result = "POSITIVA" if random.random() > 0.3 else "NEGATIVA"
                
                self.logger.log_file_processing(filename, "iniciado")
                time.sleep(2.0)
                self.logger.log_file_processing(filename, "convertido", size, text_size)
                time.sleep(1.2)
                self.logger.log_file_processing(filename, "auditado", result=result)
                time.sleep(0.8)
                self.logger.log_file_processing(filename, "completado")
                
        # Iniciar el hilo
        demo_thread = DemoActivityThread()
        demo_thread.start()
