#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gc
import json
import ollama
import re
from pathlib import Path
from typing import Dict, List, Union, Optional
import sys

# Asegurarnos que podemos importar desde el directorio padre
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importar módulos del paquete
from .logger_config import logger
from .detection import detectar_aceptacion, extract_names
from .text_processing import pre_process_data
from .file_utils import validate_call_content

# Importar módulos externos
from data_updateBD import guardar_resultado_auditoria, actualizar_estado_venta, insertar_datos_aprendizaje, obtener_datos_aprendizaje
from logic_utils.get_tags import obtener_gasera_seguro

# Importar el nuevo módulo de prompts mejorados
from enhanced_prompt import generar_prompt_mejorado, procesar_respuesta_modelo

# Constantes del sistema de evaluación
UMBRAL_VENTA_POSITIVA = 70
PESO_CRITERIOS_CRITICOS = 50
PESO_ADHERENCIA_GUION = 30
PESO_FACTORES_NEGATIVOS = 20

# Constantes de validación
MIN_ACEPTACIONES_REQUERIDAS = 3
MAX_RECHAZOS_PERMITIDOS = 0

# Tipos personalizados
JsonDict = Dict[str, Union[str, int, float, bool, dict, list]]
ValidationResult = Dict[str, Union[bool, int, str]]

def evaluar_llamada(transcripcion, tarifas, guion):
    """
    Sistema de puntuación con criterios balanceados para evaluar la llamada
    
    Args:
        transcripcion: Texto de la transcripción
        tarifas: Información de tarifas
        guion: Información de guiones
        
    Returns:
        dict: Resultado de la evaluación
    """
    resultado_aceptacion = detectar_aceptacion(transcripcion)

    puntuacion = 0
    detalles_evaluacion = {
        'criterios_cumplidos': [],
        'criterios_faltantes': [],
        'factores_negativos': [],
        'aceptaciones_detectadas': []
    }

    # Criterios con pesos ajustados y más flexibles
    criterios = {
        'criterios_criticos': {
            'aceptacion_basica': 20,     # Puntos por detectar al menos una aceptación
            'aceptacion_multiple': 10,    # Puntos extra por múltiples aceptaciones
            'mencion_tarifa': 15,         # Reducido para ser menos restrictivo
            'indemnizacion': 15,          # Reducido para ser menos restrictivo
            'entendimiento_cliente': 10   # Nuevo criterio
        },
        'adherencia_guion': {
            'saludo': 5,
            'explicacion': 10,
            'validacion': 5,
            'cierre': 5
        },
        'factores_negativos': {
            'rechazo_explicito': -50,     # Reducido para ser menos restrictivo
            'dudas_no_resueltas': -30,    # Reducido
            'informacion_incorrecta': -40  # Reducido
        }
    }

    # Evaluar aceptaciones
    if resultado_aceptacion['aceptacion']:
        puntuacion += criterios['criterios_criticos']['aceptacion_basica']
        detalles_evaluacion['criterios_cumplidos'].append('aceptacion_basica')

        if resultado_aceptacion['num_aceptaciones'] >= 3:
            puntuacion += criterios['criterios_criticos']['aceptacion_multiple']
            detalles_evaluacion['criterios_cumplidos'].append('aceptaciones_multiples')

        # Registrar detalles de aceptaciones
        for aceptacion in resultado_aceptacion['detalles_aceptaciones']:
            detalles_evaluacion['aceptaciones_detectadas'].append({
                'texto': aceptacion['texto'],
                'contexto': aceptacion['contexto']
            })

    # Evaluar criterios de guion
    palabras_clave_guion = {
        'saludo': ['buenos días', 'buenas tardes', 'buenas noches'],
        'explicacion': ['le informo', 'le explico', 'le comento'],
        'validacion': ['confirma', 'verifica', 'está de acuerdo'],
        'cierre': ['gracias por su tiempo', 'que tenga', 'hasta luego']
    }

    for tipo, palabras in palabras_clave_guion.items():
        if any(palabra in transcripcion.lower() for palabra in palabras):
            puntuacion += criterios['adherencia_guion'][tipo]
            detalles_evaluacion['criterios_cumplidos'].append(f'guion_{tipo}')

    # Ajuste de calificación final
    puntuacion_final = min(max(puntuacion, 0), 100)

    # Determinar calificación con criterios más flexibles
    if resultado_aceptacion['num_rechazos'] > 0:
        calificacion = 'NEGATIVA'
    elif puntuacion_final >= 60 and resultado_aceptacion['aceptacion']:  # Umbral reducido
        calificacion = 'POSITIVA'
    elif puntuacion_final >= 40 and resultado_aceptacion['num_aceptaciones'] >= 2:  # Caso especial
        calificacion = 'POSITIVA'
    else:
        calificacion = 'NEGATIVA'

    return {
        'puntuacion': puntuacion_final,
        'calificacion': calificacion,
        'detalles': detalles_evaluacion,
        'aceptacion': resultado_aceptacion
    }

