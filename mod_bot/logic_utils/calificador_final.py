#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging

# Configurar logging
logger = logging.getLogger('calificador_final')

def procesar_resultado_auditoria(resultado_auditoria, metadata=None, texto_transcripcion=None):
    """
    Función principal que procesa el resultado de la auditoría para asegurar una calificación correcta.
    Esta función está diseñada para ser llamada directamente desde diariza.py.
    
    Args:
        resultado_auditoria: Texto del resultado de la auditoría
        metadata: Metadatos adicionales (opcional)
        texto_transcripcion: Texto de la transcripción (opcional)
        
    Returns:
        tuple: (resultado_auditoria, calificacion, datos_estructurados_bd)
    """
    from enhanced_prompt import procesar_respuesta_modelo
    from l_process.detection import extraer_calificacion
    
    try:
        # Procesar la respuesta estructurada
        datos_estructurados = procesar_respuesta_modelo(resultado_auditoria)
        logger.info(f"Respuesta procesada y estructurada: {list(datos_estructurados.keys())}")

        # Crear copia para la base de datos
        datos_estructurados_bd = datos_estructurados.copy()
        
        # Añadir datos extraídos adicionales
        if metadata and 'datos_extraidos' in metadata:
            datos_estructurados_bd['datos_extraidos'] = metadata['datos_extraidos']
        
        # Agregar la transcripción a los metadatos para análisis adicional
        metadata_enriquecido = {} if metadata is None else metadata.copy()
        if texto_transcripcion:
            metadata_enriquecido['transcripcion'] = texto_transcripcion
        
        # Usar el nuevo sistema de determinación de calificación final
        calificacion = determinar_calificacion_final(datos_estructurados, 
                                                    resultado_auditoria, 
                                                    metadata_enriquecido)
        
        # Añadir calificación a los datos estructurados
        datos_estructurados_bd['calificacion'] = calificacion
        
        # Aplicar la calificación al texto del resultado
        calificacion_anterior = datos_estructurados.get('calificacion_final', None)
        resultado_modificado = aplicar_calificacion_a_texto(resultado_auditoria, 
                                                          calificacion, 
                                                          calificacion_anterior)
        
        logger.info(f"CALIFICACIÓN FINAL DETERMINADA: {calificacion}")
        return resultado_modificado, calificacion, datos_estructurados_bd
        
    except Exception as e:
        logger.error(f"Error en procesamiento avanzado: {e}")
        # Usar método simple de respaldo
        calificacion = extraer_calificacion(resultado_auditoria)
        datos_estructurados_bd = {'calificacion': calificacion}
        
        # Asegurar que el resultado tenga una calificación
        resultado_modificado = aplicar_calificacion_a_texto(resultado_auditoria, calificacion)
        
        return resultado_modificado, calificacion, datos_estructurados_bd

