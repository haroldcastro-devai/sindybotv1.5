#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path
from typing import Dict, List, Union, Optional
from .logger_config import logger
from .audio_processing import procesar_audio
from .text_processing import unificar_transcripciones
from .file_utils import load_json_file
from .detection import extraer_calificacion
from .call_evaluation import process_call
from data_updateBD import guardar_resultado_auditoria, actualizar_estado_venta

# Definir rutas usando rutas relativas
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
LLAMADAS_DIR = DATA_DIR / "llamadas"

# Crear el directorio audio-text en la raíz del proyecto
AUDIO_TEXT_DIR = PROJECT_ROOT / "audio-text"
LOG_AUDIO_TO_TEXT = AUDIO_TEXT_DIR / "log_audio_to_text"
LOG_SALES_AUDIT = AUDIO_TEXT_DIR / "Log_sales_audito"
UNIFIED_FILES = AUDIO_TEXT_DIR / "uni_files_audito"

# Asegurarse de que los directorios existen
for dir_path in [AUDIO_TEXT_DIR, LOG_AUDIO_TO_TEXT, LOG_SALES_AUDIT, UNIFIED_FILES]:
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creando directorio {dir_path}: {e}")

def procesar_audio_dividido(grupo_archivos: dict) -> str:
   """
   Procesa un grupo de archivos de audio que pertenecen a la misma llamada dividida.
   
   Args:
       grupo_archivos: Diccionario con información de las partes de audio
       
   Returns:
       str: Resultado de la auditoría
   """
   try:
       nombre_archivo = os.path.basename(grupo_archivos['partes'][0]['ruta'])
       partes_nombre = nombre_archivo.split("_")
       numero_contrato = partes_nombre[1] if len(partes_nombre) > 1 else "DESCONOCIDO"

       guiones = load_json_file(RAW_DIR / "guionV2.json")
       tarifas = load_json_file(RAW_DIR / "tarifasV2.json")

       if not guiones or not tarifas:
           error_msg = "Error: No se pudieron cargar los archivos de guiones o tarifas"
           logger.error(error_msg)
           return error_msg

       transcripciones = []
       errores = []

       for parte in grupo_archivos['partes']:
           try:
               logger.info(f"Procesando parte: {parte['parte']}")
               diarized_text, _, result = procesar_audio(parte['ruta'])
               transcripciones.append(result)
           except Exception as e:
               error_msg = f"Error procesando parte {parte['parte']}: {str(e)}"
               logger.error(error_msg)
               errores.append(error_msg)
               continue

       if not transcripciones:
           error_msg = "ERROR: No se pudo procesar ninguna parte del audio"
           logger.error(error_msg)
           return error_msg

       texto_unificado = unificar_transcripciones(transcripciones)
       nombre_sin_parte = nombre_archivo.rsplit('_', 1)[0]
       nombre_archivo_unificado = f"{nombre_sin_parte}.gsm_UNIFICADO"
       nombre_archivo_auditoria = f"{nombre_sin_parte}.gsm_auditoria_UNIFICADO"
       txt_file_path = UNIFIED_FILES / nombre_archivo_unificado

       try:
           with open(txt_file_path, 'w', encoding='utf-8') as file:
               file.write(texto_unificado)
       except Exception as e:
           error_msg = f"Error guardando transcripción unificada: {e}"
           logger.error(error_msg)
           return error_msg

       # Obtener resultado y calificación
       resultado_auditoria = process_call(txt_file_path, guiones, tarifas)

       # Extraer calificación
       calificacion = extraer_calificacion(resultado_auditoria)

       # Actualizar estado
       actualizar_estado_venta(numero_contrato, calificacion)

       # Guardar auditoria directamente
       guardar_resultado_auditoria(resultado_auditoria)

       # Guardar archivo de auditoría
       audit_file_path = LOG_SALES_AUDIT / nombre_archivo_auditoria
       try:
           with open(audit_file_path, 'w', encoding='utf-8') as audit_file:
               audit_file.write(resultado_auditoria)
       except Exception as e:
           logger.error(f"Error guardando archivo de auditoría: {e}")

       if errores:
           resultado_auditoria += "\n\nADVERTENCIA: Se encontraron los siguientes errores durante el procesamiento:\n"
           resultado_auditoria += "\n".join(errores)

       return resultado_auditoria

   except Exception as e:
       error_msg = f"Error en procesamiento de audio dividido: {e}"
       logger.error(error_msg)
       return error_msg