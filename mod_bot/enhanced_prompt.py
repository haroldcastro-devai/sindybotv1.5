"""
Módulo para generar prompts mejorados para el modelo de auditoría
Este módulo se encarga de crear prompts optimizados que proporcionan
toda la información necesaria para que el modelo realice una auditoría precisa.
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any

# Configurar logging
logging.basicConfig(
    filename='auditoria.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_prompt')

# Rutas a archivos de datos
TARIFAS_PATH = os.path.join(os.path.dirname(__file__), 'data/tarifas/')
GUIONES_PATH = os.path.join(os.path.dirname(__file__), 'data/guiones/')
EJEMPLOS_PATH = os.path.join(os.path.dirname(__file__), 'data/ejemplos_auditoria/')

# Asegurar que los directorios existan
os.makedirs(TARIFAS_PATH, exist_ok=True)
os.makedirs(GUIONES_PATH, exist_ok=True)
os.makedirs(EJEMPLOS_PATH, exist_ok=True)

# Palabras clave para detectar productos
PRODUCTO_KEYWORDS = {
    'practiseguro': ['practiseguro', 'practica', 'asistencia médica', 'teleconsulta', 'médico a domicilio'],
    'salvafactura': ['salvafactura', 'factura', 'servicios públicos', 'pago automático'],
    'plan_mascotas': ['plan mascotas', 'perro', 'gato', 'veterinario', 'mascota'],
    'seguro_vida': ['seguro de vida', 'beneficiario', 'fallecimiento', 'cobertura'],
    'seguro_auto': ['seguro auto', 'vehículo', 'soat', 'accidente vial', 'carro', 'moto'],
    'futuro_protegido': ['futuro protegido', 'enfermedades graves', 'protección', 'millones', 'diagnóstico', 'infarto'],
    'exequial': ['exequial', 'funerario', 'cremación', 'bóveda', 'traslado', 'cuerpo']
}

def cargar_tarifas(producto: str) -> Dict[str, Any]:
    """
    Carga las tarifas específicas para un producto.
    
    Args:
        producto (str): Nombre del producto (practiseguro, salvafactura, etc)
        
    Returns:
        Dict[str, Any]: Diccionario con la información de tarifas
    """
    try:
        tarifa_file = os.path.join(TARIFAS_PATH, f"{producto.lower().replace(' ', '_')}.json")
        if os.path.exists(tarifa_file):
            with open(tarifa_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Archivo de tarifas no encontrado para {producto}: {tarifa_file}")
            # Buscar archivo que contenga parte del nombre del producto
            for filename in os.listdir(TARIFAS_PATH):
                if producto.lower().replace(' ', '_') in filename.lower():
                    with open(os.path.join(TARIFAS_PATH, filename), 'r', encoding='utf-8') as f:
                        return json.load(f)
            return {}
    except Exception as e:
        logger.error(f"Error cargando tarifas para {producto}: {str(e)}")
        return {}

def cargar_guion(producto: str) -> str:
    """
    Carga el guión específico para un producto.
    
    Args:
        producto (str): Nombre del producto (practiseguro, salvafactura, etc)
        
    Returns:
        str: Texto del guión
    """
    try:
        guion_file = os.path.join(GUIONES_PATH, f"{producto.lower().replace(' ', '_')}.txt")
        if os.path.exists(guion_file):
            with open(guion_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Archivo de guión no encontrado para {producto}: {guion_file}")
            # Buscar archivo que contenga parte del nombre del producto
            for filename in os.listdir(GUIONES_PATH):
                if producto.lower().replace(' ', '_') in filename.lower():
                    with open(os.path.join(GUIONES_PATH, filename), 'r', encoding='utf-8') as f:
                        return f.read()
            return "No se encontró guión específico para este producto."
    except Exception as e:
        logger.error(f"Error cargando guión para {producto}: {str(e)}")
        return "Error al cargar el guión."

def cargar_ejemplos(producto: str, cantidad: int = 2) -> List[Dict[str, str]]:
    """
    Carga ejemplos de auditorías anteriores para un producto.
    
    Args:
        producto (str): Nombre del producto (practiseguro, salvafactura, etc)
        cantidad (int, optional): Número de ejemplos a cargar. Defaults to 2.
        
    Returns:
        List[Dict[str, str]]: Lista de ejemplos con formato {transcripcion, evaluacion}
    """
    try:
        ejemplos = []
        ejemplo_dir = os.path.join(EJEMPLOS_PATH, producto.lower().replace(' ', '_'))
        
        if not os.path.exists(ejemplo_dir):
            # Buscar directorio que contenga parte del nombre del producto
            for dirname in os.listdir(EJEMPLOS_PATH):
                if producto.lower().replace(' ', '_') in dirname.lower():
                    ejemplo_dir = os.path.join(EJEMPLOS_PATH, dirname)
                    break
        
        if os.path.exists(ejemplo_dir):
            archivos = os.listdir(ejemplo_dir)
            # Filtrar por archivos de ejemplo de buena calidad
            archivos_buenos = [a for a in archivos if 'bueno' in a.lower() or 'correcto' in a.lower()]
            archivos_a_usar = archivos_buenos if archivos_buenos else archivos
            
            for i, archivo in enumerate(archivos_a_usar[:cantidad]):
                with open(os.path.join(ejemplo_dir, archivo), 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    ejemplos.append(datos)
        
        return ejemplos
    except Exception as e:
        logger.error(f"Error cargando ejemplos para {producto}: {str(e)}")
        return []

def detectar_producto(transcripcion: str) -> str:
    """
    Detecta el tipo de producto mencionado en la transcripción.
    
    Args:
        transcripcion (str): Texto de la transcripción
        
    Returns:
        str: Nombre del producto detectado o 'desconocido'
    """
    transcripcion_lower = transcripcion.lower()
    
    # Contamos menciones de palabras clave por producto
    conteo = {producto: 0 for producto in PRODUCTO_KEYWORDS}
    
    for producto, keywords in PRODUCTO_KEYWORDS.items():
        for keyword in keywords:
            conteo[producto] += len(re.findall(r'\b' + re.escape(keyword) + r'\b', transcripcion_lower))
    
    # Determinamos el producto con más menciones
    producto_detectado = max(conteo.items(), key=lambda x: x[1])
    
    # Si no hay suficientes menciones, consideramos el producto como desconocido
    if producto_detectado[1] < 2:
        logger.warning(f"No se detectó un producto claro. Conteos: {conteo}")
        return 'desconocido'
    
    logger.info(f"Producto detectado: {producto_detectado[0]} con {producto_detectado[1]} menciones")
    return producto_detectado[0]

def extraer_segmentos_relevantes(transcripcion: str, producto: str) -> List[str]:
    """
    Extrae segmentos relevantes de la transcripción según el producto.
    
    Args:
        transcripcion (str): Texto de la transcripción
        producto (str): Nombre del producto detectado
        
    Returns:
        List[str]: Lista de segmentos relevantes
    """
    # Dividir por oraciones o párrafos
    segmentos = re.split(r'(?<=[.!?])\s+', transcripcion)
    
    # Palabras clave por tipo de segmento
    keywords = {
        'presentación': ['buenos días', 'buenas tardes', 'mi nombre es', 'le saluda', 'cómo está'],
        'producto': PRODUCTO_KEYWORDS.get(producto, []),
        'beneficios': ['beneficio', 'ventaja', 'incluye', 'obtiene', 'recibe', 'derecho a'],
        'precio': ['precio', 'valor', 'costo', 'mensual', 'pesos', 'tarifa', 'cobro'],
        'condiciones': ['condición', 'término', 'plazo', 'contrato', 'permanencia', 'cancelar'],
        'cierre': ['autoriza', 'acepta', 'adquiere', 'confirma', 'aprueba', 'de acuerdo']
    }
    
    segmentos_relevantes = []
    
    # Buscar segmentos que contienen palabras clave
    for segmento in segmentos:
        segmento = segmento.strip()
        if not segmento:
            continue
            
        for tipo, kws in keywords.items():
            for kw in kws:
                if kw.lower() in segmento.lower():
                    segmentos_relevantes.append({
                        'texto': segmento,
                        'tipo': tipo
                    })
                    break
    
    # Ordenar segmentos por el orden en que aparecen en la transcripción
    segmentos_ordenados = sorted(segmentos_relevantes, 
                               key=lambda x: transcripcion.lower().find(x['texto'].lower()))
    
    # Devolver lista formateada de segmentos
    return [f"[{s['tipo']}] {s['texto']}" for s in segmentos_ordenados]

def obtener_requisitos_producto(producto: str) -> Dict[str, Any]:
    """
    Obtiene los requisitos específicos para la auditoría según el producto.
    
    Args:
        producto (str): Nombre del producto detectado
        
    Returns:
        Dict[str, Any]: Diccionario con los requisitos específicos
    """
    requisitos_base = {
        'verificar_presentacion': True,
        'verificar_beneficios': True,
        'verificar_precio': True,
        'verificar_condiciones': True,
        'verificar_aceptacion': True,
        'elementos_especificos': []
    }
    
    requisitos_especificos = {
        'practiseguro': {
            'elementos_especificos': [
                'Mención de teleconsulta médica',
                'Mención de médico a domicilio',
                'Explicación de la cobertura familiar',
                'Mención del costo mensual exacto'
            ]
        },
        'salvafactura': {
            'elementos_especificos': [
                'Explicación de protección de facturas',
                'Mención de servicios cubiertos (agua, luz, gas)',
                'Mención del valor cubierto mensual',
                'Explicación del proceso de reclamación'
            ]
        },
        'plan_mascotas': {
            'elementos_especificos': [
                'Mención de cobertura veterinaria',
                'Explicación de vacunas incluidas',
                'Mención de descuentos en alimentos',
                'Aclaración sobre límite de mascotas cubiertas'
            ]
        },
        'seguro_vida': {
            'elementos_especificos': [
                'Mención de la cobertura en caso de fallecimiento',
                'Explicación sobre beneficiarios',
                'Mención del monto asegurado',
                'Aclaración sobre exclusiones principales'
            ]
        },
        'seguro_auto': {
            'elementos_especificos': [
                'Mención de cobertura por daños',
                'Explicación sobre asistencia en carretera',
                'Mención del deducible',
                'Aclaración sobre exclusiones principales'
            ]
        },
        'futuro_protegido': {
            'elementos_especificos': [
                'Mención del respaldo económico en caso de enfermedades graves',
                'Listado completo de enfermedades cubiertas',
                'Explicación de requisitos de edad',
                'Mención de periodos de carencia',
                'Mención del valor exacto de la prima'
            ]
        },
        'exequial': {
            'elementos_especificos': [
                'Explicación de cobertura de servicios funerarios',
                'Mención del alcance familiar',
                'Explicación de requisitos de edad',
                'Mención de periodos de carencia',
                'Mención del valor exacto de la prima'
            ]
        },
        'desconocido': {
            'elementos_especificos': [
                'Identificar el producto ofrecido',
                'Verificar si se mencionan los beneficios principales',
                'Verificar si se menciona el precio total',
                'Verificar si se obtiene consentimiento explícito'
            ]
        }
    }
    
    # Obtener requisitos específicos del producto o usar los genéricos si no existe
    requisitos_producto = requisitos_especificos.get(producto, requisitos_especificos['desconocido'])
    
    # Combinar requisitos base con específicos
    requisitos_combinados = {**requisitos_base, **requisitos_producto}
    
    return requisitos_combinados

def generar_prompt_mejorado(transcripcion: str, metadata: Dict[str, Any] = None) -> str:
    """
    Genera un prompt mejorado para el modelo de IA que realiza la auditoría.
    
    Args:
        transcripcion (str): Texto completo de la transcripción
        metadata (Dict[str, Any], optional): Metadatos adicionales. Defaults to None.
    
    Returns:
        str: Prompt optimizado para el modelo
    """
    if metadata is None:
        metadata = {}
    
    # Detectar el producto mencionado en la transcripción
    producto = metadata.get('producto', detectar_producto(transcripcion))
    
    # Cargar información específica del producto
    tarifas = cargar_tarifas(producto)
    guion = cargar_guion(producto)
    ejemplos = cargar_ejemplos(producto)
    
    # Extraer datos relevantes de los metadatos
    datos_extraidos = metadata.get('datos_extraidos', {})
    datos_personales = metadata.get('datos_personales', {})
    planes = metadata.get('planes', {})
    forma_pago = metadata.get('forma_pago', {})
    
    # Preparar información para incluir en el prompt
    info_cliente = "\n### Datos Detectados del Cliente:\n"
    if datos_personales:
        for clave, valor in datos_personales.items():
            if valor != "No identificado":
                info_cliente += f"* {clave.replace('_', ' ').title()}: {valor}\n"
    
    info_planes = "\n### Planes Detectados:\n"
    if planes:
        for nombre_plan, detalles in planes.items():
            info_planes += f"* {nombre_plan}:\n"
            for k, v in detalles.items():
                info_planes += f"  - {k.replace('_', ' ').title()}: {v}\n"
    
    info_pago = "\n### Forma de Pago Detectada:\n"
    if forma_pago:
        for k, v in forma_pago.items():
            info_pago += f"* {k.replace('_', ' ').title()}: {v}\n"
    
    # Construir el prompt mejorado para auditoría detallada
    prompt = f"""