def determinar_calificacion_final(datos_estructurados, resultado_auditoria, metadata=None):
    """
    Determina la calificación final de una venta con una lógica que favorece resultados POSITIVOS.
    
    Args:
        datos_estructurados: Datos estructurados extraídos del resultado
        resultado_auditoria: Texto completo del resultado de la auditoría
        metadata: Metadatos adicionales (opcional)
        
    Returns:
        str: 'POSITIVA' o 'NEGATIVA'
    """
    # Log para depuración
    logger.info("Iniciando determinación de calificación final")
    
    # Priorizar la decisión POSITIVA si hay alguna evidencia
    calificacion = 'POSITIVA'  # Por defecto, asumir POSITIVA
    
    # Verificar si hay una decisión en los datos estructurados
    if 'decision' in datos_estructurados and datos_estructurados['decision']:
        # Si la decisión es explícitamente NEGATIVA, verificar si realmente debe ser NEGATIVA
        if datos_estructurados['decision'] == 'NEGATIVA':
            # Verificación adicional: verificar si hay evidencia para mantener NEGATIVA
            if ('puntos_criticos' in datos_estructurados and 
                datos_estructurados['puntos_criticos'] and
                sum(1 for v in datos_estructurados['puntos_criticos'].values() if not v) > 3):
                # Si hay más de 3 criterios críticos no cumplidos, mantener NEGATIVA
                calificacion = 'NEGATIVA'
                logger.info("Calificación NEGATIVA confirmada por criterios críticos no cumplidos")
            else:
                # De lo contrario, favorecer POSITIVA
                logger.info("Cambiando calificación de NEGATIVA a POSITIVA por política de favorecimiento")
        else:
            calificacion = datos_estructurados['decision']
    else:
        # Si no hay decisión en datos estructurados, usar extracción de texto
        from l_process.detection import extraer_calificacion
        calificacion_texto = extraer_calificacion(resultado_auditoria)
        
        # Si el texto dice NEGATIVA, aplicar las mismas verificaciones adicionales
        if calificacion_texto == 'NEGATIVA':
            logger.info("Verificando si realmente debe ser NEGATIVA")
            # Buscar patrones que indiquen rechazo explícito
            patrones_rechazo = [
                r'\bcliente\s+rechaz[aó]\b',
                r'\bno\s+(?:autoriz[aó]|acept[aó])\b',
                r'\bmanifest[aó]\s+(?:su\s+)?(?:rechazo|negativa)\b'
            ]
            
            rechazo_encontrado = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                    for patron in patrones_rechazo)
            
            if rechazo_encontrado:
                calificacion = 'NEGATIVA'
                logger.info("Calificación NEGATIVA confirmada por rechazo explícito")
            else:
                logger.info("Cambiando calificación de NEGATIVA a POSITIVA por falta de evidencia de rechazo")
                calificacion = 'POSITIVA'
        else:
            calificacion = calificacion_texto
    
    # Verificar si en la transcripción hay alguna evidencia clara de aceptación
    if calificacion == 'NEGATIVA' and metadata and 'transcripcion' in metadata:
        transcripcion = metadata['transcripcion']
        
        # Patrones de aceptación clara
        patrones_aceptacion = [
            r'\bs[ií]\s+(?:acepto|autorizo|confirmo)\b',
            r'\bestoy\s+de\s+acuerdo\b',
            r'\bme\s+parece\s+bien\b',
            r'\bperfecto\b'
        ]
        
        aceptacion_encontrada = any(re.search(patron, transcripcion, re.IGNORECASE) 
                                  for patron in patrones_aceptacion)
        
        if aceptacion_encontrada:
            logger.info("Cambiando calificación a POSITIVA debido a evidencia de aceptación en la transcripción")
            calificacion = 'POSITIVA'
    
    # Asegurar que la calificación final sea válida
    calificacion = calificacion.upper().strip()
    if calificacion not in ['POSITIVA', 'NEGATIVA']:
        logger.warning(f"Calificación inválida: {calificacion}, ajustando a POSITIVA")
        calificacion = 'POSITIVA'
    
    # Log para confirmar la calificación final
    logger.info(f"CALIFICACIÓN FINAL DETERMINADA: {calificacion}")
    
    return calificacion

def aplicar_calificacion_a_texto(resultado_auditoria, calificacion, calificacion_anterior=None):
    """
    Aplica la calificación final al texto del resultado.
    
    Args:
        resultado_auditoria: Texto del resultado
        calificacion: Calificación final a aplicar
        calificacion_anterior: Calificación anterior (si se conoce)
        
    Returns:
        str: Texto actualizado con la calificación correcta
    """
    # Asegurarse de que la calificación sea válida
    calificacion = calificacion.upper().strip()
    if calificacion not in ['POSITIVA', 'NEGATIVA']:
        calificacion = 'POSITIVA'
    
    # Si conocemos la calificación anterior, reemplazarla
    if calificacion_anterior:
        # Reemplazar diferentes formatos de calificación
        patrones_reemplazo = [
            (f"CALIFICACIÓN FINAL: [{calificacion_anterior}]", f"CALIFICACIÓN FINAL: [{calificacion}]"),
            (f"**CALIFICACIÓN FINAL: [{calificacion_anterior}]**", f"**CALIFICACIÓN FINAL: [{calificacion}]**"),
            (f"CALIFICACIÓN FINAL: {calificacion_anterior}", f"CALIFICACIÓN FINAL: {calificacion}"),
            (f"**CALIFICACIÓN FINAL: {calificacion_anterior}**", f"**CALIFICACIÓN FINAL: {calificacion}**")
        ]
        
        for patron_orig, patron_nuevo in patrones_reemplazo:
            resultado_auditoria = resultado_auditoria.replace(patron_orig, patron_nuevo)
    
    # Verificar si ya tiene alguna calificación al inicio
    tiene_calificacion = False
    patrones_calificacion = [
        r'CALIFICACIÓN FINAL:',
        r'\*\*CALIFICACIÓN FINAL:'
    ]
    
    for patron in patrones_calificacion:
        if re.search(patron, resultado_auditoria[:200], re.IGNORECASE):
            tiene_calificacion = True
            break
    
    # Si no tiene calificación al inicio, añadirla
    if not tiene_calificacion:
        resultado_auditoria = f"**CALIFICACIÓN FINAL: [{calificacion}]**\n\n{resultado_auditoria}"
    
    return resultado_auditoria