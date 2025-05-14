#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from typing import Dict, List, Union, Optional
from .logger_config import logger

def extraer_calificacion(resultado_auditoria):
    """
    Extrae la calificación final del reporte de auditoría.
    
    Args:
        resultado_auditoria: Texto del reporte de auditoría
        
    Returns:
        str: 'POSITIVA' o 'NEGATIVA'
    """
    # Expresión regular mejorada
    calificacion_match = re.search(
        r'(?:Calificación\s*de\s*la\s*venta:?\s*)?.*?(POSITIVA|NEGATIVA)',
        resultado_auditoria,
        re.IGNORECASE | re.DOTALL
    )

    if calificacion_match:
        calificacion = calificacion_match.group(1).upper()
        if calificacion == "POSITIVA":
            return "POSITIVA"
        elif calificacion == "NEGATIVA":
            return "NEGATIVA"

    # Si no se encuentra una calificación válida, registrar un error
    logger.error(f"No se pudo extraer la calificación del reporte: {resultado_auditoria[:200]}...")
    return "NEGATIVA"  # Por defecto, asumir negativa si hay un error

def detectar_aceptacion(texto):
    """
    Sistema mejorado de detección de aceptación que reconoce más patrones
    y es más flexible en la interpretación
    
    Args:
        texto: Texto a analizar para detectar aceptación
        
    Returns:
        dict: Resultado del análisis con detalles de aceptaciones y rechazos
    """
    patrones_aceptacion = [
        # Aceptaciones simples
        r'(?i)\b(?:sí|si)\b',
        r'(?i)\bacepto\b',
        r'(?i)\bclaro\b',

        # Aceptaciones explícitas
        r'(?i)(?:sí|si),?\s*(?:estoy|estamos)?\s*(?:de acuerdo|acepto|conforme)',
        r'(?i)(?:sí|si),?\s*(?:entiendo|entendido)',
        r'(?i)(?:sí|si),?\s*(?:me|nos)?\s*parece\s*bien',
        r'(?i)estoy\s*de\s*acuerdo',
        r'(?i)me\s*parece\s*bien',

        # Confirmaciones de entendimiento
        r'(?i)(?:sí|si),?\s*(?:lo|le)?\s*entiendo',
        r'(?i)(?:sí|si),?\s*está\s*claro',
        r'(?i)(?:sí|si),?\s*comprendo',
        r'(?i)entendido',

        # Aceptaciones de valor/monto
        r'(?i)(?:sí|si),?\s*(?:acepto|está bien)\s*(?:el|ese|este)?\s*(?:valor|monto|precio|costo)',
        r'(?i)(?:sí|si),?\s*estoy\s*de\s*acuerdo\s*con\s*(?:el|ese|este)?\s*(?:valor|monto|precio|costo)',

        # Aceptaciones de servicio
        r'(?i)(?:sí|si),?\s*(?:quiero|deseo)\s*(?:el|este)?\s*(?:servicio|seguro|plan)',
        r'(?i)(?:sí|si),?\s*(?:me|nos)?\s*interesa',

        # Expresiones informales de aceptación
        r'(?i)correcto',
        r'(?i)exacto',
        r'(?i)así\s*es',
        r'(?i)está\s*bien'
    ]

    patrones_rechazo = [
        r'(?i)no\s*(?:quiero|deseo|acepto)',
        r'(?i)no\s*estoy\s*(?:de acuerdo|seguro)',
        r'(?i)no\s*me\s*interesa',
        r'(?i)tengo\s*que\s*pensarlo',
        r'(?i)necesito\s*tiempo',
        r'(?i)lo\s*voy\s*a\s*pensar',
        r'(?i)\bno\b\s*(?:gracias|quiero continuar)',
        r'(?i)\bno\b\s*(?:por ahora|en este momento)',
        r'(?i)\bno\b\s*(?:sé|estoy seguro)',
        r'(?i)\btal vez\b'
    ]

    # Buscar todas las coincidencias de aceptación
    aceptaciones = []
    for patron in patrones_aceptacion:
        coincidencias = re.finditer(patron, texto)
        for match in coincidencias:
            # Extraer un contexto de 50 caracteres antes y después
            inicio = max(0, match.start() - 50)
            fin = min(len(texto), match.end() + 50)
            contexto = texto[inicio:fin]
            aceptaciones.append({
                'patron': patron,
                'texto': match.group(),
                'contexto': contexto
            })

    # Buscar rechazos
    rechazos = []
    for patron in patrones_rechazo:
        coincidencias = re.finditer(patron, texto)
        for match in coincidencias:
            inicio = max(0, match.start() - 50)
            fin = min(len(texto), match.end() + 50)
            contexto = texto[inicio:fin]
            rechazos.append({
                'patron': patron,
                'texto': match.group(),
                'contexto': contexto
            })

    # Análisis de resultados
    num_aceptaciones = len(aceptaciones)
    num_rechazos = len(rechazos)

    # Calificar confianza
    if num_aceptaciones >= 3 and num_rechazos == 0:
        nivel_confianza = 'ALTA'
    elif num_aceptaciones > 1 and num_rechazos == 0:
        nivel_confianza = 'MEDIA'
    elif num_aceptaciones > 0 and num_rechazos == 0:
        nivel_confianza = 'BAJA'
    else:
        nivel_confianza = 'NULA'

    return {
        'aceptacion': num_aceptaciones > 0 and num_rechazos == 0,
        'num_aceptaciones': num_aceptaciones,
        'num_rechazos': num_rechazos,
        'confianza': nivel_confianza,
        'detalles_aceptaciones': aceptaciones,
        'detalles_rechazos': rechazos
    }

def extract_names(contenido: str) -> tuple:
    """
    Extrae nombres de asesor y cliente del contenido.
    
    Args:
        contenido: Texto a analizar
        
    Returns:
        tuple: (nombre_asesor, nombre_cliente)
    """
    try:
        asesor_match = re.search(r'ASESOR:\s*(\w+(?:\s+\w+)?)', contenido)
        cliente_match = re.search(r'CLIENTE:\s*(\w+(?:\s+\w+)?)', contenido)

        asesor = asesor_match.group(1) if asesor_match else "No identificado"
        cliente = cliente_match.group(1) if cliente_match else "No identificado"

        return asesor, cliente
    except Exception as e:
        logger.error(f"Error extrayendo nombres: {e}")
        return "No identificado", "No identificado"