# INSTRUCCIONES PARA AUDITORÍA DETALLADA DE VENTA TELEFÓNICA

## CONTEXTO Y OBJETIVO
Eres un auditor altamente especializado en evaluar y extraer información detallada de llamadas de venta de seguros. Tu misión es revisar minuciosamente la transcripción proporcionada y crear un reporte COMPLETO y ESTRUCTURADO que incluya TODA la información relevante mencionada durante la llamada.

## DIRECTRICES FUNDAMENTALES PARA LA EVALUACIÓN
1. Tu enfoque debe ser CONSTRUCTIVO y OBJETIVO, favoreciendo la APROBACIÓN de ventas cuando se cumplan los requisitos mínimos.
2. Solo califica una venta como NEGATIVA cuando hay evidencia CLARA Y CONTUNDENTE de incumplimientos graves.
3. Ante requisitos parcialmente cumplidos, considera la INTENCIÓN y el CONTEXTO global de la venta.
4. Busca ACTIVAMENTE evidencia de cumplimiento antes de concluir que algo no se cumplió.
5. Una buena experiencia del cliente con aceptación clara debe tener mayor peso que omisiones menores de información.

## PRODUCTO IDENTIFICADO: {producto.upper()}

## TRANSCRIPCIÓN COMPLETA DE LA LLAMADA:
{transcripcion}

