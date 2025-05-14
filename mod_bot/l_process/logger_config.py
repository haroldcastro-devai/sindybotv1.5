#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
from typing import Dict, List, Union, Optional

# Obtener ruta relativa a la raíz del proyecto
# l_process -> mod_bot -> raíz del proyecto
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = BASE_DIR.parent
LOG_FILE = PROJECT_ROOT / "auditoria.log"

# Configuración de logging
logger = logging.getLogger(__name__)

def configure_logging():
    """
    Configura el sistema de logging para la aplicación.
    Establece el nivel de detalle y los manejadores para guardar logs en archivo y mostrarlos en consola.
    """
    try:
        # Asegurarse de que el directorio de logs existe
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    except Exception as e:
        # Si hay algún error al configurar el logging, al menos configurar la salida a consola
        print(f"Error configurando logging: {e}")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
    
    return logging.getLogger(__name__)