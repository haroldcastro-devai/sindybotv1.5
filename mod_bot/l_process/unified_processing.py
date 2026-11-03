#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path
from typing import Dict, List, Union, Optional
import sys

# Asegurarnos que podemos importar desde el directorio padre
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from .logger_config import logger
from .stt_provider import procesar_audio_via_provider
from .text_processing import unificar_transcripciones
from .file_utils import load_json_file
from .detection import extraer_calificacion
from .call_evaluation import process_call
from logic_utils.get_tags import obtener_gasera_seguro
from .detection import extract_names
from data_updateBD import guardar_resultado_auditoria, actualizar_estado_venta

from .llm_client import generate_from_prompt

# Importar el nuevo módulo de prompts mejorados
from enhanced_prompt import generar_prompt_mejorado, procesar_respuesta_modelo

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

       # Extraer metadatos del nombre del archivo o de la información del grupo
       try:
           if 'metadata' in grupo_archivos and grupo_archivos['metadata']:
               gasera = grupo_archivos['metadata'].get('gasera', 'Desconocido')
               num_contrato = grupo_archivos['metadata'].get('contrato', numero_contrato)
               fecha_contrato = grupo_archivos['metadata'].get('fecha', 'Desconocido')
               seguro = grupo_archivos['metadata'].get('seguro', 'Desconocido')
           else:
               gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(nombre_archivo)
               seguro = seguro_1 if seguro_1 else seguro_2 if seguro_2 else seguro_3
       except Exception as e:
           logger.warning(f"Error obteniendo metadatos del archivo: {e}")
           gasera, num_contrato, fecha_contrato, seguro = "Desconocido", numero_contrato, "Desconocido", "Desconocido"

       transcripciones = []
       resultados = []
       errores = []

       for parte in grupo_archivos['partes']:
           try:
               logger.info(f"Procesando parte: {parte['parte']}")
               diarized_text, _, result = procesar_audio_via_provider(parte['ruta'])
               transcripciones.append(diarized_text)
               resultados.append(result)
           except Exception as e:
               error_msg = f"Error procesando parte {parte['parte']}: {str(e)}"
               logger.error(error_msg)
               errores.append(error_msg)
               continue

       if not transcripciones:
           error_msg = "ERROR: No se pudo procesar ninguna parte del audio"
           logger.error(error_msg)
           return error_msg

       texto_unificado = unificar_transcripciones(resultados)
       nombre_sin_parte = nombre_archivo.rsplit('_', 1)[0]
       nombre_archivo_unificado = f"{nombre_sin_parte}.gsm_UNIFICADO"
       nombre_archivo_auditoria = f"{nombre_sin_parte}.gsm_auditoria_UNIFICADO"
       txt_file_path = UNIFIED_FILES / f"{nombre_archivo_unificado}.txt"

       try:
           with open(txt_file_path, 'w', encoding='utf-8') as file:
               file.write(texto_unificado)
       except Exception as e:
           error_msg = f"Error guardando transcripción unificada: {e}"
           logger.error(error_msg)
           return error_msg

       # Extraer nombres de asesor y cliente
       asesor, cliente = extract_names(texto_unificado)

       # Crear metadatos para el prompt mejorado
       metadata = {
           'gasera': gasera,
           'contrato': num_contrato,
           'fecha': fecha_contrato,
           'seguro': seguro,
           'asesor': asesor,
           'cliente': cliente,
           'tarifas': tarifas,
           'guiones': guiones,
           'es_audio_dividido': True
       }

       # Decidir si usar el nuevo sistema de análisis o el antiguo
       # Para asegurar compatibilidad, usamos el nuevo sistema por defecto,
       # pero tenemos el antiguo como respaldo en caso de error
       try:
           logger.info("Iniciando procesamiento con prompts mejorados para audio dividido")
           
           # Generar prompt mejorado con la transcripción y metadatos
           prompt_mejorado = generar_prompt_mejorado(texto_unificado, metadata)
           
           logger.info("Análisis audio dividido con llm_client")
           resultado_auditoria = generate_from_prompt(
               prompt_mejorado,
               temperature=0.3,
               max_output_tokens=8192,
           )
           
           # Extraer calificación del resultado
           try:
               datos_estructurados = procesar_respuesta_modelo(resultado_auditoria)
               logger.info(f"Respuesta procesada y estructurada: {list(datos_estructurados.keys())}")
               
               # Determinar calificación a partir de los datos estructurados
               if 'decision' in datos_estructurados and datos_estructurados['decision']:
                   calificacion = 'POSITIVA' if datos_estructurados['decision'] == 'APROBADA' else 'NEGATIVA'
               else:
                   calificacion = extraer_calificacion(resultado_auditoria)
           except Exception as e:
               logger.warning(f"Error procesando respuesta estructurada para audio dividido: {e}")
               calificacion = extraer_calificacion(resultado_auditoria)
       
       except Exception as e:
           logger.warning(f"Error en el procesamiento mejorado para audio dividido: {e}. Usando método antiguo.")
           # Caer al método antiguo en caso de error
           resultado_auditoria = process_call(txt_file_path, guiones, tarifas)
           calificacion = extraer_calificacion(resultado_auditoria)

       # Actualizar estado
       actualizar_estado_venta(num_contrato, calificacion)

       # Guardar auditoria directamente en BD
       guardar_resultado_auditoria(resultado_auditoria)

       # Guardar archivo de auditoría
       audit_file_path = LOG_SALES_AUDIT / f"{nombre_archivo_auditoria}.txt"
       try:
           with open(audit_file_path, 'w', encoding='utf-8') as audit_file:
               audit_file.write(resultado_auditoria)
       except Exception as e:
           logger.error(f"Error guardando archivo de auditoría: {e}")

       if errores:
           resultado_auditoria += "\n\nADVERTENCIA: Se encontraron los siguientes errores durante el procesamiento:\n"
           resultado_auditoria += "\n".join(errores)

       logger.info(f"Procesamiento de audio dividido completado. Calificación: {calificacion}")
       return resultado_auditoria

   except Exception as e:
       error_msg = f"Error en procesamiento de audio dividido: {e}"
       logger.error(error_msg)
       return error_msg