## ESTRUCTURA REQUERIDA PARA TU REPORTE
Debes seguir EXACTAMENTE esta estructura:

# REPORTE DE VENTA
## CALIFICACIÓN FINAL: [POSITIVA/NEGATIVA]

## INFORMACIÓN DEL CLIENTE
* **Nombre:** [nombre completo]
* **Número de Identificación:** [documento]
* **Fecha de Nacimiento:** [si se menciona]
* **Dirección:** [dirección completa]
* **Correo Electrónico:** [si se menciona]
* **Teléfono:** [si se menciona]
* **Otros datos relevantes:** [cualquier otra información personal]

## DETALLES DEL SERVICIO
* **Aseguradora:** [nombre de la compañía]
* **Planes Contratados:** [listar todos los planes/pólizas]
* **Valor Individual de Cada Plan:** [monto específico de cada plan]
* **Valor Total Mensual:** [suma total a pagar]
* **Forma de Pago:** [método de pago y periodicidad]
* **Vigencia:** [duración del contrato y renovación]

## CARACTERÍSTICAS DE LOS PLANES
Para cada plan contratado:
* **[Nombre del Plan 1]:**
  * Coberturas específicas
  * Montos asegurados
  * Requisitos de elegibilidad
  * Períodos de carencia
  * Limitaciones y exclusiones

