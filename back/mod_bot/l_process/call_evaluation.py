#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gc
import json
import ollama
from pathlib import Path
from typing import Dict, List, Union, Optional

# Importar módulos del paquete
from .logger_config import logger
from .detection import detectar_aceptacion, extract_names
from .text_processing import pre_process_data
from .file_utils import validate_call_content

# Importar módulos externos
from data_updateBD import guardar_resultado_auditoria, actualizar_estado_venta, insertar_datos_aprendizaje, obtener_datos_aprendizaje
from logic_utils.get_tags import obtener_gasera_seguro

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

        # Evaluación cuantitativa
        evaluacion = evaluar_llamada(contenido, tarifas, guiones)

        # Construir prompt
        prompt = f"""

        **PRINCIPIOS BÁSICOS:**

        1. **Precisión extrema:**
        - Debes ser **EXTREMADAMENTE PRECISO** con valores monetarios, fechas, timestamps y contextos mencionados en la llamada.
        - **NO** puedes inventar, inferir, aproximar o modificar valores, información o diálogos no mencionados explícitamente.
        - Si un valor no está mencionado, debes indicar **"NO MENCIONADO"**.
        - A cada punto crítico debes añadir el timestamp correspondiente.
        - **NO** puedes omitir, resumir o alterar información relevante.
        - **NO** puedes añadir información no mencionada en la llamada.
        - **NO** puedes modificar el contenido original de la llamada.
        - **NO** puedes inventar diálogos o interacciones no presentes en la llamada.
        - debes comparar los  valores, tarifas, indemnizaciones y coberturas mencionadas con las tarifas establecidas.
        - debes comparar el guion usado por el aseror con los guiones establecidos segun el plan.
        - debes validar e identificar cada objeción del usuario y la respuesta correspondiente del asesor.
        - debes validar e indentificar la resolución final de cada objeción y la aceptacion final al seguro o servicio ofrecido. 

        2. **Validación y evaluación obligatoria:**
        - Detectar y validar que el asesor se presente y salude correctamente.
        - Detectar y validar TODAS las interacciones entre asesor y usuario durante la llamada.
        - Detectar, validar y evaluar la respuesta del usuario sobre la responsabilidad del pago de la factura.
        - Detectar, validar y evaluar la coherencia entre la edad declarada y la fecha de nacimiento.
        - Detectar, validar y evaluar la confirmación de datos personales del usuario.
        - Detectar, validar y evaluar la aceptación de términos y condiciones del plan.
        - Detectar, validar y evaluar la aceptación del habeas data.
        - Detectar, validar y evaluar la información proporcionada por el asesor sobre montos, tarifas, indemnizaciones, coberturas y servicios.
        - Detectar el valor del plan, nombre del plan, aseguradora, gasera, cobertura e indemnización.
        - Detectar, validar y evaluar el tipo y edad de la mascota (solo para planes de mascotas).
        - Detectar, validar y evaluar el cumplimiento de los puntos críticos del guion.
        - Detectar, validar y evaluar cada objeción del usuario y la respuesta correspondiente del asesor.
        - Detectar, validar y evaluar la resolución final de cada objeción.
        - Detectar y validar explícitamente la aceptación final del usuario después de resolver todas las objeciones realizadas por el usuario.
        - Detectar y validar la aceptación explícita ("sí") del cobro en la factura al cierre de la venta.
        - Detectar y validar el envio de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")

        3. **Puntos Críticos:**
        - Saludo: Cordial y profesional
        - Explicación del servicio: Clara y detallada
        - Validación de datos: Precisa y completa
        - Habeas data: Clara y detallada
        - Términos y condiciones: Claros y detallados
        - Cobro del plan: Claro y detallado
        - Manejo de objeciones: Identificar, responder y resolver
        - Confirmación post-objeciones: Validar aceptación después de resolver cada objeción
        - validación de envio de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - validación de recepción de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - tipo de mascota y edad de la mascota (solo para planes de mascotas)
        - Aceptación final: Confirmar "sí" explícito al cobro del servicio
        - Validación de interacciones: Asegurar registro de diálogo bilateral
        - Cierre de la llamada: Amable y respetuoso

        4. **ANÁLISIS DE OBJECIONES:**
        Para cada objeción detectada, registrar:
        - Timestamp de la objeción
        - Contenido de la objeción
        - Respuesta del asesor
        - Reacción del usuario
        - Resolución final a las objeciones de forma coherente (aceptada/no aceptada)

        **CLASIFICACIÓN DE VENTA:**

        **VENTA POSITIVA requiere:**
        - Registro completo de interacciones asesor-usuario (diálogo bilateral obligatorio)
        - Presentación y saludo del asesor
        - Usuario responsable del pago de la factura
        - Usuario cumple requisitos de edad mínima y máxima según el plan
        - Edad declarada coincide con fecha de nacimiento
        - Usuario confirma datos personales
        - Usuario acepta explícitamente ("sí") términos y condiciones (verificar ***EXCEPCIONES***)
        - Usuario acepta explícitamente ("sí") habeas data  (verificar ***EXCEPCIONES***)
        - Montos, tarifas, indemnizaciones, coberturas y servicios exactos según tarifas establecidas
        - Tipo de mascota es "perro o gato" (solo para planes de mascotas)
        - Edad de mascota cumple condiciones del plan (solo para planes de mascotas)
        - Asesor sigue puntos críticos del guion
        - Todas las objeciones deben estar documentadas con:
        * Objeción inicial del usuario
        * Respuesta del asesor
        * Resolución/aceptación del usuario
        - Aceptación explícita final con "sí" después de resolver todas las objeciones
        - Usuario acepta explícitamente ("sí") cobro del plan en factura
        - CONFIRMACIÓN de envio de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - CONFIRMACIÓN de recepción de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        * los valores indicados por el asesor coinciden con tarifas establecidas
        * el asesor sigue el guion establecido

        **VENTA NEGATIVA cuando:**
        - No hay registro de respuestas del usuario (diálogo unilateral)
        - Asesor usa lenguaje inapropiado
        - Cliente rechaza explícitamente durante la llamada
        - Información incompleta o incorrecta de tarifas establecidas
        - Usuario no es responsable del pago de factura
        - Hay rechazo del servicio
        - No se menciona valor específico del plan
        - No hay confirmación clara con "sí"
        - Cliente solicita más tiempo
        - edad de mascota es superior a la permitida según tarifas establecidas (solo para planes de mascotas)
        - tipo de mascota es diferente a perro o gato (solo para planes de mascotas)
        - Quedan dudas sin resolver
        - Objeciones sin resolución documentada
        - No hay aceptación clara de habeas data
        - No hay aceptación explícita final con "sí" después de resolver objeciones
        - Usuario no acepta cobro del plan al final
        - ACESOR NO SE ENVIA codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - USUARIO NO RECIBE codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - Valor indicado no coincide con tarifas establecidas

        **EXCEPCIONES:**
        Para planes practiseguro y salvafactura:
        - No requieren aceptación explícita de términos
        - No requieren aceptación explícita de habeas data
        - Solo requieren permanencia en llamada
        - La permanencia en línea equivale a aceptación
        - los codigos otp enviados por mensaje de texto o whatsapp solo aplican para gasera GDO "GASES DE OCCIDENTE"

        **CONTEXTO Y DATOS:**
        - nombre de la gasera: {gasera}
        - guiones establecidos: {guiones_formatted}
        - tarifas establecidas : {tarifas_formatted}

        **DETALLES DE LA LLAMADA:**
        - Transcripción a analizar: {contenido}
        - Nombres detectados:
        - Asesor: {asesor}
        - Cliente: {cliente}

        **REPORTE REQUERIDO:**
        Título obligatorio: "**REPORTE DE VENTA**"

        Contenido:
        - Calificación final: VENTA [{evaluacion['calificacion']}]
        - Resumen de la llamada e interacción asesor-cliente (usar solo información proporcionada)
        - Valores y montos mencionados (no usar valores aproximados)
        - nombre de la gasera
        - Registro cronológico de objeciones y resoluciones
        - Aceptaciones y rechazos detectados
        - Respuestas del cliente sobre datos personales, términos, habeas data, cobro y aceptación
        - Cumplimiento de puntos críticos
        - envio de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - recepción de codigo OTP por medio de mensaje de texto sms o wahtsapp al usuario  (SOLO PARA PARA GASERA GDO "GASES DE OCCIDENTE")
        - tipo de mascota y edad de la mascota (solo para planes de mascotas)
        - Validación específica de aceptación final post-objeciones
        - Confirmación explícita de permanencia en línea para planes practiseguro/salvafactura
        - Registro de interacciones bilaterales asesor-usuario
        - Verificación de "sí" explícito final al cobro
        - Justificación de calificación
        - Observaciones adicionales

        **Precisiones finales:**
        - Usar solo información proporcionada
        - Limitar interpretación de información
        - Ser preciso con valores y timestamps
        - Mantener reporte claro y estructurado
        - Debe ser presicion  con las **EXCEPCIONES:** las cuales aplican solo para planes practiseguro y salvafactura.
        - Documentar TODAS las interacciones asesor-usuario
        - Validar resolución de cada objeción individualmente
        - Confirmar aceptación final explícita post-objeciones
        - Aplicar correctamente excepciones para planes practiseguro/salvafactura
        - Asegurar registro de diálogo bilateral completo
        - Consultar contexto en tarifas establecidas y guiones establecidos si hay dudas
       
        """
        # Procesamiento con OLLAMA
        max_intentos = 3
        resultado = None

        for intento in range(max_intentos):
            try:
                model = ollama.Client()
                response = model.generate(model="qwen2.5:14b-instruct-q6_K", prompt=prompt)
                resultado = response['response']
                break
            except Exception as e:
                logger.error(f"Intento {intento + 1} fallido: {e}")
                if intento == max_intentos - 1:
                    raise Exception(f"Error después de {max_intentos} intentos")
                continue

        if not resultado:
            raise Exception("No se pudo obtener respuesta del modelo")

        # Extraer información del archivo
        partes_nombre = nombre_archivo.split("_")
        numero_contrato = partes_nombre[1] if len(partes_nombre) > 1 else "DESCONOCIDO"

        # Extraer calificación
        from .detection import extraer_calificacion
        calificacion = extraer_calificacion(resultado)

        # Actualizar estado de venta
        actualizar_estado_venta(numero_contrato, calificacion)

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
        del contenido, prompt
        gc.collect()

        return resultado

    except Exception as e:
        logger.error(f"Error en process_call: {e}")
        return f"ERROR: {str(e)}"