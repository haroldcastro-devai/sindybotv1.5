#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import logging
import os
import sys
import tempfile
import atexit

from core.cli_logging import configure_cli_logging

configure_cli_logging()
logger = logging.getLogger(__name__)

def safe_banner():
    """
    Retorna un banner seguro que funciona en cualquier terminal.
    """
    return """
"""

# Importar el banner desde el módulo banner, con manejo seguro de errores
banner_module_available = False
try:
    # Primero intentamos importar solo las funciones auxiliares
    from banner import is_unicode_supported, supports_ansi_colors
    
    # Si funciona, intentamos obtener el banner
    if is_unicode_supported() and supports_ansi_colors():
        from banner import get_banner
        banner_module_available = True
    else:
        def get_banner():
            return safe_banner()
except (ImportError, UnicodeEncodeError):
    # Si hay algún error, utilizamos el banner seguro
    def get_banner():
        return safe_banner()

# Archivo de bloqueo para controlar si el banner ya se mostró en esta sesión
lock_file = os.path.join(tempfile.gettempdir(), 'sbot_banner_lock')

def cleanup():
    """Eliminar el archivo de bloqueo al salir"""
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except OSError as exc:
            logger.debug("No se pudo eliminar %s: %s", lock_file, exc)

# Registrar la función de limpieza para ejecutarse al salir
atexit.register(cleanup)

def display_banner_once():
    """Muestra el banner solo una vez por sesión de terminal"""
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        # Comprobamos si el PID del proceso padre ya ha mostrado el banner
        parent_pid = os.getppid()
        
        # Verificamos si existe el archivo de bloqueo
        if not os.path.exists(lock_file):
            # Forzar el soporte de color en Windows si es posible
            if sys.platform == 'win32':
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                except (OSError, AttributeError) as exc:
                    logger.debug("Consola Windows sin modo ANSI: %s", exc)
            
            try:
                # Intentamos mostrar el banner
                banner = get_banner()
                print(banner)
            except UnicodeEncodeError:
                # Si hay error de codificación, usamos el banner seguro
                print(safe_banner())
            except Exception as exc:
                logger.warning("Error al mostrar banner: %s", exc, exc_info=True)
                print("\n=== SBOT v1.5.8.0 - SISTEMA IA DE AUDITORIA ===\n")
            
            print(f"\n{'=' * 78}\n")  # Línea separadora
            
            # Creamos el archivo de bloqueo
            try:
                with open(lock_file, 'w') as f:
                    f.write(str(parent_pid))
            except OSError as exc:
                logger.debug("No se pudo crear lock de banner: %s", exc)

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    
    try:
        # Mostrar el banner solo una vez, con manejo de errores
        display_banner_once()
    except Exception as exc:
        logger.debug("Banner omitido: %s", exc, exc_info=True)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