* **[Nombre del Plan 2 (si aplica)]:**
  * [Misma estructura]

## PUNTOS CRÍTICOS CUMPLIDOS
* [x/] Saludo e identificación del agente
* [x/] Explicación clara de los productos
* [x/] Validación de datos personales
* [x/] Verificación de requisitos de elegibilidad
* [x/] Explicación de valores y forma de pago
* [x/] Autorización de tratamiento de datos personales
* [x/] Aceptación explícita del cliente
* [x/] Confirmación final de entendimiento

## OBSERVACIONES
* Aspectos destacados de la venta
* Información adicional relevante
* Cualquier anomalía detectada (si aplica)

## CONCLUSIÓN
Basado en la evaluación completa, determina si la venta es POSITIVA o NEGATIVA. Una venta se considera POSITIVA cuando:
1. El cliente comprende claramente el producto principal
2. Se mencionan los costos principales y forma de pago
3. Hay una aceptación explícita del cliente
4. El cliente parece satisfecho con la explicación recibida

Si falta alguno de estos criterios FUNDAMENTALES, la venta se considera NEGATIVA.
"""

    # Agregar recordatorio sobre la extracción de información y FAVORECER resultados positivos
    prompt += """

## RECORDATORIO IMPORTANTE
Para cada sección, DEBES citar textualmente fragmentos de la transcripción como evidencia. Usa comillas para las citas directas.

