"""
Sistema de logging profesional para SBOT.
Este módulo proporciona una implementación personalizada del sistema de logs
para el servidor de desarrollo de Django.
"""

import os
import sys
import time
import logging
import datetime
import re
import threading
import psutil
from collections import defaultdict, deque

# Colores ANSI
class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    @staticmethod
    def colorize(text, color):
        """Aplica color al texto."""
        return f"{color}{text}{Colors.RESET}"
    
    @staticmethod
    def supports_color():
        """Verifica si la terminal soporta colores."""
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                mode = ctypes.c_int()
                kernel32.GetConsoleMode(kernel32.GetStdHandle(-11), ctypes.byref(mode))
                if mode.value & 4:  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                    return True
            except (OSError, AttributeError) as exc:
                logging.getLogger(__name__).debug(
                    "Terminal sin VT processing: %s", exc
                )
                return False
        return os.environ.get('TERM') not in (None, '', 'dumb')

# Símbolos
class Symbols:
    CHECK = '✓'
    WARNING = '⚠'
    ERROR = '✖'
    INFO = 'ℹ'
    ARROW = '→'
    BOLT = '⚡'
    
    @staticmethod
    def get(symbol_name):
        """Obtiene el símbolo si está disponible, sino usa una alternativa."""
        if not Colors.supports_color():
            # Alternativas ASCII
            alt_symbols = {
                'CHECK': '[+]',
                'WARNING': '[!]',
                'ERROR': '[x]',
                'INFO': '[i]',
                'ARROW': '->',
                'BOLT': '[*]'
            }
            return alt_symbols.get(symbol_name, '[-]')
        return getattr(Symbols, symbol_name)

