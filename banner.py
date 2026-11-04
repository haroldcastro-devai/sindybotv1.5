"""
Módulo que contiene el banner de presentación para SBOT.
Este archivo permite separar la presentación visual del sistema
de la lógica de ejecución, facilitando su mantenimiento.
"""

import os
import sys
import platform

# Códigos ANSI para colores
GREEN = "\033[32m"  # Verde
BRIGHT_GREEN = "\033[92m"  # Verde brillante
RED = "\033[31m"  # Rojo
BRIGHT_RED = "\033[91m"  # Rojo brillante
RESET = "\033[0m"  # Restablecer color


# Banner Unicode (para terminales compatibles)
UNICODE_BANNER = f"""{GREEN}
╭──────────────────────────────────────────────────────────────────────────╮
│                                                                          │
│    ██████╗██████╗  ██████╗ ████████╗                                     │
│   ██╔════╝██╔══██╗██╔═══██╗╚══██╔══╝              SISTEMA IA             │
│   ╚█████╗ ██████╔╝██║   ██║   ██║                 DE AUDITORÍA           │
│    ╚═══██╗██╔══██╗██║   ██║   ██║                                        │
│   ██████╔╝██████╔╝╚██████╔╝   ██║                                        │
│   ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝                                        │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────┐         │
│   │{RED}Versión: 1.5.8.0{GREEN}                                            │         │
│   │{RED}Last Update: 2024-12-20{GREEN}                                     │         │
│   │Environment: {RED}Production{GREEN}                                     │         │
│   │Dev : Harold Castro                                         │         │
│   │Cliente: XUMA                                               │         │
│   └────────────────────────────────────────────────────────────┘         │
│                                                                          │
╰──────────────────────────────────────────────────────────────────────────╯
{RESET}"""

def is_unicode_supported():
    """
    Verifica si la terminal actual soporta caracteres Unicode.
    
    Returns:
        bool: True si soporta Unicode, False en caso contrario.
    """
    # Verificar codificación de la terminal
    try:
        # Intentar detectar la codificación actual
        encoding = sys.stdout.encoding
        if encoding is None or encoding.lower() not in ('utf-8', 'utf8'):
            return False
            
        if platform.system() == 'Windows':
            # PowerShell / Windows Terminal (sin subprocess ni shell=True)
            if os.environ.get("PSModulePath") or os.environ.get("WT_SESSION"):
                return True
            return False

        # En otros sistemas, intentar escribir un carácter Unicode
        # y ver si hay error
        try:
            sys.stdout.write('✓')
            sys.stdout.flush()
            return True
        except UnicodeEncodeError:
            return False
    except:
        return False
    
    # Por defecto, asumir que no soporta Unicode
    return False

def supports_ansi_colors():
    """
    Detecta si la terminal actual soporta colores ANSI.
    
    Returns:
        bool: True si soporta colores, False en caso contrario.
    """
    # Si no estamos en una terminal, no hay soporte de color
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    
    # Windows 10 o superior con terminal moderna soporta colores
    if platform.system() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Obtener versión de Windows
            version = sys.getwindowsversion()
            if version.major >= 10:
                # Comprobar si la terminal es compatible con ANSI
                mode = ctypes.c_int()
                kernel32.GetConsoleMode(kernel32.GetStdHandle(-11), ctypes.byref(mode))
                if mode.value & 4:  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                    return True
        except:
            return False
    
    # En sistemas Unix-like, comprobamos la variable TERM
    return os.environ.get('TERM') not in (None, '', 'dumb')

def get_banner():
    """
    Retorna el banner de SBOT adaptado a la terminal.
    Detecta automáticamente si la terminal soporta Unicode y colores.
    
    Returns:
        str: El banner formateado adecuadamente para la terminal actual.
    """
    try:
        # Intentar la versión Unicode si es soportada
        if is_unicode_supported() and supports_ansi_colors():
            return UNICODE_BANNER
    except:
        pass
    
    # Si hay algún problema o no se soporta Unicode, usar ASCII
    return ASCII_BANNER

def get_colored_text(text, color=GREEN):
    """
    Aplica color a un texto si es soportado por la terminal.
    
    Args:
        text (str): Texto a colorear.
        color (str, optional): Código ANSI del color. Por defecto es verde.
    
    Returns:
        str: Texto coloreado o sin colorear dependiendo de la terminal.
    """
    if supports_ansi_colors():
        return f"{color}{text}{RESET}"
    return text

if __name__ == "__main__":
    # Si se ejecuta directamente este script, muestra el banner
    print(get_banner())
    print(get_colored_text("SBOT está iniciado y funcionando correctamente."))