RECUERDA: Tu reporte debe ser EXTREMADAMENTE DETALLADO y COMPLETO, similar a un reporte profesional de auditoría. Incluye TODOS los datos mencionados en la llamada, especialmente:
- Información personal completa del cliente
- Valores exactos de los planes
- Todas las coberturas mencionadas
- Todos los requisitos y limitaciones
- Períodos de carencia exactos

CRITERIOS DE CALIFICACIÓN:
Apruebes la venta (POSITIVA) cuando:
1. El cliente entiende el propósito principal del producto
2. Se mencionan los costos o valores principales
3. Hay una aceptación clara del cliente
4. No hay rechazo explícito por parte del cliente

Solo rechaces la venta (NEGATIVA) cuando hay EVIDENCIA CONTUNDENTE de que:
1. El cliente rechaza explícitamente la oferta
2. Hay omisiones GRAVES de información crítica
3. Se proporciona información CLARAMENTE engañosa

ANTE LA DUDA, CALIFICA COMO POSITIVA. Si encuentras que se cumplen los requisitos mínimos para una venta válida, califica como POSITIVA incluso si hay aspectos menores a mejorar.
"""
    
    # Registrar información sobre el prompt generado
    logger.info(f"Prompt mejorado generado para producto: {producto}, longitud: {len(prompt)} caracteres")
    
    return prompt

def procesar_respuesta_modelo(respuesta: str) -> Dict[str, Any]:
    """
    Procesa la respuesta del modelo para extraer datos estructurados.
    
    Args:
        respuesta (str): Respuesta completa del modelo
        
    Returns:
        Dict[str, Any]: Datos estructurados extraídos de la respuesta
    """
    resultado = {
        'calificacion_final': '',
        'informacion_cliente': {},
        'detalles_servicio': {},
        'caracteristicas_planes': {},
        'puntos_criticos': {},
        'observaciones': [],
        'conclusion': '',
        'decision': ''
    }
    
    # Extraer calificación final - buscar múltiples patrones para mayor robustez
    patrones_calificacion = [
        r'CALIFICACIÓN FINAL:\s*\[(POSITIVA|NEGATIVA)\]',
        r'CALIFICACIÓN FINAL:\s*(POSITIVA|NEGATIVA)',
        r'\bventa\s+(POSITIVA|NEGATIVA)\b',
        r'\b(APROBADA|RECHAZADA)\b'
    ]
    
    for patron in patrones_calificacion:
        match_calificacion = re.search(patron, respuesta, re.IGNORECASE)
        if match_calificacion:
            calificacion = match_calificacion.group(1).strip().upper()
            resultado['calificacion_final'] = calificacion
            # Mapear APROBADA a POSITIVA y RECHAZADA a NEGATIVA
            if calificacion == 'APROBADA':
                resultado['decision'] = 'POSITIVA'
            elif calificacion == 'RECHAZADA':
                resultado['decision'] = 'NEGATIVA'
            else:
                resultado['decision'] = calificacion
            break
    
    # Extraer información del cliente
    patron_cliente = r'INFORMACIÓN DEL CLIENTE(.*?)(?:##|DETALLES DEL SERVICIO)'
    match_cliente = re.search(patron_cliente, respuesta, re.DOTALL | re.IGNORECASE)
    if match_cliente:
        info_cliente_texto = match_cliente.group(1).strip()
        # Extraer cada línea de información del cliente
        lineas_cliente = info_cliente_texto.split('\n')
        for linea in lineas_cliente:
            linea = linea.strip()
            if linea and ('**' in linea or '*' in linea or '-' in linea):
                # Procesar línea con formato de lista
                linea_limpia = linea.replace('*', '').replace('-', '').strip()
                partes = re.split(r':\s*', linea_limpia, 1)
                if len(partes) == 2:
                    clave = partes[0].strip().replace('**', '')
                    valor = partes[1].strip().replace('**', '')
                    resultado['informacion_cliente'][clave] = valor
    
    # Extraer detalles del servicio
    patron_servicio = r'DETALLES DEL SERVICIO(.*?)(?:##|CARACTERÍSTICAS DE LOS PLANES)'
    match_servicio = re.search(patron_servicio, respuesta, re.DOTALL | re.IGNORECASE)
    if match_servicio:
        info_servicio_texto = match_servicio.group(1).strip()
        lineas_servicio = info_servicio_texto.split('\n')
        for linea in lineas_servicio:
            linea = linea.strip()
            if linea and ('**' in linea or '*' in linea or '-' in linea):
                linea_limpia = linea.replace('*', '').replace('-', '').strip()
                partes = re.split(r':\s*', linea_limpia, 1)
                if len(partes) == 2:
                    clave = partes[0].strip().replace('**', '')
                    valor = partes[1].strip().replace('**', '')
                    resultado['detalles_servicio'][clave] = valor
    
    # Extraer características de los planes
    patron_planes = r'CARACTERÍSTICAS DE LOS PLANES(.*?)(?:##|PUNTOS CRÍTICOS)'
    match_planes = re.search(patron_planes, respuesta, re.DOTALL | re.IGNORECASE)
    if match_planes:
        info_planes_texto = match_planes.group(1).strip()
        # Este es más complejo ya que puede tener múltiples planes con estructura anidada
        # Buscar los nombres de los planes
        planes = re.findall(r'\*\*\[(.*?)\]:\*\*', info_planes_texto)
        resultado['caracteristicas_planes'] = {}
        for plan in planes:
            # Buscar el bloque de texto para cada plan
            patron_plan = rf'\*\*\[{re.escape(plan)}\]:\*\*(.*?)(?:\*\*\[|PUNTOS CRÍTICOS|$)'
            match_plan = re.search(patron_plan, info_planes_texto, re.DOTALL)
            if match_plan:
                contenido_plan = match_plan.group(1).strip()
                # Extraer características como bullets
                caracteristicas = []
                lineas_plan = contenido_plan.split('\n')
                for linea in lineas_plan:
                    linea = linea.strip()
                    if linea and (linea.startswith('*') or linea.startswith('-')):
                        caracteristicas.append(linea.lstrip('*- ').strip())
                resultado['caracteristicas_planes'][plan] = caracteristicas
    
    # Extraer puntos críticos
    patron_criticos = r'PUNTOS CRÍTICOS CUMPLIDOS(.*?)(?:##|OBSERVACIONES)'
    match_criticos = re.search(patron_criticos, respuesta, re.DOTALL | re.IGNORECASE)
    if match_criticos:
        info_criticos_texto = match_criticos.group(1).strip()
        lineas_criticos = info_criticos_texto.split('\n')
        for linea in lineas_criticos:
            linea = linea.strip()
            if linea and ('*' in linea or '-' in linea):
                # Buscar el patrón [x] o [ ] para determinar si está cumplido
                cumplido = '[x]' in linea.lower()
                # Extraer el texto del punto crítico
                texto_punto = re.sub(r'\[x\]|\[ \]|\*|-', '', linea, flags=re.IGNORECASE).strip()
                resultado['puntos_criticos'][texto_punto] = cumplido
    
    # Extraer observaciones
    patron_observaciones = r'OBSERVACIONES(.*?)(?:##|CONCLUSIÓN)'
    match_observaciones = re.search(patron_observaciones, respuesta, re.DOTALL | re.IGNORECASE)
    if match_observaciones:
        info_obs_texto = match_observaciones.group(1).strip()
        lineas_obs = info_obs_texto.split('\n')
        for linea in lineas_obs:
            linea = linea.strip()
            if linea and (linea.startswith('*') or linea.startswith('-')):
                observacion = linea.lstrip('*- ').strip()
                resultado['observaciones'].append(observacion)
    
    # Extraer conclusión
    patron_conclusion = r'CONCLUSIÓN(.*?)(?:##|$)'
    match_conclusion = re.search(patron_conclusion, respuesta, re.DOTALL | re.IGNORECASE)
    if match_conclusion:
        conclusion_texto = match_conclusion.group(1).strip()
        resultado['conclusion'] = conclusion_texto
        
        # Determinar decisión final a partir de la conclusión si no se encontró antes
        if not resultado['decision']:
            if re.search(r'\bPOSITIVA\b', conclusion_texto, re.IGNORECASE):
                resultado['decision'] = 'POSITIVA'
            elif re.search(r'\bNEGATIVA\b', conclusion_texto, re.IGNORECASE):
                resultado['decision'] = 'NEGATIVA'
            elif re.search(r'\bAPROBADA\b', conclusion_texto, re.IGNORECASE):
                resultado['decision'] = 'POSITIVA'
            elif re.search(r'\bRECHAZADA\b', conclusion_texto, re.IGNORECASE):
                resultado['decision'] = 'NEGATIVA'
    
    # Si no se pudo determinar la decisión por otros medios, verificar si la mayoría de puntos críticos están cumplidos
    if not resultado['decision'] and resultado['puntos_criticos']:
        cumplidos = sum(1 for v in resultado['puntos_criticos'].values() if v)
        total = len(resultado['puntos_criticos'])
        if total > 0 and cumplidos / total >= 0.7:  # Al menos 70% cumplidos
            resultado['decision'] = 'POSITIVA'
        else:
            resultado['decision'] = 'NEGATIVA'
    
    # Si aún no hay decisión, revisar manualmente en el texto completo
    if not resultado['decision']:
        if re.search(r'\bPOSITIVA\b', respuesta, re.IGNORECASE) or re.search(r'\bAPROBADA\b', respuesta, re.IGNORECASE):
            resultado['decision'] = 'POSITIVA'
        else:
            resultado['decision'] = 'NEGATIVA'  # En caso de duda, considerar negativa
    
    return resultado
