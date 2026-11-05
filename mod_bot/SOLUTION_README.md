# Solución para Mejorar la Precisión de las Auditorías de Ventas

> **Documento histórico (era Ollama / qwen).** La auditoría actual usa **Google Gemini** vía `l_process/llm_client.py`. Ver [IA-STT-ARQUITECTURA.md](../Docs--Readme/IA-STT-ARQUITECTURA.md).

Este documento explica la solución implementada para resolver el problema de alucinaciones en el modelo de inteligencia artificial que realiza las auditorías de ventas telefónicas.

## Problema Identificado

Se identificó que el modelo de IA "mixtral:8x22b-instruct-v0.1-q4_K_M" (ahora "qwen2.5:14b-instruct-q6_K") no estaba recibiendo de forma correcta toda la información necesaria para generar auditorías precisas, lo que resultaba en:

1. Información incompleta del texto del audio de la venta
2. Información incompleta de tarifas y guiones
3. Contexto insuficiente para la toma de decisiones
4. Alucinaciones donde el modelo inventaba información no presente en la conversación

## Solución Implementada

Se creó un sistema mejorado que:

1. **Enriquece el contexto** proporcionado al modelo de IA
2. **Estructura la información** de manera más clara y organizada
3. **Personaliza el análisis** según el tipo de producto identificado
4. **Incluye ejemplos previos** para mejorar la consistencia
5. **Proporciona instrucciones explícitas** contra alucinaciones
6. **Extrae segmentos relevantes** para facilitar el análisis

### Componentes Principales

#### 1. Módulo `enhanced_prompt.py`

Módulo central que:
- Detecta automáticamente el tipo de producto mencionado en la transcripción
- Carga información específica sobre tarifas, guiones y ejemplos para ese producto
- Genera prompts personalizados con toda la información necesaria
- Proporciona instrucciones claras al modelo para evitar alucinaciones
- Extrae y procesa la respuesta del modelo para obtener datos estructurados

#### 2. Estructura de Datos

Se crearon directorios para almacenar:
- Tarifas específicas para cada producto (`data/tarifas/`)
- Guiones de ventas para cada producto (`data/guiones/`)
- Ejemplos de auditorías correctas (`data/ejemplos_auditoria/`)

#### 3. Integración con Sistema Existente

Se modificaron los siguientes archivos para integrar la solución:
- `diariza.py`: Punto de entrada principal para el procesamiento de audios
- `l_process/call_evaluation.py`: Módulo de evaluación de llamadas
- `l_process/unified_processing.py`: Módulo para procesar audios divididos

### Flujo del Proceso Mejorado

1. Se transcribe el audio utilizando el sistema existente
2. Se extrae la información del producto y metadatos relevantes
3. Se genera un prompt personalizado usando `enhanced_prompt.py`
4. Se envía el prompt al modelo de IA con instrucciones mejoradas
5. Se procesa la respuesta para extraer datos estructurados
6. Se determina la calificación final y se guarda el resultado

### Características Clave

- **Personalización por producto**: El sistema detecta automáticamente el tipo de producto (Practiseguro, Salvafactura, Plan Mascotas, etc.) y adapta el análisis.
- **Instrucciones anti-alucinación**: Se dan instrucciones explícitas y repetidas al modelo para basarse ÚNICAMENTE en información presente en la transcripción.
- **Aprendizaje de ejemplos**: Se incluyen ejemplos de auditorías exitosas para guiar al modelo.
- **Alta tolerancia a fallos**: Si el nuevo método falla, el sistema utiliza el método anterior como respaldo.
- **Estructura clara**: Se define un formato específico para las evaluaciones, asegurando que se cubran todos los puntos necesarios.

## Beneficios de la Solución

1. **Mayor precisión**: El modelo recibe toda la información necesaria para realizar análisis precisos.
2. **Menos alucinaciones**: Se reducen significativamente las instancias donde el modelo inventa información.
3. **Consistencia**: Los análisis siguen un formato estándar y son consistentes entre diferentes llamadas.
4. **Adaptabilidad**: El sistema se adapta automáticamente a diferentes tipos de productos.
5. **Robustez**: Cuenta con sistemas de respaldo para garantizar que las auditorías siempre se completen.

## Uso

El sistema mejorado se utiliza exactamente igual que el anterior:

```bash
python diariza.py ruta_del_archivo_de_audio.mp3
```

O para audios divididos:

```bash
python diariza.py --contrato-dividido json_contrato_info
```

No se requieren cambios en la forma de invocar el sistema, ya que las mejoras están integradas de manera transparente en el flujo existente.

## Mantenimiento

Para añadir soporte para nuevos productos:

1. Agregar el archivo de tarifas en `data/tarifas/` (formato JSON)
2. Agregar el guión en `data/guiones/` (formato TXT)
3. Agregar palabras clave para detectar el producto en la variable `PRODUCTO_KEYWORDS` en `enhanced_prompt.py`
4. Opcionalmente, añadir ejemplos de auditorías correctas en `data/ejemplos_auditoria/[nombre_producto]/`

Estas mejoras proporcionan un sistema más robusto, preciso y confiable para la auditoría de ventas telefónicas.
