"""
Módulo especializado para extraer datos clave de transcripciones de llamadas de venta de seguros.
Este módulo complementa el sistema de prompts para garantizar una correcta extracción de información.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extraer_datos_personales(transcripcion: str) -> Dict[str, str]:
    """
    Extrae información personal del cliente de la transcripción de la llamada.
    
    Args:
        transcripcion: Texto completo de la transcripción
        
    Returns:
        Dict[str, str]: Diccionario con los datos personales extraídos
    """
    datos_personales = {
        'nombre': "No identificado",
        'cedula': "No identificado",
        'fecha_nacimiento': "No identificado",
        'fecha_expedicion': "No identificado",
        'direccion': "No identificado",
        'correo_electronico': "No identificado",
        'telefono': "No identificado"
    }
    
    # Patrones para extraer nombre completo
    patrones_nombre = [
        r'(?:me\s+comunico\s+con\s+(?:el\s+)?(?:señor|señora)\s+)([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\?]|\s+[A-Za-z])',
        r'(?:nombre\s+completo\s+es\s+)([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\?]|\s+[A-Za-z])',
        r'(?:llama\s+)([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\?]|\s+[A-Za-z])'
    ]
    
    for patron in patrones_nombre:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            nombre = match.group(1).strip()
            if len(nombre.split()) >= 2:  # Al menos nombre y apellido
                datos_personales['nombre'] = nombre
                break
    
    # Patrón para cédula (documento de identidad)
    patrones_cedula = [
        r'(?:cédula|documento|identificación|cc)[\s:\.\-]+(\d[\d\s\.\-]+\d)',
        r'(?:número\s+de\s+)(?:cédula|documento|identificación)[\s:\.\-]+(\d[\d\s\.\-]+\d)'
    ]
    
    for patron in patrones_cedula:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            cedula = match.group(1).strip()
            # Limpiar formato (eliminar espacios, puntos, guiones)
            cedula = re.sub(r'[\s\.\-]', '', cedula)
            if len(cedula) >= 6:  # Longitud mínima razonable para un documento
                datos_personales['cedula'] = cedula
                break
    
    # Patrón para fecha de nacimiento
    patrones_nacimiento = [
        r'(?:fecha\s+de\s+nacimiento|nació\s+el)[\s:]+(\d{1,2}\s+de\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+\s+(?:de\s+)?\d{2,4})',
        r'(?:fecha\s+de\s+nacimiento|nació\s+el)[\s:]+(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})'
    ]
    
    for patron in patrones_nacimiento:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            datos_personales['fecha_nacimiento'] = match.group(1).strip()
            break
    
    # Patrón para fecha de expedición
    patrones_expedicion = [
        r'(?:fecha\s+de\s+expedición|expedida\s+el)[\s:]+(\d{1,2}\s+de\s+[A-Za-zÁáÉéÍíÓóÚúÑñ]+\s+(?:de\s+)?\d{2,4})',
        r'(?:fecha\s+de\s+expedición|expedida\s+el)[\s:]+(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})'
    ]
    
    for patron in patrones_expedicion:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            datos_personales['fecha_expedicion'] = match.group(1).strip()
            break
    
    # Patrón para dirección
    patrones_direccion = [
        r'(?:dirección|vive\s+en|ubicado\s+en|dirección\s+exacta)[\s:]+([A-Za-zÁáÉéÍíÓóÚúÑñ0-9\s\.,#\-]+)(?:[\.\?]|\s+[A-Za-z])',
        r'(?:barrio|urbanización|residencial)[\s:]+([A-Za-zÁáÉéÍíÓóÚúÑñ0-9\s\.,#\-]+)(?:[\.\?]|\s+[A-Za-z])'
    ]
    
    for patron in patrones_direccion:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            direccion = match.group(1).strip()
            if len(direccion.split()) >= 3:  # Al menos tres palabras para una dirección
                datos_personales['direccion'] = direccion
                break
    
    # Patrón para correo electrónico
    patron_correo = r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}'
    match = re.search(patron_correo, transcripcion)
    if match:
        datos_personales['correo_electronico'] = match.group(0)
    
    # Patrón para teléfono
    patron_telefono = r'(?:teléfono|celular|móvil|contacto)[\s:]+(\d[\d\s\.\-]+\d)'
    match = re.search(patron_telefono, transcripcion, re.IGNORECASE)
    if match:
        telefono = match.group(1).strip()
        # Limpiar formato (eliminar espacios, puntos, guiones)
        telefono = re.sub(r'[\s\.\-]', '', telefono)
        if len(telefono) >= 7:  # Longitud mínima para un número de teléfono
            datos_personales['telefono'] = telefono
    
    return datos_personales

def extraer_planes_seguros(transcripcion: str) -> Dict[str, Dict[str, Any]]:
    """
    Extrae información sobre los planes de seguros mencionados en la transcripción.
    
    Args:
        transcripcion: Texto completo de la transcripción
        
    Returns:
        Dict[str, Dict[str, Any]]: Diccionario con información de cada plan
    """
    planes = {}
    
    # Patrones para detectar nombres de planes
    patrones_nombres_planes = [
        r'(?:póliza|plan|seguro)\s+(?:de\s+)?([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\,]|\s+por)',
        r'(?:su\s+)(?:póliza|plan|seguro)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\,]|\s+y|\s+por)',
        r'plan\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:plus|premium)?'
    ]
    
    # Identificar nombres de planes
    nombres_planes = []
    for patron in patrones_nombres_planes:
        matches = re.finditer(patron, transcripcion, re.IGNORECASE)
        for match in matches:
            nombre_plan = match.group(1).strip()
            if len(nombre_plan) > 3 and nombre_plan.lower() not in ['su', 'este', 'el', 'un', 'mi']:
                nombres_planes.append(nombre_plan)
    
    # Patrones específicos para planes comunes
    if not nombres_planes:
        if re.search(r'futuro\s+protegido', transcripcion, re.IGNORECASE):
            nombres_planes.append('Futuro Protegido Plus')
        if re.search(r'protecci[oó]n\s+e[xz]equial', transcripcion, re.IGNORECASE):
            nombres_planes.append('Protección Exequial')
    
    # Buscar valores mensuales de primas
    patron_valor_plan = r'(?:valor|costo|precio|mensual|prima)\s+(?:de|es|por)\s+(?:de\s+)?[$\s]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+[\.,]\d+)(?:\s+(?:pesos|COP|USD|euros|MXN))?,?\s+(?:mensual|por\s+mes)?'
    valores_planes = re.finditer(patron_valor_plan, transcripcion, re.IGNORECASE)
    valores = []
    for match in valores_planes:
        valor = match.group(1).strip()
        # Limpiar formato (eliminar comas como separadores de miles)
        valor = valor.replace(',', '')
        valores.append(valor)
    
    # Buscar valores específicos con formato "$X por su póliza Y"
    patron_valor_especifico = r'(?:valor|costo|precio|mensual|prima|cargar|cobro)\s+(?:de|del|es|por|mensual)\s+(?:de\s+)?[$\s]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+[\.,]\d+)(?:\s+(?:pesos|COP|USD|euros|MXN))?(?:[\s,]+(?:por|para|de|en)\s+(?:su\s+)?(?:póliza|plan|seguro)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+))'
    valores_especificos = re.finditer(patron_valor_especifico, transcripcion, re.IGNORECASE)
    for match in valores_especificos:
        valor = match.group(1).strip().replace(',', '')
        plan = match.group(2).strip()
        if plan.lower() not in ['su', 'este', 'el', 'un', 'mi']:
            if plan not in planes:
                planes[plan] = {'valor_mensual': valor}
            else:
                planes[plan]['valor_mensual'] = valor
    
    # Buscar montos de indemnización/cobertura
    patron_indemnizacion = r'(?:respaldo|indemnización|cobertura|beneficio)\s+(?:económico|por)\s+(?:de\s+)?[$\s]*(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+)(?:\s+(?:millones|mil|m))'
    indemnizaciones = re.finditer(patron_indemnizacion, transcripcion, re.IGNORECASE)
    for match in indemnizaciones:
        valor = match.group(1).strip()
        # Verificar si menciona "millones"
        if 'millones' in match.group(0).lower():
            valor = f"{valor} millones"
        # Asignar al primer plan si no tenemos asociación específica
        if nombres_planes and nombres_planes[0] not in planes:
            planes[nombres_planes[0]] = {'indemnizacion': valor}
        elif nombres_planes and 'indemnizacion' not in planes[nombres_planes[0]]:
            planes[nombres_planes[0]]['indemnizacion'] = valor
    
    # Asignar valores a planes sin información específica
    for i, nombre in enumerate(nombres_planes):
        if nombre not in planes:
            planes[nombre] = {}
        
        # Asignar valores mensuales si están disponibles y no asignados
        if 'valor_mensual' not in planes[nombre] and i < len(valores):
            planes[nombre]['valor_mensual'] = valores[i]
    
    # Si no se detectaron planes pero hay valores, crear un plan genérico
    if not planes and valores:
        planes['Seguro'] = {'valor_mensual': valores[0]}
        if len(valores) > 1:
            planes['Seguro']['indemnizacion'] = valores[1]
    
    # Extraer coberturas y beneficios para cada plan
    for nombre_plan in planes.keys():
        # Buscar texto que mencione el plan seguido de beneficios
        patron_beneficios = rf'(?:{re.escape(nombre_plan)}|seguro)[\s\,\.]+(?:[A-Za-zÁáÉéÍíÓóÚúÑñ\s\,\.]+(?:cubre|incluye|beneficio|cobertura)[A-Za-zÁáÉéÍíÓóÚúÑñ\s\,\.]+)'
        match = re.search(patron_beneficios, transcripcion, re.IGNORECASE)
        if match:
            planes[nombre_plan]['beneficios'] = match.group(0).strip()
        
        # Buscar requisitos de edad
        patron_edad = r'(?:edad|requisito)[\s\:]+(?:[A-Za-zÁáÉéÍíÓóÚúÑñ\s\,\.]+(?:año|edad|menor)[\s\:]+(\d{1,2}))'
        match = re.search(patron_edad, transcripcion, re.IGNORECASE)
        if match:
            planes[nombre_plan]['requisito_edad'] = match.group(1).strip()
        
        # Buscar periodos de carencia
        patron_carencia = r'(?:periodo|carencia|cubre|cubierto)[\s\:]+(?:a\s+partir\s+(?:del|de)\s+(?:día\s+)?(\d+))'
        match = re.search(patron_carencia, transcripcion, re.IGNORECASE)
        if match:
            planes[nombre_plan]['periodo_carencia'] = match.group(1).strip()
    
    return planes

def extraer_forma_pago(transcripcion: str) -> Dict[str, str]:
    """
    Extrae información sobre la forma de pago mencionada en la transcripción.
    
    Args:
        transcripcion: Texto completo de la transcripción
        
    Returns:
        Dict[str, str]: Información de forma de pago
    """
    forma_pago = {
        'metodo': "No especificado",
        'periodicidad': "No especificado",
        'autorizacion': False
    }
    
    # Patrón para método de pago
    patrones_metodo = [
        r'(?:pago|cobro|cargo)\s+(?:en|a través de|mediante|por medio de|con|factura(?:\s+de)?)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\,]|\s+[A-Za-z])',
        r'(?:débito automático|factura|recibo)\s+(?:de|del)\s+([A-Za-zÁáÉéÍíÓóÚúÑñ\s]+)(?:[\.\,]|\s+[A-Za-z])'
    ]
    
    for patron in patrones_metodo:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            metodo = match.group(1).strip().lower()
            # Filtrar métodos válidos
            if any(palabra in metodo for palabra in ['factura', 'gas', 'luz', 'agua', 'energía', 'bancario', 'tarjeta', 'débito', 'crédito']):
                forma_pago['metodo'] = metodo
                break
    
    # Patrón para periodicidad
    patrones_periodicidad = [
        r'(?:pago|cobro|cargo)\s+(?:mensual|bimestral|trimestral|anual)',
        r'(?:cada|por)\s+(?:mes|bimestre|trimestre|año)'
    ]
    
    for patron in patrones_periodicidad:
        match = re.search(patron, transcripcion, re.IGNORECASE)
        if match:
            periodicidad = match.group(0).strip().lower()
            if 'mensual' in periodicidad or 'mes' in periodicidad:
                forma_pago['periodicidad'] = 'Mensual'
            elif 'bimestral' in periodicidad or 'bimestre' in periodicidad:
                forma_pago['periodicidad'] = 'Bimestral'
            elif 'trimestral' in periodicidad or 'trimestre' in periodicidad:
                forma_pago['periodicidad'] = 'Trimestral'
            elif 'anual' in periodicidad or 'año' in periodicidad:
                forma_pago['periodicidad'] = 'Anual'
            break
    
    # Si no se especifica, asumir mensual (lo más común)
    if forma_pago['periodicidad'] == "No especificado":
        forma_pago['periodicidad'] = 'Mensual'
    
    # Verificar autorización
    patrones_autorizacion = [
        r'(?:autoriza|acepta)\s+(?:el|los)?\s+(?:cargo|cobro|pago)',
        r'(?:está\s+de\s+acuerdo|acepta)\s+(?:con)?\s+(?:el|los)?\s+(?:cargo|cobro|pago)'
    ]
    
    for patron in patrones_autorizacion:
        if re.search(patron, transcripcion, re.IGNORECASE):
            forma_pago['autorizacion'] = True
            break
    
    return forma_pago

def procesar_transcripcion(transcripcion: str) -> Dict[str, Any]:
    """
    Procesa la transcripción completa para extraer toda la información relevante.
    
    Args:
        transcripcion: Texto completo de la transcripción
        
    Returns:
        Dict[str, Any]: Información estructurada extraída de la transcripción
    """
    resultado = {}
    
    # Extraer datos personales
    try:
        datos_personales = extraer_datos_personales(transcripcion)
        resultado['datos_personales'] = datos_personales
    except Exception as e:
        logger.error(f"Error extrayendo datos personales: {e}")
        resultado['datos_personales'] = {}
    
    # Extraer información de planes
    try:
        planes = extraer_planes_seguros(transcripcion)
        resultado['planes'] = planes
    except Exception as e:
        logger.error(f"Error extrayendo información de planes: {e}")
        resultado['planes'] = {}
    
    # Extraer forma de pago
    try:
        forma_pago = extraer_forma_pago(transcripcion)
        resultado['forma_pago'] = forma_pago
    except Exception as e:
        logger.error(f"Error extrayendo forma de pago: {e}")
        resultado['forma_pago'] = {}
    
    # Extraer aceptación explícita
    try:
        # Patrones para detectar aceptación explícita
        patrones_aceptacion = [
            r'\b(?:s[ií]|claro|por\s+supuesto|correcto|exacto|est[áa]\s+bien)\b',
            r'\b(?:acepto|autorizo|confirmo|apruebo)\b',
            r'(?:est[áa]\s+de\s+acuerdo|aprueba)\b'
        ]
        
        aceptaciones = []
        for patron in patrones_aceptacion:
            matches = list(re.finditer(patron, transcripcion, re.IGNORECASE))
            aceptaciones.extend(matches)
        
        # Ordenar por posición en el texto
        aceptaciones.sort(key=lambda x: x.start())
        
        # Extraer las últimas 3 aceptaciones (las más importantes para la conclusión)
        ultimas_aceptaciones = [
            {
                'texto': match.group(0),
                'contexto': transcripcion[max(0, match.start()-30):min(len(transcripcion), match.end()+30)]
            } 
            for match in aceptaciones[-3:]
        ]
        
        resultado['aceptaciones'] = ultimas_aceptaciones
        resultado['consentimiento_explicito'] = len(ultimas_aceptaciones) > 0
    except Exception as e:
        logger.error(f"Error extrayendo aceptaciones: {e}")
        resultado['aceptaciones'] = []
        resultado['consentimiento_explicito'] = False
    
    # Extraer vigencia
    try:
        # Patrones para detectar vigencia
        patron_vigencia = r'(?:vigencia|duración|período|plazo|cobertura)\s+(?:de|es|por)\s+(?:de\s+)?(\d+)\s+(?:meses|años|días)'
        match = re.search(patron_vigencia, transcripcion, re.IGNORECASE)
        if match:
            duracion = match.group(1)
            unidad = re.search(r'(meses|años|días)', match.group(0), re.IGNORECASE).group(1).lower()
            resultado['vigencia'] = f"{duracion} {unidad}"
        else:
            # Por defecto muchos seguros son anuales
            resultado['vigencia'] = "12 meses"
    except Exception as e:
        logger.error(f"Error extrayendo vigencia: {e}")
        resultado['vigencia'] = "No especificada"
    
    return resultado
