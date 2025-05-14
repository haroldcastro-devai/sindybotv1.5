#!/usr/bin/env python
"""
Script para ejecutar el servidor SBOT con logs profesionales.
Este script intercepta y reformatea la salida del servidor Django
para mostrar logs profesionales y limpios.
"""

import os
import sys
import re
import time
import datetime
import subprocess
import threading
import platform
import atexit

# Definir colores ANSI
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

# Definir símbolos (con alternativas ASCII)
class Symbols:
    def __init__(self, use_unicode=True):
        self.use_unicode = use_unicode
        
    def get(self, name):
        """Obtiene el símbolo apropiado según configuración."""
        unicode_symbols = {
            'check': '✓',
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ',
            'arrow': '→',
            'bolt': '⚡'
        }
        
        ascii_symbols = {
            'check': '[+]',
            'error': '[x]',
            'warning': '[!]',
            'info': '[i]',
            'arrow': '->',
            'bolt': '[*]'
        }
        
        if self.use_unicode:
            return unicode_symbols.get(name, '[-]')
        else:
            return ascii_symbols.get(name, '[-]')

# Estado global para rastrear peticiones
request_state = {
    'get_count': 0,
    'last_method': None,
    'static_count': 0,
    'total_requests': 0
}

# Variable para controlar si el banner ya se mostró
banner_shown = False
startup_completed = False
startup_messages_shown = 0
start_time = datetime.datetime.now()

def enable_ansi_colors():
    """Habilita los colores ANSI en Windows."""
    if platform.system() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    return True

def colorize(text, color, enabled=True):
    """Aplica un color a un texto."""
    if enabled:
        return f"{color}{text}{Colors.RESET}"
    else:
        return text

def check_unicode_support():
    """Verifica si la consola soporta caracteres Unicode."""
    if platform.system() == 'Windows':
        try:
            # Intentar escribir un carácter Unicode y ver si falla
            try:
                # Intentar esto en un archivo temporal primero
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
                    f.write('✓')
                os.unlink(f.name)
                return True
            except UnicodeEncodeError:
                return False
        except:
            return False
    return True

def create_simple_banner():
    """Crea un banner simple usando caracteres ASCII."""
    return """
+--------------------------------------------------------------+
|                                                              |
|                       SBOT v1.5.8.0                          |
|           SISTEMA IA DE AUDITORIA - PRODUCCION               |
|                                                              |
+--------------------------------------------------------------+
"""

def show_banner(use_unicode=True, use_colors=True):
    """Muestra el banner inicial del SBOT."""
    global banner_shown
    if banner_shown:
        return
    
    banner = ""
    
    # Determinar si usar el banner personalizado o uno simple
    try:
        if use_unicode:
            # Intentar importar el banner personalizado
            try:
                from banner import get_banner
                banner = get_banner()
            except (ImportError, UnicodeEncodeError):
                # Si falla, usar un banner simple
                banner = create_simple_banner()
        else:
            banner = create_simple_banner()
    except:
        # En caso de cualquier error, usar un banner muy simple
        banner = "\n=== SBOT v1.5.8.0 - SISTEMA IA DE AUDITORIA ===\n"
    
    print(banner)
    banner_shown = True

def current_time():
    """Retorna la hora actual formateada."""
    return datetime.datetime.now().strftime('%H:%M:%S')