def process_call(file_path: str, guiones: JsonDict, tarifas: JsonDict) -> str:
    """
    Procesa el contenido de una llamada y genera un reporte de auditoría.
    
    Args:
        file_path: Ruta al archivo de transcripción
        guiones: Información de guiones
        tarifas: Información de tarifas
        
    Returns:
        str: Resultado de la auditoría
    """
    nombre_archivo = os.path.basename(file_path) 
   
    try:
        # Registrar el inicio del procesamiento
        logger.info(f"Iniciando procesamiento de llamada: {file_path}")

        # Obtener el nombre de la gasera y otros datos
        gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(nombre_archivo)

        # Validar si la gasera es desconocida
        if not gasera:
            logger.error("No se pudo determinar la gasera a partir del nombre del archivo.")
            raise ValueError("Gasera desconocida o no válida.")
    
        # Usar el nombre de la gasera en el reporte de auditoría
        logger.info(f"Procesando archivo para la gasera: {gasera}")
        
        # Recuperar datos de aprendizaje previo
        datos_aprendizaje = obtener_datos_aprendizaje()
        logger.info(f"Datos de aprendizaje recuperados: {len(datos_aprendizaje)} registros")

        # Leer contenido del archivo
        with open(file_path, "r", encoding="utf-8") as f:
            contenido = f.read()

        # Pre-procesar y validar datos
        guiones_formatted, tarifas_formatted = pre_process_data(guiones, tarifas)
        validacion = validate_call_content(contenido, guiones, tarifas)
        asesor, cliente = extract_names(contenido)

        # Evaluación cuantitativa (mantenemos esta función para compatibilidad)
        evaluacion = evaluar_llamada(contenido, tarifas, guiones)

        # Crear metadatos para el prompt mejorado
        metadata = {
            'gasera': gasera,
            'contrato': num_contrato,
            'fecha': fecha_contrato,
            'seguro': seguro_1 if seguro_1 else seguro_2 if seguro_2 else seguro_3,
            'asesor': asesor,
            'cliente': cliente,
            'tarifas': tarifas,
            'guiones': guiones,
            'evaluacion_previa': evaluacion
        }
        
        # Generar prompt mejorado
        logger.info("Generando prompt mejorado para la auditoría")
        prompt_mejorado = generar_prompt_mejorado(contenido, metadata)
        
        # Procesamiento con OLLAMA
        max_intentos = 3
        resultado = None

        for intento in range(max_intentos):
            try:
                logger.info(f"Intento {intento + 1} de análisis con el modelo de IA")
                # Usamos el mismo modelo qwen2.5 pero con el prompt mejorado
                model = ollama.Client()
                response = model.generate(model="qwen2.5:14b-instruct-q6_K", prompt=prompt_mejorado)
                resultado = response['response']
                logger.info(f"Análisis completado correctamente en intento {intento + 1}")
                break
            except Exception as e:
                logger.error(f"Intento {intento + 1} fallido: {e}")
                if intento == max_intentos - 1:
                    raise Exception(f"Error después de {max_intentos} intentos")
                continue

        if not resultado:
            raise Exception("No se pudo obtener respuesta del modelo")

        # Procesar respuesta para extraer datos estructurados (nuevo)
        datos_estructurados = procesar_respuesta_modelo(resultado)
        logger.info(f"Respuesta procesada y estructurada: {list(datos_estructurados.keys())}")

        # Extraer calificación de los datos estructurados (nuevo)
        if 'decision' in datos_estructurados and datos_estructurados['decision']:
            calificacion = 'POSITIVA' if datos_estructurados['decision'] == 'APROBADA' else 'NEGATIVA'
        else:
            # Método anterior como fallback
            from .detection import extraer_calificacion
            calificacion = extraer_calificacion(resultado)
            
        # Verificación adicional: buscar patrones positivos explícitos en el resultado
        # para evitar falsos negativos
        patrones_positivos_explicitos = [
            r'\bPOSITIVA\b',
            r'\bAPROBADA\b',
            r'CALIFICACIÓN FINAL:\s*\[?\s*POSITIVA\s*\]?',
            r'venta\s+POSITIVA',
            r'se considera aprobada'
        ]
        
        for patron in patrones_positivos_explicitos:
            if re.search(patron, resultado, re.IGNORECASE):
                logger.info("Se detectó un patrón positivo explícito en el reporte")
                calificacion = 'POSITIVA'
                break
                
        # Log para debug
        logger.info(f"Calificación final determinada: {calificacion}")
        logger.info(f"Esta calificación será guardada en la base de datos")

        # Actualizar estado de venta - asegurar que se almacene la calificación correcta
        from data_updateBD import actualizar_estado_venta
        actualizar_estado_venta(num_contrato, calificacion)

        # Guardar el resultado textual de la auditoría
        guardar_resultado_auditoria(resultado)

        # Almacenar datos de aprendizaje
        detalles_evaluacion = {
            'criterios_cumplidos': evaluacion['detalles']['criterios_cumplidos'],
            'criterios_faltantes': evaluacion['detalles']['criterios_faltantes'],
            'factores_negativos': evaluacion['detalles']['factores_negativos'],
            'aceptaciones_detectadas': evaluacion['detalles']['aceptaciones_detectadas']
        }
        insertar_datos_aprendizaje(contenido, calificacion, detalles_evaluacion)

        logger.info(f"Procesamiento completado para {file_path}")

        # Limpieza de memoria
        del contenido, prompt_mejorado
        gc.collect()

        return resultado

    except Exception as e:
        logger.error(f"Error en process_call: {e}")
        return f"ERROR: {str(e)}"