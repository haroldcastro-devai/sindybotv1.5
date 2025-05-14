#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo para la generación de prompts mejorados con contexto enriquecido
para obtener auditorías más precisas del modelo de IA.
"""

import os
import json
from pathlib import Path
import re
from typing import Dict, List, Union, Optional, Any
from .logger_config import logger
from .text_processing import extraer_segmentos_relevantes, identificar_producto, extraer_palabras_clave

def cargar_ejemplos_aprendizaje(num_ejemplos=3):
    """
    Carga ejemplos de auditorías previas para mejorar el contexto.
    
    Args:
        num_ejemplos: Número de ejemplos a cargar
        
    Returns:
        list: Lista de ejemplos relevantes
    """
    try:
        # Ruta al directorio donde se almacenan las auditorías previas
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ejemplos_dir = base_dir.parent / "audio-text" / "Log_sales_audito"
        
        ejemplos = []
        if ejemplos_dir.exists():
            # Obtener los archivos más recientes
            archivos = list(ejemplos_dir.glob("*_auditoria*.txt"))
            archivos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Cargar los ejemplos más recientes
            for archivo in archivos[:num_ejemplos]:
                try:
                    with open(archivo, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        # Extraer solo la parte de calificación y justificación
                        match = re.search(r'(Calificación.*?)(?=\n\n|\Z)', contenido, re.DOTALL)
                        if match:
                            ejemplos.append(match.group(1))
                except Exception as e:
                    logger.warning(f"Error al cargar ejemplo {archivo}: {e}")
                    continue
        
        return ejemplos
    except Exception as e:
        logger.error(f"Error cargando ejemplos de aprendizaje: {e}")
        return []

def formatear_tarifas_detalladas(tarifas: Dict) -> str:
    """
    Formatea la información de tarifas para hacerla más comprensible para el modelo.
    
    Args:
        tarifas: Diccionario con la información de tarifas
        
    Returns:
        str: Texto formateado con detalles de tarifas
    """
    try:
        resultado = "INFORMACIÓN DETALLADA DE TARIFAS Y PLANES:\n\n"
        
        # Agrupar por tipo de plan para mejor organización
        planes_por_tipo = {}
        for plan_id, plan_info in tarifas.items():
            tipo_plan = plan_info.get('tipo_plan', 'Otros')
            if tipo_plan not in planes_por_tipo:
                planes_por_tipo[tipo_plan] = []
            planes_por_tipo[tipo_plan].append((plan_id, plan_info))
        
        # Formatear por tipo de plan
        for tipo_plan, planes in planes_por_tipo.items():
            resultado += f"== PLANES TIPO: {tipo_plan.upper()} ==\n"
            
            for plan_id, plan_info in planes:
                nombre = plan_info.get('nombre', 'Sin nombre')
                valor = plan_info.get('valor', 'No especificado')
                cobertura = plan_info.get('cobertura', 'No especificada')
                indemnizacion = plan_info.get('indemnizacion', 'No especificada')
                gaseras = plan_info.get('gaseras', 'Todas')
                edad_minima = plan_info.get('edad_minima', 'No especificada')
                edad_maxima = plan_info.get('edad_maxima', 'No especificada')
                
                resultado += f"\nPLAN: {nombre}\n"
                resultado += f"  ID: {plan_id}\n"
                resultado += f"  Valor: {valor}\n"
                resultado += f"  Cobertura: {cobertura}\n"
                resultado += f"  Indemnización: {indemnizacion}\n"
                resultado += f"  Gaseras aplicables: {gaseras}\n"
                resultado += f"  Edad mínima: {edad_minima}\n"
                resultado += f"  Edad máxima: {edad_maxima}\n"
                
                # Incluir información adicional específica si existe
                if 'mascota' in tipo_plan.lower():
                    resultado += f"  Tipo de mascota permitido: {plan_info.get('tipo_mascota', 'Perros y gatos')}\n"
                    resultado += f"  Edad máxima mascota: {plan_info.get('edad_max_mascota', '10 años')}\n"
                
                # Especificidades para cada tipo de plan
                if 'beneficios' in plan_info:
                    resultado += "  Beneficios específicos:\n"
                    for beneficio in plan_info['beneficios']:
                        resultado += f"    - {beneficio}\n"
                
                # Requisitos especiales
                if 'requisitos_especiales' in plan_info:
                    resultado += "  Requisitos especiales:\n"
                    for requisito in plan_info['requisitos_especiales']:
                        resultado += f"    - {requisito}\n"
                        
                # Excepciones
                excepciones = []
                if 'practiseguro' in nombre.lower() or 'salvafactura' in nombre.lower():
                    excepciones.append("No requiere aceptación explícita de términos y condiciones")
                    excepciones.append("No requiere aceptación explícita de habeas data")
                    excepciones.append("La permanencia en línea equivale a aceptación")
                
                if excepciones:
                    resultado += "  EXCEPCIONES IMPORTANTES:\n"
                    for excepcion in excepciones:
                        resultado += f"    - {excepcion}\n"
                
                resultado += "\n"
                
            resultado += "\n"
        
        return resultado
    except Exception as e:
        logger.error(f"Error formateando tarifas: {e}")
        return str(tarifas)

def formatear_guiones_detallados(guiones: Dict) -> str:
    """
    Formatea la información de guiones para hacerla más comprensible para el modelo.
    
    Args:
        guiones: Diccionario con la información de guiones
        
    Returns:
        str: Texto formateado con detalles de guiones
    """
    try:
        resultado = "GUIONES DETALLADOS POR TIPO DE PLAN:\n\n"
        
        for plan_id, guion_info in guiones.items():
            nombre = guion_info.get('nombre', 'Sin nombre')
            tipo_plan = guion_info.get('tipo_plan', 'General')
            
            resultado += f"== GUION PARA: {nombre.upper()} (TIPO: {tipo_plan}) ==\n\n"
            
            # Formatear las secciones del guion
            secciones = guion_info.get('secciones', {})
            for seccion_nombre, seccion_texto in secciones.items():
                resultado += f"SECCIÓN: {seccion_nombre.upper()}\n"
                resultado += f"{seccion_texto}\n\n"
            
            # Puntos críticos a evaluar
            puntos_criticos = guion_info.get('puntos_criticos', [])
            if puntos_criticos:
                resultado += "PUNTOS CRÍTICOS A EVALUAR:\n"
                for punto in puntos_criticos:
                    resultado += f"- {punto}\n"
                resultado += "\n"
            
            # Información adicional específica
            info_adicional = guion_info.get('info_adicional', {})
            if info_adicional:
                resultado += "INFORMACIÓN ADICIONAL IMPORTANTE:\n"
                for clave, valor in info_adicional.items():
                    resultado += f"- {clave}: {valor}\n"
                resultado += "\n"
            
            resultado += "\n"
        
        return resultado
    except Exception as e:
        logger.error(f"Error formateando guiones: {e}")
        return str(guiones)

def identificar_tipo_producto(transcripcion: str, tarifas: Dict) -> str:
    """
    Intenta identificar el tipo de producto/plan mencionado en la transcripción.
    
    Args:
        transcripcion: Texto de la transcripción
        tarifas: Información de tarifas para referencia
        
    Returns:
        str: Tipo de producto identificado o "No identificado"
    """
    try:
        tipos_productos = set()
        for _, info in tarifas.items():
            if 'tipo_plan' in info:
                tipos_productos.add(info['tipo_plan'].lower())
            if 'nombre' in info:
                tipos_productos.add(info['nombre'].lower())
        
        texto_lower = transcripcion.lower()
        
        # Palabras clave específicas por tipo de producto
        keywords = {
            'practiseguro': ['practiseguro', 'practi seguro', 'practi', 'básico'],
            'salvafactura': ['salvafactura', 'salva factura', 'factura protegida'],
            'futuro protegido': ['futuro protegido', 'futuro', 'protegido plus'],
            'mascota': ['mascota', 'perro', 'gato', 'veterinario', 'mascot'],
            'funerario': ['funerario', 'funeral', 'sepelio', 'exequias']
        }
        
        matches = {}
        for tipo, palabras in keywords.items():
            count = sum(1 for palabra in palabras if palabra in texto_lower)
            if count > 0:
                matches[tipo] = count
        
        # Si hay coincidencias, devolver el tipo con más menciones
        if matches:
            return max(matches.items(), key=lambda x: x[1])[0]
            
        # Si no hay coincidencias específicas, buscar en los tipos generales
        for tipo in tipos_productos:
            if tipo in texto_lower:
                return tipo
                
        return "No identificado"
    except Exception as e:
        logger.error(f"Error identificando tipo de producto: {e}")
        return "No identificado"

def analizar_requisitos_especificos(tipo_producto: str) -> Dict[str, Any]:
    """
    Determina los requisitos específicos a verificar según el tipo de producto.
    
    Args:
        tipo_producto: Tipo de producto identificado
        
    Returns:
        dict: Requisitos específicos para el tipo de producto
    """
    requisitos = {
        'verificar_edad': True,
        'verificar_aceptacion_explicita': True,
        'verificar_habeas_data': True,
        'verificar_terminos': True,
        'permanencia_linea': False,
        'verificar_otp': False,
        'verificar_mascota': False,
    }
    
    tipo_producto = tipo_producto.lower()
    
    # Ajustes para Practiseguro y Salvafactura
    if 'practi' in tipo_producto or 'salva' in tipo_producto or 'factura' in tipo_producto:
        requisitos['verificar_aceptacion_explicita'] = False
        requisitos['verificar_habeas_data'] = False
        requisitos['verificar_terminos'] = False
        requisitos['permanencia_linea'] = True
    
    # Ajustes para planes de mascotas
    if 'mascota' in tipo_producto:
        requisitos['verificar_mascota'] = True
    
    # Verificación OTP solo para GDO
    if 'gdo' in tipo_producto or 'gases de occidente' in tipo_producto:
        requisitos['verificar_otp'] = True
    
    return requisitos

def generar_prompt_mejorado(
    transcripcion: str, 
    tarifas: Dict, 
    guiones: Dict, 
    gasera: str,
    asesor: str = "No identificado", 
    cliente: str = "No identificado",
    evaluacion: Optional[Dict] = None
) -> str:
    """
    Genera un prompt mejorado con contexto enriquecido para el modelo.
    
    Args:
        transcripcion: Texto de la transcripción
        tarifas: Información de tarifas
        guiones: Información de guiones
        gasera: Nombre de la gasera
        asesor: Nombre del asesor (si se conoce)
        cliente: Nombre del cliente (si se conoce)
        evaluacion: Evaluación previa (si existe)
        
    Returns:
        str: Prompt mejorado para el modelo
    """
    try:
        # Identificar tipo de producto
        tipo_producto = identificar_tipo_producto(transcripcion, tarifas)
        
        # Determinar requisitos específicos
        requisitos = analizar_requisitos_especificos(tipo_producto)
        
        # Cargar ejemplos de aprendizaje
        ejemplos = cargar_ejemplos_aprendizaje(2)
        
        # Extraer segmentos relevantes de la transcripción
        segmentos = extraer_segmentos_relevantes(transcripcion)
        
        # Extraer palabras clave para mejorar el enfoque
        palabras_clave = extraer_palabras_clave(transcripcion)
        
        # Formatear tarifas y guiones para mejor comprensión
        tarifas_formateadas = formatear_tarifas_detalladas(tarifas)
        guiones_formateados = formatear_guiones_detallados(guiones)
        
        # Construir prompt mejorado con secciones claramente diferenciadas
        prompt = f"""
        ## TAREA: ANÁLISIS FORENSE DE LLAMADA DE VENTA

        ### CONTEXTO GENERAL
        Este análisis busca determinar si una venta telefónica cumple con todos los requisitos legales y procedimentales. **Extrema precisión** es requerida para evitar errores y tomar decisiones incorrectas que afecten al cliente o la empresa.

        ### INSTRUCCIONES CRÍTICAS DE PRECISIÓN

        1. **PROHIBICIÓN ABSOLUTA DE ALUCINACIONES**:
           - NUNCA inventes, asumas o inferas información no mencionada explícitamente en la llamada.
           - Todo dato, valor, fecha, nombre o información DEBE provenir EXACTAMENTE de la transcripción.
           - Si un dato no está mencionado, reporta "NO MENCIONADO" - NUNCA lo inventes.
           - NO hagas suposiciones basadas en otras llamadas o experiencias previas.
           - Ante cualquier duda o ambigüedad, indica "INFORMACIÓN AMBIGUA" para su revisión manual.

        2. **PRECISIÓN EN VALORES Y DATOS**:
           - Indica los valores monetarios, fechas, nombres y datos EXACTAMENTE como aparecen en la llamada.
           - NO redondees ni aproximes valores monetarios - usa el monto exacto mencionado.
           - Verifica que cada valor citado tenga su ubicación exacta (timestamp o marcador) en la transcripción.
           - En casos de discrepancias de valores, reporta TODAS las variantes mencionadas.

        3. **VALIDACIÓN OBLIGATORIA DE ELEMENTOS CRÍTICOS**:
           - Valida cada interacción entre asesor y cliente.
           - Valida explícitamente cada respuesta del cliente a preguntas críticas.
           - Si una respuesta es ambigua, indícalo explícitamente.
           - Reporta si se omitió algún elemento crítico según el guion.
           - Verifica que cada valor, tarifa, indemnización y cobertura mencionada coincida EXACTAMENTE con las tarifas establecidas.
           - Verifica que el guion usado siga los lineamientos establecidos para el plan específico.

        ### CRITERIOS ESPECÍFICOS PARA ESTE CASO
        
        **TIPO DE PRODUCTO IDENTIFICADO**: {tipo_producto}
        **GASERA**: {gasera}

        **Verificaciones requeridas para este tipo de producto**:
        """
        
        # Añadir requisitos específicos según tipo de producto
        if requisitos['verificar_edad']:
            prompt += "- Edad del cliente dentro de rangos permitidos\n"
        if requisitos['verificar_aceptacion_explicita']:
            prompt += "- Aceptación explícita del servicio\n"
        if requisitos['verificar_habeas_data']:
            prompt += "- Aceptación explícita de política de habeas data\n"
        if requisitos['verificar_terminos']:
            prompt += "- Aceptación explícita de términos y condiciones\n"
        if requisitos['permanencia_linea']:
            prompt += "- Permanencia en línea durante explicación del servicio\n"
        if requisitos['verificar_otp']:
            prompt += "- Verificación de envío y recepción de código OTP\n"
        if requisitos['verificar_mascota']:
            prompt += "- Verificación de tipo y edad de mascota\n"
        
        # Añadir instrucciones para calificación de venta
        prompt += """
        ### CRITERIOS DE CALIFICACIÓN DE VENTA

        **VENTA POSITIVA requiere TODOS estos elementos**:
        - Interacción bilateral verificable (diálogo entre asesor y cliente)
        - Usuario responsable del pago de la factura
        - Edad dentro de rango permitido para el plan
        - Datos personales confirmados por el cliente
        - Valores mencionados coinciden EXACTAMENTE con tarifas establecidas
        - Asesor sigue el guion establecido
        - Cada objeción del cliente resuelta satisfactoriamente
        """
        
        # Añadir criterios específicos según tipo de producto
        if requisitos['verificar_aceptacion_explicita']:
            prompt += "- Aceptación explícita final (\"sí\") del servicio\n"
        if requisitos['verificar_habeas_data']:
            prompt += "- Aceptación explícita de habeas data\n"
        if requisitos['verificar_terminos']:
            prompt += "- Aceptación explícita de términos y condiciones\n"
        if requisitos['permanencia_linea']:
            prompt += "- Permanencia en línea durante explicación equivale a aceptación\n"
        if requisitos['verificar_otp']:
            prompt += "- Confirmación de envío y recepción de código OTP\n"
        if requisitos['verificar_mascota']:
            prompt += "- Tipo de mascota (perro o gato) y edad dentro de límites permitidos\n"
        
        # Añadir criterios para venta negativa
        prompt += """
        **VENTA NEGATIVA si ocurre CUALQUIERA de estos elementos**:
        - Falta de diálogo bilateral (no hay respuestas del cliente)
        - Rechazo explícito del servicio
        - Cliente no es responsable del pago de factura
        - Información inconsistente con tarifas establecidas
        - Objeciones sin resolución satisfactoria
        - No hay aceptación final clara
        """
        
        # Añadir información detallada
        prompt += f"""
        ### INFORMACIÓN DETALLADA DE TARIFAS
        {tarifas_formateadas}
        
        ### INFORMACIÓN DETALLADA DE GUIONES
        {guiones_formateados}
        
        ### ANÁLISIS PRELIMINAR DE LA LLAMADA
        **Nombres detectados**:
        - Asesor: {asesor}
        - Cliente: {cliente}
        
        **Palabras clave identificadas**:
        {', '.join(palabras_clave)}
        
        **Segmentos relevantes detectados**:
        {segmentos}
        """
        
        # Si hay evaluación previa, añadirla
        if evaluacion:
            prompt += f"""
            ### EVALUACIÓN PRELIMINAR DEL SISTEMA
            - Puntuación: {evaluacion.get('puntuacion', 'No disponible')}
            - Calificación inicial: {evaluacion.get('calificacion', 'No disponible')}
            - Aceptaciones detectadas: {evaluacion.get('aceptacion', {}).get('num_aceptaciones', 0)}
            - Rechazos detectados: {evaluacion.get('aceptacion', {}).get('num_rechazos', 0)}
            """
        
        # Ejemplos de análisis anteriores para mejorar la consistencia
        if ejemplos:
            prompt += """
            ### EJEMPLOS DE ANÁLISIS ANTERIORES (para referencia de formato)
            """
            
            for i, ejemplo in enumerate(ejemplos, 1):
                prompt += f"""
                EJEMPLO {i}:
                {ejemplo}
                """
        
        # Instrucciones finales y formato de reporte
        prompt += f"""
        ### TRANSCRIPCIÓN COMPLETA A ANALIZAR
        ```
        {transcripcion}
        ```

        ### FORMATO DE RESPUESTA REQUERIDO
        Tu análisis debe seguir estrictamente este formato:

        ---
        # REPORTE DE AUDITORÍA DE VENTA
        
        ## CALIFICACIÓN FINAL: [POSITIVA/NEGATIVA]
        
        ## RESUMEN DE LA LLAMADA
        [Resumen conciso pero completo de la llamada]
        
        ## INFORMACIÓN CRÍTICA VALIDADA
        - Gasera: [Nombre exacto]
        - Producto/Plan: [Nombre exacto]
        - Valor mencionado: [Valor exacto] - [Coincide/No coincide] con tarifas establecidas
        - Indemnización: [Valor exacto] - [Coincide/No coincide] con tarifas establecidas
        - Cobertura: [Información exacta] - [Coincide/No coincide] con tarifas establecidas
        
        ## VERIFICACIÓN DE REQUISITOS
        - Diálogo bilateral: [Sí/No]
        - Cliente responsable de factura: [Sí/No/No mencionado]
        - Edad dentro de rangos permitidos: [Sí/No/No verificada]
        """
        
        # Añadir requisitos específicos según tipo de producto
        if requisitos['verificar_aceptacion_explicita']:
            prompt += "- Aceptación explícita final: [Sí/No/Ambigua]\n"
        if requisitos['verificar_habeas_data']:
            prompt += "- Aceptación de habeas data: [Sí/No/No mencionado]\n"
        if requisitos['verificar_terminos']:
            prompt += "- Aceptación de términos y condiciones: [Sí/No/No mencionado]\n"
        if requisitos['permanencia_linea']:
            prompt += "- Permanencia en línea durante explicación: [Sí/No]\n"
        if requisitos['verificar_otp']:
            prompt += "- Envío de código OTP: [Sí/No/No aplica]\n"
            prompt += "- Recepción de código OTP: [Sí/No/No aplica]\n"
        if requisitos['verificar_mascota']:
            prompt += "- Tipo de mascota: [Perro/Gato/Otro/No mencionado]\n"
            prompt += "- Edad de mascota: [Edad mencionada/No mencionada]\n"
        
        prompt += """
        ## OBJECIONES Y RESOLUCIONES
        [Lista cronológica de cada objeción del cliente y cómo fue resuelta]
        
        ## JUSTIFICACIÓN DE CALIFICACIÓN
        [Explicación detallada de por qué la venta es positiva o negativa, citando evidencia específica de la transcripción]
        
        ## OBSERVACIONES ADICIONALES
        [Cualquier información relevante adicional no contemplada en las secciones anteriores]
        ---
        
        RECUERDA: Tu análisis debe basarse ÚNICAMENTE en la información presente en la transcripción. NUNCA inventes, asumas o inferas información no mencionada explícitamente.
        """
        
        return prompt
    except Exception as e:
        logger.error(f"Error generando prompt mejorado: {e}")
        # Devolver un prompt básico en caso de error
        return f"""
        Analiza la siguiente transcripción de una llamada de venta:
        
        Transcripción:
        {transcripcion}
        
        Determina si la venta es POSITIVA o NEGATIVA basándote únicamente en la información presente en la transcripción.
        """
