#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path
from typing import Dict, List, Union, Optional
from .logger_config import logger

# Tipo personalizado para facilitar anotaciones
JsonDict = Dict[str, Union[str, int, float, bool, dict, list]]

def validar_estructura_guion(data: JsonDict) -> bool:
    """
    Valida la estructura del archivo de guiones.
    
    Args:
        data: Datos del guion a validar
        
    Returns:
        bool: True si la estructura es válida, False en caso contrario
    """
    try:
        required_keys = {'gaseras', 'planes'}
        if not all(key in data for key in required_keys):
            logger.error("Estructura de guion inválida: faltan claves requeridas")
            return False

        if not isinstance(data['gaseras'], list) or not isinstance(data['planes'], dict):
            logger.error("Estructura de guion inválida: tipo de datos incorrecto")
            return False

        return True
    except Exception as e:
        logger.error(f"Error validando estructura de guion: {e}")
        return False

def validar_estructura_tarifas(data: JsonDict) -> bool:
    """
    Valida la estructura del archivo de tarifas.
    
    Args:
        data: Datos de tarifas a validar
        
    Returns:
        bool: True si la estructura es válida, False en caso contrario
    """
    try:
        if 'GASERAS_TARIFAS_INDEMNIZACION_COVERTURA' not in data:
            logger.error("Estructura de tarifas inválida: falta clave principal")
            return False

        for gasera, info in data['GASERAS_TARIFAS_INDEMNIZACION_COVERTURA'].items():
            if 'aseguradoras' not in info:
                logger.error(f"Estructura de tarifas inválida en gasera {gasera}")
                return False

            for aseguradora in info['aseguradoras']:
                if 'planes' not in aseguradora:
                    logger.error(f"Estructura de tarifas inválida en aseguradora de {gasera}")
                    return False

        return True
    except Exception as e:
        logger.error(f"Error validando estructura de tarifas: {e}")
        return False

def load_json_file(file_path: Path) -> Optional[JsonDict]:
    """
    Carga y valida un archivo JSON.
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Optional[JsonDict]: Datos cargados o None si hay error
    """
    try:
        if not file_path.exists():
            logger.error(f"Archivo no encontrado: {file_path}")
            return None

        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if not isinstance(data, (dict, list)):
                logger.error(f"Formato inválido en {file_path}")
                return None

            # Validación específica para cada tipo de archivo
            if 'guionV3.json' in str(file_path):
                if not validar_estructura_guion(data):
                    return None
            elif 'tarifasV2.json' in str(file_path):
                if not validar_estructura_tarifas(data):
                    return None

            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error leyendo archivo {file_path}: {e}")
        return None

def validate_call_content(contenido: str, guiones: JsonDict, tarifas: JsonDict) -> JsonDict:
    """
    Valida el contenido de la llamada contra guiones y tarifas.
    
    Args:
        contenido: Texto de la transcripción
        guiones: Información de guiones
        tarifas: Información de tarifas
        
    Returns:
        JsonDict: Resultado de la validación
    """
    try:
        # Validar adherencia al guión
        adherencia_guion = any(g.lower() in contenido.lower() for g in guiones.get('gaseras', []))

        # Validar menciones de tarifas y montos
        menciones_tarifas = 0
        montos_mencionados = []

        for gasera_data in tarifas.get('GASERAS_TARIFAS_INDEMNIZACION_COVERTURA', {}).values():
            if isinstance(gasera_data, dict) and 'aseguradoras' in gasera_data:
                for aseguradora in gasera_data['aseguradoras']:
                    for plan_name, plan in aseguradora.get('planes', {}).items():
                        # Verificar menciones del plan
                        if plan_name.lower() in contenido.lower():
                            menciones_tarifas += 1

                        # Verificar valores monetarios
                        if isinstance(plan, dict):
                            for key, value in plan.items():
                                if isinstance(value, (int, float)) and str(value) in contenido:
                                    montos_mencionados.append({
                                        'plan': plan_name,
                                        'tipo': key,
                                        'valor': value
                                    })

        # Validar palabras negativas
        palabras_negativas = [
            'no quiero', 'no me interesa', 'no acepto', 'no estoy de acuerdo',
            'lo pensaré', 'después', 'más tarde', 'no entiendo', 'muy caro',
            'no puedo', 'no tengo', 'mejor otro día'
        ]
        tiene_palabras_negativas = any(palabra in contenido.lower() for palabra in palabras_negativas)

        return {
            'adherencia_guion': adherencia_guion,
            'menciones_tarifas': menciones_tarifas,
            'montos_mencionados': montos_mencionados,
            'tiene_palabras_negativas': tiene_palabras_negativas,
            'validacion_exitosa': True
        }
    except Exception as e:
        logger.error(f"Error en validación de contenido: {e}")
        return {
            'adherencia_guion': False,
            'menciones_tarifas': 0,
            'montos_mencionados': [],
            'tiene_palabras_negativas': False,
            'validacion_exitosa': False,
            'error': str(e)
        }