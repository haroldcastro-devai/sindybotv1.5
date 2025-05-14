#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, List, Union, Optional
from datetime import timedelta
from .logger_config import logger

def cargar_diccionario(ruta_diccionario: str) -> dict:
    """
    Carga el diccionario de correcciones.
    
    Args:
        ruta_diccionario: Ruta al archivo de diccionario
        
    Returns:
        dict: Diccionario con palabras a corregir
    """
    try:
        diccionario = {}
        with open(ruta_diccionario, 'r', encoding='utf-8') as file:
            for line in file.read().splitlines():
                partes = line.split(':')
                if len(partes) == 2:
                    diccionario[partes[0].strip()] = partes[1].strip()
                else:
                    logger.warning(f"Línea ignorada en diccionario: '{line}'")
        return diccionario
    except Exception as e:
        logger.error(f"Error cargando diccionario: {e}")
        return {}

def corregir_texto(texto: str, diccionario: dict) -> str:
    """
    Aplica correcciones al texto usando el diccionario.
    
    Args:
        texto: Texto a corregir
        diccionario: Diccionario de correcciones
        
    Returns:
        str: Texto corregido
    """
    try:
        palabras = texto.split()
        texto_corregido = []
        for palabra in palabras:
            palabra_corregida = diccionario.get(palabra.lower(), palabra)
            texto_corregido.append(palabra_corregida)
        return ' '.join(texto_corregido)
    except Exception as e:
        logger.error(f"Error corrigiendo texto: {e}")
        return texto

def pre_process_data(guiones: dict, tarifas: dict) -> tuple:
    """
    Preprocesa los datos de guiones y tarifas.
    
    Args:
        guiones: Datos de guiones
        tarifas: Datos de tarifas
        
    Returns:
        tuple: (guiones_formateados, tarifas_formateadas)
    """
    try:
        import json
        guiones_formatted = json.dumps(guiones, indent=2)
        tarifas_formatted = json.dumps(tarifas, indent=2)
        return guiones_formatted, tarifas_formatted
    except Exception as e:
        logger.error(f"Error en pre-procesamiento de datos: {e}")
        return "{}", "{}"

def unificar_transcripciones(transcripciones: List[dict]) -> str:
    """
    Unifica múltiples transcripciones en un solo texto coherente.
    
    Args:
        transcripciones: Lista de transcripciones
        
    Returns:
        str: Texto unificado
    """
    try:
        texto_unificado = ""
        tiempo_acumulado = 0

        for idx, trans in enumerate(transcripciones):
            if idx > 0:
                texto_unificado += "\n[CONTINUACIÓN DE LLAMADA]\n"

            # Ajustar timestamps
            for segmento in trans["segments"]:
                segmento['start'] += tiempo_acumulado
                segmento['end'] += tiempo_acumulado

            # Actualizar tiempo acumulado
            if trans["segments"]:
                tiempo_acumulado += trans["segments"][-1]['end']

            # Agregar segmentos al texto unificado
            for segmento in trans["segments"]:
                texto_unificado += f"\n[{segmento.get('speaker', 'Speaker')}]\n"
                texto_unificado += f"{timedelta(seconds=segmento['start'])} - {timedelta(seconds=segmento['end'])}: {segmento['text']}\n"

        return texto_unificado

    except Exception as e:
        logger.error(f"Error unificando transcripciones: {e}")
        return "ERROR: No se pudieron unificar las transcripciones"