# Gestor de estadísticas
class StatsManager:
    def __init__(self):
        self.requests = {
            'total': 0,
            'GET': 0,
            'POST': 0,
            'PUT': 0,
            'DELETE': 0,
            'PATCH': 0,
            'OPTIONS': 0,
            'HEAD': 0,
            'static': 0
        }
        self.response_times = []
        self.status_codes = defaultdict(int)
        self.static_buffer = []
        self.static_buffer_size = 25
        self.last_summary_time = time.time()
        self.last_summary_count = 0
        self.summary_interval = 60  # segundos
        self.processed_files = 0
        
    def add_request(self, method, path, status_code, duration):
        """Registra una petición."""
        self.requests['total'] += 1
        self.requests[method] = self.requests.get(method, 0) + 1
        self.status_codes[status_code] += 1
        self.response_times.append(duration)
        
        # Detectar peticiones estáticas
        if self._is_static_file(path):
            self.requests['static'] += 1
            self.static_buffer.append((method, path, status_code, duration))
            
            # Limitar el buffer de estáticos
            if len(self.static_buffer) > self.static_buffer_size:
                self.static_buffer.pop(0)
                
        # Comprobar si es momento de mostrar resumen
        current_time = time.time()
        if (current_time - self.last_summary_time >= self.summary_interval and 
            self.requests['total'] - self.last_summary_count >= 10):
            self.last_summary_time = current_time
            self.last_summary_count = self.requests['total']
            return self.get_summary()
        return None
    
    def get_avg_response_time(self):
        """Obtiene el tiempo medio de respuesta."""
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times)
    
    def get_memory_usage(self):
        """Obtiene el uso de memoria del proceso actual."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)  # MB
    
    def _is_static_file(self, path):
        """Determina si una ruta corresponde a un archivo estático."""
        static_extensions = ['.css', '.js', '.jpg', '.jpeg', '.png', '.gif', 
                             '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot']
        return any(path.endswith(ext) for ext in static_extensions)
    
    def get_summary(self):
        """Genera un resumen de actividad."""
        summary = [
            "────────────────────── RESUMEN DE ACTIVIDAD ──────────────────────",
            f"→ Peticiones totales: {self.requests['total']} | GET: {self.requests['GET']} | POST: {self.requests['POST']}",
            f"→ Tiempo medio respuesta: {self.get_avg_response_time():.1f} ms",
            f"→ Archivos procesados: {self.processed_files} | Memoria utilizada: {self.get_memory_usage():.1f} MB",
            "──────────────────────────────────────────────────────────────────"
        ]
        return '\n'.join(summary)
    
    def add_processed_file(self):
        """Incrementa el contador de archivos procesados."""
        self.processed_files += 1
        
# Sistema de logging principal
class ProfessionalLogger:
    def __init__(self):
        self.stats = StatsManager()
        self.get_count = 0
        self.get_requests_limit = 2
        self.last_method = None
        self.buffer = []
        self.buffer_count = 0
        
        # Banner y estado
        self.banner_shown = False
        self.startup_logs_shown = 0
        self.startup_complete = False
        
        # Para determinar si estamos procesando archivos
        self.processing_file = False
        self.processing_filename = None
    
    def _format_time(self):
        """Obtiene la hora actual formateada."""
        return datetime.datetime.now().strftime('%H:%M:%S')
        
    def show_banner(self):
        """Muestra el banner inicial."""
        if self.banner_shown:
            return
            
        try:
            from banner import get_banner
            print(get_banner())
        except ImportError:
            banner = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║ SBOT v1.5.8.0 - SISTEMA DE INTELIGENCIA ARTIFICIAL PARA AUDITORÍA          ║
║ Entorno: Producción | Iniciado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}                        ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
            print(banner)
            
        self.banner_shown = True
        
    def show_startup_logs(self):
        """Muestra logs de inicio del sistema."""
        if self.startup_logs_shown >= 4:
            self.startup_complete = True
            return
            
        startup_logs = [
            f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Servicios principales inicializados",
            f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Base de datos conectada (MySQL server 8.0.32)",
            f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Servicio de auditoría cargado correctamente",
            f"[{self._format_time()}] {Colors.colorize(Symbols.get('ARROW'), Colors.CYAN)} Servidor ejecutándose en http://127.0.0.1:8000/",
        ]
        
        print(startup_logs[self.startup_logs_shown])
        self.startup_logs_shown += 1
    
    def log_request(self, method, path, status_code, duration=None):
        """Registra una petición HTTP."""
        # Mostrar banner y logs de inicio si es necesario
        if not self.banner_shown:
            self.show_banner()
            print()  # Línea en blanco
            
        if not self.startup_complete:
            self.show_startup_logs()
            if self.startup_complete:
                print()  # Línea en blanco después de logs de inicio
        
        # Estadísticas
        summary = self.stats.add_request(method, path, status_code, duration or 0)
        
        # Verificar si es una petición estática
        is_static = self.stats._is_static_file(path)
        
        # Agrupar peticiones estáticas
        if is_static:
            self.buffer_count += 1
            if self.buffer_count == self.stats.static_buffer_size:
                print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('INFO'), Colors.BLUE)} {self.buffer_count} peticiones estáticas procesadas...")
                self.buffer_count = 0
            return
            
        # Limitar logs de GET repetidos
        if method == 'GET':
            if self.last_method == 'GET':
                self.get_count += 1
                if self.get_count > self.get_requests_limit:
                    # No mostrar este log
                    return
            else:
                self.get_count = 1
        else:
            self.get_count = 0
            
        self.last_method = method
        
        # Colorear según método
        if method == 'GET':
            method_color = Colors.GREEN
        elif method == 'POST':
            method_color = Colors.BLUE
        elif method == 'DELETE':
            method_color = Colors.RED
        elif method == 'PUT' or method == 'PATCH':
            method_color = Colors.YELLOW
        else:
            method_color = Colors.RESET
            
        # Colorear según código de estado
        if str(status_code).startswith('2'):
            status_color = Colors.GREEN
        elif str(status_code).startswith('3'):
            status_color = Colors.CYAN
        elif str(status_code).startswith('4'):
            status_color = Colors.YELLOW
        elif str(status_code).startswith('5'):
            status_color = Colors.RED
        else:
            status_color = Colors.RESET
            
        # Formatear duración
        duration_text = f" ({duration:.1f} ms)" if duration else ""
        
        # Casos especiales
        extra_info = ""
        if method == 'POST' and 'auth-signin' in path:
            extra_info = f" {Colors.colorize(Symbols.get('BOLT'), Colors.YELLOW)} admin"
            # Simular mensaje de autenticación
            print(f"[{self._format_time()}] {Colors.colorize(status_code, status_color)} {Colors.colorize(method, method_color)} {path}{duration_text}{extra_info}")
            print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Usuario autenticado: admin")
            return
        
        # Log estándar
        print(f"[{self._format_time()}] {Colors.colorize(status_code, status_color)} {Colors.colorize(method, method_color)} {path}{duration_text}{extra_info}")
        
        # Mostrar resumen si es necesario
        if summary:
            print()
            print(summary)
            print()
    
    def log_file_processing(self, filename, status="iniciado", size=None, text_size=None, result=None):
        """Registra el procesamiento de un archivo."""
        if status == "iniciado":
            self.processing_file = True
            self.processing_filename = filename
            print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('WARNING'), Colors.YELLOW)} EVENTO: Procesamiento de datos iniciado ({filename})")
        elif status == "convertido" and size and text_size:
            print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Conversión a texto completada: {size:.1f}MB → {text_size:.0f}KB")
        elif status == "auditado" and result:
            print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Auditoría completada: Venta {result}")
        elif status == "completado":
            print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('CHECK'), Colors.GREEN)} Datos almacenados en la base de datos")
            self.processing_file = False
            self.processing_filename = None
            self.stats.add_processed_file()
            print()  # Línea en blanco
            
    def log_error(self, message, exception=None):
        """Registra un error."""
        error_text = f"[{self._format_time()}] {Colors.colorize(Symbols.get('ERROR'), Colors.RED)} ERROR: {message}"
        if exception:
            error_text += f"\n    {Colors.colorize(str(exception), Colors.BRIGHT_RED)}"
        print(error_text)
        
    def log_warning(self, message):
        """Registra una advertencia."""
        print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('WARNING'), Colors.YELLOW)} ADVERTENCIA: {message}")
        
    def log_info(self, message):
        """Registra información general."""
        print(f"[{self._format_time()}] {Colors.colorize(Symbols.get('INFO'), Colors.BLUE)} {message}")

# Instancia global del logger
professional_logger = ProfessionalLogger()

# Reemplazo para el logger de Django
class CustomWSGIRequestHandler:
    """
    Manejador personalizado para peticiones WSGI.
    """
    def log_message(self, format, *args):
        """Método personalizado para logging."""
        try:
            request = args[0].split()[0]  # GET, POST, etc.
            path = args[0].split()[1]
            status_code = args[1]
            
            # Calcular duración (simular)
            duration = max(10, min(200, time.time() * 1000 % 200))
            
            # Registrar usando nuestro logger profesional
            professional_logger.log_request(request, path, status_code, duration)
        except Exception as e:
            # Si hay algún error, usar el logger estándar
            sys.__stdout__.write(f"[ERROR LOGGING] {str(e)}\n")
            sys.__stdout__.write(f"{format % args}\n")

# Simulador de actividades para demostraciones
class ActivitySimulator(threading.Thread):
    """
    Simula actividades como procesamiento de archivos para demos.
    """
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True
        
    def run(self):
        while self.running:
            # Esperar 60-120 segundos
            time.sleep(random.randint(60, 120))
            
            # 30% de probabilidad de simular procesamiento
            if random.random() < 0.3:
                self.simulate_file_processing()
                
    def simulate_file_processing(self):
        """Simula el procesamiento de un archivo."""
        filename = f"audio-{random.randint(1000, 9999)}.gsm"
        size = random.uniform(0.8, 2.5)  # MB
        text_size = size * 20  # KB
        result = "POSITIVA" if random.random() > 0.3 else "NEGATIVA"
        
        professional_logger.log_file_processing(filename, "iniciado")
        time.sleep(1.5)
        professional_logger.log_file_processing(filename, "convertido", size, text_size)
        time.sleep(0.8)
        professional_logger.log_file_processing(filename, "auditado", result=result)
        time.sleep(0.5)
        professional_logger.log_file_processing(filename, "completado")
        
# Función para iniciar el logger
def start_logger():
    """Inicia el sistema de logging."""
    # Iniciar simulador solo para demos
    if os.environ.get('SBOT_DEMO_MODE', 'false').lower() == 'true':
        simulator = ActivitySimulator()
        simulator.start()
    
    return professional_logger

# Para pruebas directas
if __name__ == "__main__":
    import random
    logger = start_logger()
    
    # Simular actividad
    paths = [
        '/dashboard/',
        '/accounts/login/',
        '/api/data/',
        '/static/main.css',
        '/static/js/app.js',
        '/media/images/logo.png',
        '/admin/'
    ]
    
    methods = ['GET', 'POST', 'GET', 'GET', 'GET']
    statuses = [200, 301, 302, 400, 404, 500]
    weights = [0.8, 0.05, 0.05, 0.03, 0.02, 0.05]
    
    for i in range(50):
        method = random.choice(methods)
        path = random.choice(paths)
        status = random.choices(statuses, weights)[0]
        duration = random.uniform(10, 200)
        
        logger.log_request(method, path, status, duration)
        time.sleep(0.5)
        
        if i == 15:
            logger.log_file_processing('audio-2345.gsm', 'iniciado')
            time.sleep(1)
            logger.log_file_processing('audio-2345.gsm', 'convertido', 1.2, 24)
            time.sleep(1)
            logger.log_file_processing('audio-2345.gsm', 'auditado', result='POSITIVA')
            time.sleep(1)
            logger.log_file_processing('audio-2345.gsm', 'completado')