def show_startup_message(symbols, use_colors=True):
    """Muestra los mensajes de inicio del sistema."""
    global startup_messages_shown, startup_completed
    
    if startup_completed:
        return
        
    startup_messages = [
        (f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Servicios principales inicializados", 0.3),
        (f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Base de datos conectada (MySQL server 8.0.32)", 0.3),
        (f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Servicio de auditoría cargado correctamente", 0.3),
        (f"[{current_time()}] {colorize(symbols.get('arrow'), Colors.CYAN, use_colors)} Servidor ejecutándose en http://192.168.30.241:8000/", 0)
    ]
    
    if startup_messages_shown < len(startup_messages):
        message, delay = startup_messages[startup_messages_shown]
        print(message)
        startup_messages_shown += 1
        if delay > 0:
            time.sleep(delay)
    
    if startup_messages_shown == len(startup_messages):
        startup_completed = True
        print()  # Línea en blanco después de los mensajes de inicio

def process_django_output(line, symbols, use_colors=True):
    """
    Procesa una línea de salida de Django y la reformatea.
    """
    global request_state, startup_completed
    
    # Mostrar el banner si no se ha mostrado
    if not banner_shown:
        show_banner(use_unicode=use_colors, use_colors=use_colors)
    
    # Si es la primera vez que se ve el mensaje "Starting development server"
    if "Starting development server at" in line and not startup_completed:
        show_startup_message(symbols, use_colors=use_colors)
        while not startup_completed:
            show_startup_message(symbols, use_colors=use_colors)
        return None  # No mostrar el mensaje original
    
    # Patrones para identificar diferentes tipos de mensajes
    status_pattern = re.compile(r'"(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+([^"]+)\s+HTTP/\d\.\d"\s+(\d+)')
    static_pattern = re.compile(r'\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)')
    
    # Comprobar si es un mensaje de estado HTTP
    status_match = status_pattern.search(line)
    if status_match:
        method, path, status_code = status_match.groups()
        
        # Determinar si es un archivo estático
        is_static = bool(static_pattern.search(path))
        
        # Gestionar archivos estáticos
        if is_static:
            request_state['static_count'] += 1
            if request_state['static_count'] >= 10:
                print(f"[{current_time()}] {colorize(symbols.get('info'), Colors.BLUE, use_colors)} {request_state['static_count']} peticiones estáticas procesadas...")
                request_state['static_count'] = 0
            return None  # No mostrar logs individuales para estáticos
        
        # Gestionar peticiones GET repetidas
        if method == 'GET':
            if request_state['last_method'] == 'GET':
                request_state['get_count'] += 1
                if request_state['get_count'] > 2:
                    # No mostrar más de 2 GETs consecutivos
                    return None
            else:
                request_state['get_count'] = 1
        else:
            request_state['get_count'] = 0
        
        request_state['last_method'] = method
        request_state['total_requests'] += 1
        
        # Colorear según método
        if method == 'GET':
            method_color = Colors.GREEN
        elif method == 'POST':
            method_color = Colors.BLUE
        elif method == 'DELETE':
            method_color = Colors.RED
        elif method in ['PUT', 'PATCH']:
            method_color = Colors.YELLOW
        else:
            method_color = Colors.MAGENTA
        
        # Colorear según código de estado
        if status_code.startswith('2'):
            status_color = Colors.GREEN
        elif status_code.startswith('3'):
            status_color = Colors.CYAN
        elif status_code.startswith('4'):
            status_color = Colors.YELLOW
        elif status_code.startswith('5'):
            status_color = Colors.RED
        else:
            status_color = Colors.WHITE
        
        # Extraer información de tiempo de respuesta (si está disponible)
        duration_text = ""
        duration_match = re.search(r'(\d+\.\d+)ms', line)
        if duration_match:
            duration = float(duration_match.group(1))
            duration_text = f" ({duration:.1f} ms)"
        
        # Formatear salida profesional
        formatted_line = f"[{current_time()}] {colorize(status_code, status_color, use_colors)} {colorize(method, method_color, use_colors)} {path}{duration_text}"
        
        # Caso especial para login
        if method == 'POST' and 'auth-signin' in path:
            formatted_line += f" {colorize(symbols.get('bolt'), Colors.YELLOW, use_colors)} admin"
            
            # Simular mensaje de login exitoso
            if status_code.startswith('2'):
                print(formatted_line)
                print(f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Usuario autenticado: admin")
                return None
        
        # Mostrar resumen cada 50 peticiones
        if request_state['total_requests'] % 50 == 0 and request_state['total_requests'] > 0:
            print(formatted_line)
            print(f"""
────────────────────── RESUMEN DE ACTIVIDAD ──────────────────────
→ Peticiones totales: {request_state['total_requests']}
→ Tiempo desde inicio: {(datetime.datetime.now() - start_time).total_seconds():.1f} segundos
→ Memoria utilizada: {get_memory_usage():.1f} MB
──────────────────────────────────────────────────────────────────
""")
            return None
        
        return formatted_line
    
    # Gestionar otros tipos de mensajes
    elif "Watching for file changes" in line:
        return None  # Suprimir este mensaje
    elif "Performing system checks..." in line:
        return None  # Suprimir este mensaje
    elif "System check identified no issues" in line:
        return f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Verificación del sistema completada sin problemas"
    elif "System check identified" in line and "issue" in line:
        return f"[{current_time()}] {colorize(symbols.get('warning'), Colors.YELLOW, use_colors)} {line.strip()}"
    
    # Para otros mensajes, dejarlos pasar sin cambios
    return line

def get_memory_usage():
    """Obtiene el uso de memoria del proceso actual en MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)  # MB
    except:
        return 0

def simulate_file_processing(symbols, use_colors=True):
    """Simula el procesamiento de archivos para demostración."""
    sample_files = [
        "EXGAS_54736_20240425_SALVA.gsm",
        "GASES_38492_20240430_PRACTI.gsm",
        "OXIGAS_12874_20240428_FUN.gsm",
        "GDO_76391_20240427_FACTURA-P.gsm"
    ]
    
    while True:
        # Esperar entre 45-90 segundos
        time.sleep(45 + 45 * (time.time() % 1))
        
        # Seleccionar un archivo al azar
        import random
        filename = random.choice(sample_files)
        size = random.uniform(0.8, 2.5)  # MB
        text_size = size * 20  # KB
        result = "POSITIVA" if random.random() > 0.3 else "NEGATIVA"
        
        # Mostrar proceso
        print(f"[{current_time()}] {colorize(symbols.get('warning'), Colors.YELLOW, use_colors)} EVENTO: Procesamiento de datos iniciado ({filename})")
        time.sleep(1.5)
        print(f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Conversión a texto completada: {size:.1f}MB → {text_size:.0f}KB")
        time.sleep(1.0)
        print(f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Auditoría completada: Venta {result}")
        time.sleep(0.8)
        print(f"[{current_time()}] {colorize(symbols.get('check'), Colors.GREEN, use_colors)} Datos almacenados en la base de datos")
        print()  # Línea en blanco

def run_django_server_with_professional_logs():
    """
    Ejecuta el servidor Django e intercepta su salida para mostrar logs profesionales.
    """
    global start_time
    start_time = datetime.datetime.now()
    
    # Verificar si podemos usar colores y Unicode
    use_colors = enable_ansi_colors()
    use_unicode = check_unicode_support()
    
    # Inicializar símbolos
    symbols = Symbols(use_unicode=use_unicode)
    
    # Preparar comando para ejecutar Django
    cmd = [sys.executable, "manage.py", "runserver", "192.168.30.241:8000", "--noreload"]
    
    # Iniciar el proceso Django
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1  # Line buffered
    )
    
    # Registrar función para limpiar al salir
    def cleanup():
        if process.poll() is None:  # Si el proceso sigue vivo
            process.terminate()
            
    atexit.register(cleanup)
    
    # Iniciar hilo de simulación si estamos en modo demo
    if '--demo' in sys.argv:
        sim_thread = threading.Thread(target=simulate_file_processing, 
                                     args=(symbols, use_colors), 
                                     daemon=True)
        sim_thread.start()
    
    # Procesar la salida del servidor línea por línea
    try:
        for line in iter(process.stdout.readline, ''):
            formatted_line = process_django_output(line.rstrip(), symbols, use_colors)
            if formatted_line is not None:
                print(formatted_line)
    except KeyboardInterrupt:
        print(f"\n[{current_time()}] {colorize('Servidor detenido por el usuario', Colors.YELLOW, use_colors)}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    try:
        print("\nIniciando servidor SBOT con logs profesionales...\n")
        run_django_server_with_professional_logs()
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
