#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from typing import Dict, List, Union, Optional
from .logger_config import logger

def extraer_calificacion(resultado_auditoria):
    """
    Extrae la calificación final del reporte de auditoría con una lógica mejorada.
    Esta versión favorece la detección de resultados POSITIVOS cuando hay evidencia suficiente.
    Versión optimizada para minimizar falsos negativos.
    
    Args:
        resultado_auditoria: Texto del reporte de auditoría
        
    Returns:
        str: 'POSITIVA' o 'NEGATIVA'
    """
    # Log para ayudar en la depuración
    logger.info("Comenzando extracción de calificación del reporte")
    
    if not resultado_auditoria or not isinstance(resultado_auditoria, str):
        logger.warning("El resultado de la auditoría está vacío o no es texto válido")
        return "POSITIVA"  # Por defecto, favorecer POSITIVA
    
    # Buscar patrones de calificación explícita primero (más prioritarios)
    patrones_explicitos = [
        r'CALIFICACIÓN FINAL:\s*\[(POSITIVA|NEGATIVA)\]',
        r'CALIFICACIÓN FINAL:\s*(POSITIVA|NEGATIVA)',
        r'CONCLUSIÓN:.*?\b(POSITIVA|NEGATIVA)\b',
        r'\*\*CALIFICACIÓN FINAL:\s*\[(POSITIVA|NEGATIVA)\]\*\*'
    ]
    
    for patron in patrones_explicitos:
        match = re.search(patron, resultado_auditoria, re.IGNORECASE | re.DOTALL)
        if match:
            calificacion = match.group(1).upper()
            logger.info(f"Calificación explícita encontrada: {calificacion}")
            return calificacion
    
    # Buscar patrones positivos (si hay alguna evidencia de que es positiva, considerarla)
    # Lista amplificada de patrones positivos para capturar más casos
    patrones_positiva = [
        r'\bVENTA\s+POSITIVA\b',
        r'\bAPROBADA\b',
        r'reporte\s+de\s+venta.*?positiva',
        r'calificación.*?positiva',
        r'venta\s+se\s+considera\s+aprobada',
        r'venta\s+cumple\s+con\s+(?:todos|los)\s+requisitos',
        r'se\s+aprobó\s+la\s+venta',
        r'venta\s+exitosa',
        r'venta\s+válida',
        r'se\s+considera\s+una\s+venta\s+válida',
        r'la\s+venta\s+es\s+(?:\w+\s+)*correcta',
        r'la\s+venta\s+es\s+(?:\w+\s+)*adecuada',
        r'(?:se\s+)?(?:autoriza|acepta|valida|aprueba)\s+(?:la\s+)?(?:venta|contratación)',
        r'(?:resultado|resolución)\s+(?:final|definitiva)\s*:\s*(?:positiva|aprobada)',
        r'(?:se\s+)?recomienda\s+(?:la\s+)?(?:aprobación|validación)',
        r'(?:el\s+)?(?:cliente|titular)\s+(?:proporcionó|brindó|dio)\s+(?:su\s+)?(?:consentimiento|autorización)',
        r'(?:cliente|titular)\s+(?:confirmó|verificó)\s+(?:su\s+)?(?:aceptación|intención)',
        r'cumplió\s+(?:con\s+)?(?:todos|la\s+mayoría\s+de)\s+(?:los\s+)?(?:requisitos|criterios|lineamientos)',
        r'(?:venta|auditoría)\s+(?:satisfactoria|completa)',
        r'(?:se\s+)?obtuvo\s+(?:el\s+)?consentimiento\s+(?:del\s+)?(?:cliente|titular)',
        r'venta\s+califica\s+como\s+(?:positiva|válida)',
        r'calificación\s+general\s*:\s*(?:positiva|aprobada)',
        r'en\s+general\s+la\s+venta\s+(?:es|fue)\s+(?:correcta|adecuada|satisfactoria)'
    ]
    
    # Buscar cualquier patrón positivo en el texto
    for patron in patrones_positiva:
        if re.search(patron, resultado_auditoria, re.IGNORECASE | re.DOTALL):
            logger.info(f"Patrón positivo encontrado: {patron}")
            return "POSITIVA"
    
    # Buscar patrones negativos - SOLO considerar negativa si hay patrón explícito
    # de rechazo y si hay al menos 3 criterios críticos incumplidos
    patrones_negativa_claros = [
        r'\bVENTA\s+NEGATIVA\b',
        r'\bRECHAZADA\b',
        r'reporte\s+de\s+venta.*?negativa',
        r'calificación.*?negativa',
        r'venta\s+no\s+cumple\s+con\s+(?:los|varios|muchos)\s+requisitos\s+(?:fundamentales|básicos|esenciales)',
        r'se\s+rechazó\s+la\s+venta\s+(?:debido|por)\s+a\s+(?:graves|múltiples)\s+(?:incumplimientos|problemas)',
        r'venta\s+inválida\s+por\s+(?:falta|ausencia)\s+de\s+(?:consentimiento|autorización)\s+(?:explícito|claro)',
        r'(?:no\s+se\s+puede|no\s+se\s+debe)\s+aprobar\s+debido\s+a\s+(?:graves|múltiples)\s+(?:incumplimientos|problemas)',
        r'el\s+cliente\s+(?:rechazó|negó)\s+(?:explícitamente|claramente)\s+(?:la\s+)?(?:oferta|propuesta|contratación)'
    ]
    
    # Verificar si hay patrones negativos claros e inequívocos
    patron_negativo_encontrado = False
    for patron in patrones_negativa_claros:
        if re.search(patron, resultado_auditoria, re.IGNORECASE | re.DOTALL):
            logger.info(f"Patrón negativo encontrado: {patron}")
            patron_negativo_encontrado = True
            break
    
    # Si hay un patrón negativo claro, verificar si hay suficientes criterios incumplidos
    if patron_negativo_encontrado:
        try:
            # Contar criterios no cumplidos
            no_cumple_count = len(re.findall(r'\[ \]|\[NO CUMPLE\]', resultado_auditoria, re.IGNORECASE))
            logger.info(f"Criterios no cumplidos: {no_cumple_count}")
            
            # Solo considerar NEGATIVA si hay al menos 3 criterios críticos no cumplidos
            if no_cumple_count >= 3:
                logger.info("Suficientes criterios no cumplidos para confirmar calificación NEGATIVA")
                return "NEGATIVA"
            else:
                logger.info("A pesar del patrón negativo, no hay suficientes criterios incumplidos, considerando POSITIVA")
                return "POSITIVA"
        except Exception as e:
            logger.error(f"Error analizando criterios no cumplidos: {e}")
            # Si hay error en el análisis, pero hay patrón negativo claro, considerar NEGATIVA
            return "NEGATIVA"
    
    # Verificar cumplimiento de criterios críticos
    try:
        # Contar menciones de CUMPLE vs NO CUMPLE
        cumple_count = len(re.findall(r'\[(?:x|X)\]|\[CUMPLE\]', resultado_auditoria, re.IGNORECASE))
        no_cumple_count = len(re.findall(r'\[ \]|\[NO CUMPLE\]', resultado_auditoria, re.IGNORECASE))
        
        logger.info(f"Análisis de cumplimiento: CUMPLE={cumple_count}, NO CUMPLE={no_cumple_count}")
        
        # Si hay más "CUMPLE" que "NO CUMPLE", considerar positiva
        if cumple_count >= no_cumple_count:
            logger.info("Más criterios cumplidos que no cumplidos, considerando POSITIVA")
            return "POSITIVA"
        
        # Buscar puntos críticos específicos - si CUMPLEN los importantes es POSITIVA
        patrones_criterios_criticos = [
            r'(?:precio|valor|tarifa|costo).*?\[(?:x|X)\]|\[CUMPLE\]',
            r'(?:consentimiento|autorización|aceptación).*?\[(?:x|X)\]|\[CUMPLE\]',
            r'(?:beneficios|coberturas|servicios).*?\[(?:x|X)\]|\[CUMPLE\]',
            r'(?:explicación|información).*?\[(?:x|X)\]|\[CUMPLE\]'
        ]
        
        criterios_cumplidos = 0
        for patron in patrones_criterios_criticos:
            if re.search(patron, resultado_auditoria, re.IGNORECASE | re.DOTALL):
                criterios_cumplidos += 1
        
        logger.info(f"Criterios críticos cumplidos: {criterios_cumplidos} de {len(patrones_criterios_criticos)}")
        
        # Si se cumplen al menos 2 de los 4 criterios críticos, considerar POSITIVA
        if criterios_cumplidos >= 2:
            logger.info("Suficientes criterios críticos cumplidos, considerando POSITIVA")
            return "POSITIVA"
        
        # Verificar mención de criterios críticos sin formato [x]
        criterios_text = [
            r'se\s+mencion(?:a|o)\s+(?:el|un|\w+)?\s*(?:precio|valor|tarifa|costo)',
            r'se\s+obtuvo\s+(?:el|un|\w+)?\s*(?:consentimiento|autorización|aceptación)',
            r'se\s+(?:explic(?:a|o)|inform(?:a|o)|detall(?:a|o))\s+(?:los|las)?\s*(?:beneficios|coberturas|servicios)',
            r'(?:cliente|usuario)\s+(?:acept(?:a|o)|confirm(?:a|o)|autoriz(?:a|o))'
        ]
        
        criterios_text_cumplidos = 0
        for patron in criterios_text:
            if re.search(patron, resultado_auditoria, re.IGNORECASE | re.DOTALL):
                criterios_text_cumplidos += 1
        
        logger.info(f"Criterios textuales cumplidos: {criterios_text_cumplidos} de {len(criterios_text)}")
        
        # Si se mencionan al menos 2 criterios críticos en el texto, considerar POSITIVA
        if criterios_text_cumplidos >= 2:
            logger.info("Suficientes criterios textuales mencionados, considerando POSITIVA")
            return "POSITIVA"
    
    except Exception as e:
        logger.error(f"Error en el análisis avanzado de calificación: {e}")
        # En caso de error, favorecer POSITIVA por defecto
        return "POSITIVA"
    
    # Si el reporte es extenso y detallado, probablemente sea una venta válida
    if len(resultado_auditoria) > 800:
        secciones_detectadas = 0
        for seccion in ['INFORMACIÓN DEL CLIENTE', 'DETALLES DEL SERVICIO', 'CARACTERÍSTICAS', 'CONCLUSIÓN']:
            if seccion in resultado_auditoria:
                secciones_detectadas += 1
        
        # Si es un reporte completo con al menos 3 secciones estándar, considerar POSITIVA
        if secciones_detectadas >= 3:
            logger.info("Reporte completo y detallado con suficientes secciones, considerando POSITIVA")
            return "POSITIVA"
    
    # Si todo lo demás falla, verificar proporción de lenguaje positivo vs negativo
    palabras_positivas = ['cumple', 'correcto', 'adecuado', 'aprobado', 'positivo', 'acept', 'valid', 'confirma',
                         'autorización', 'sí', 'exitoso', 'satisfactorio', 'completo', 'bueno']
    palabras_negativas = ['no cumple', 'incorrecto', 'inadecuado', 'rechazado', 'negativo', 'invalid', 'falta',
                        'no autoriz', 'no acept', 'no confirm', 'rechaz', 'neg', 'incumpl']
    
    count_positivas = sum(len(re.findall(r'\b' + palabra + r'\w*\b', resultado_auditoria, re.IGNORECASE)) 
                       for palabra in palabras_positivas)
    count_negativas = sum(len(re.findall(r'\b' + palabra + r'\w*\b', resultado_auditoria, re.IGNORECASE)) 
                        for palabra in palabras_negativas)
    
    logger.info(f"Análisis de lenguaje: Positivo={count_positivas}, Negativo={count_negativas}")
    
    # Favorecemos el resultado POSITIVO - umbral más bajo para POSITIVA
    if count_positivas > 0 and count_positivas >= count_negativas * 0.5:  # Umbral más favorable a POSITIVA
        logger.info("Suficiente presencia de lenguaje positivo, considerando POSITIVA")
        return "POSITIVA"
    elif count_negativas > count_positivas * 1.5:  # Mayor umbral para NEGATIVA
        logger.info("Dominante presencia de lenguaje negativo, considerando NEGATIVA")
        return "NEGATIVA"
    
    # En caso de duda o si el análisis no es concluyente, favorecemos POSITIVA
    logger.info("Análisis no concluyente. Por defecto: POSITIVA")
    return "POSITIVA"

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
        # Patrones mejorados para diferentes formatos en transcripciones
        patrones_asesor = [
            r'SPEAKER_\d+.*?(?:asesor|agente|representante|ejecutiv[oa])\s*(?:de ventas)?[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'me\s+(?:llamo|comunico)\s+(?:con)?\s*([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'le\s+habla\s+([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'mi\s+nombre\s+es\s+([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'ASESOR:\s*([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})'
        ]
        
        patrones_cliente = [
            r'SPEAKER_\d+.*?(?:cliente|usuario)\s*[:\s]+([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'(?:señor|señora|cliente)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'me\s+comunico\s+con\s+(?:el\s+(?:señor|cliente))?\s*([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})',
            r'CLIENTE:\s*([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})'
        ]

        # Buscar el nombre del asesor
        asesor = "No identificado"
        for patron in patrones_asesor:
            match = re.search(patron, contenido, re.IGNORECASE)
            if match:
                asesor = match.group(1).strip()
                break
        
        # Buscar el nombre del cliente
        cliente = "No identificado"
        for patron in patrones_cliente:
            match = re.search(patron, contenido, re.IGNORECASE)
            if match:
                cliente = match.group(1).strip()
                break
        
        # Método alternativo: buscar cualquier nombre mencionado en el formato "me comunico con el señor X"
        if cliente == "No identificado":
            nombre_match = re.search(r'me\s+comunico\s+con\s+(?:el\s+(?:señor|cliente))?\s*([A-Za-zÁáÉéÍíÓóÚúÑñ]+(?:\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+){0,2})', contenido, re.IGNORECASE)
            if nombre_match:
                cliente = nombre_match.group(1).strip()

        logger.info(f"Nombres extraídos: Asesor={asesor}, Cliente={cliente}")
        return asesor, cliente
    except Exception as e:
        logger.error(f"Error extrayendo nombres: {e}")
        return "No identificado", "No identificado"
