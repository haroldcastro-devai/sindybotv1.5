# Sistema de Gestión de Diccionario de Correcciones

#-----------------------------------------------#
Scripts Ejecutable ---->  diccionario_manager.py
#-----------------------------------------------#

## Descripción General

El Sistema de Gestión de Diccionario de Correcciones es una herramienta diseñada para mejorar la precisión de las transcripciones de audio en el proceso de auditoría de ventas. El sistema permite la creación, gestión y aplicación de un diccionario de correcciones que normaliza términos técnicos, nombres de empresas, productos y frases específicas del sector.

## Propósito

El propósito principal de este sistema es resolver el problema de inconsistencias y errores en las transcripciones de audio, especialmente para términos técnicos y nombres propios que son frecuentemente mal interpretados por los sistemas de reconocimiento de voz.

## Flujo de Trabajo

![Diagrama de Flujo](https://via.placeholder.com/800x400?text=Diagrama+de+Flujo+del+Sistema)

### 1. Gestión del Diccionario

#### Entrada de Datos
- **Interfaz Gráfica**: Permite la adición, edición y eliminación de entradas individuales
- **Carga Masiva**: Permite importar diccionarios completos desde archivos de texto o JSON
- **Entrada Manual**: Admite la transcripción directa de entradas en formato `original:corrección`

#### Almacenamiento
- **Base de Datos Principal (Nube)**: Almacenamiento primario en `34.229.113.3` 
- **Base de Datos Local**: Respaldo automático en base de datos local
- **Exportación**: Permite exportar todo el diccionario a formato JSON para respaldo

### 2. Proceso de Corrección

1. **Carga de Diccionario**: 
   - El sistema intenta cargar el diccionario desde la base de datos en la nube
   - Si falla, intenta cargar desde la base de datos local
   - Si ambas fallan, utiliza un archivo de respaldo como último recurso

2. **Procesamiento del Texto**:
   - **Corrección de Frases**: Primero procesa frases completas (secuencias de múltiples palabras)
   - **Corrección de Palabras**: Luego procesa palabras individuales
   - **Preservación de Formato**: Mantiene mayúsculas/minúsculas y puntuación original

3. **Integración con el Sistema de Transcripción**:
   - El módulo `text_processing.py` llama a la función `cargar_diccionario()` para obtener el diccionario
   - Luego aplica la función `corregir_texto()` a la transcripción
   - El texto corregido continúa el flujo normal de procesamiento de la llamada

### 3. Actualización y Mantenimiento

- Las actualizaciones al diccionario se aplican instantáneamente a ambas bases de datos
- Las nuevas entradas identificadas por los usuarios pueden agregarse fácilmente
- El sistema permite probar las correcciones antes de guardarlas definitivamente

## Estructura del Sistema

### Componentes Principales

1. **Interfaz Gráfica (`diccionario_manager.py`)**:
   - Gestión completa del diccionario
   - Pruebas de corrección
   - Estadísticas

2. **Gestor de Base de Datos (`db_manager.py`)**:
   - Conexión a bases de datos
   - Creación y mantenimiento de tablas
   - Carga y almacenamiento de datos

3. **Motor de Corrección (`diccionario_utils.py`)**:
   - Algoritmos de corrección
   - Manejo de palabras y frases
   - Preservación de formato

4. **Integración con Sistema de Transcripción (`text_processing.py`)**:
   - Carga del diccionario
   - Aplicación de correcciones al texto de la transcripción

5. **Utilidades de Importación/Exportación (`import_dictionary.py`)**:
   - Migración desde sistemas anteriores
   - Importación masiva de diccionarios

## Casos de Uso Típicos

### Corrección de Términos Técnicos
- **Ejemplo**: "cupo" → "cupo"
- **Beneficio**: Mantiene consistencia en términos técnicos

### Corrección de Nombres de Empresas
- **Ejemplo**: "gases del caribe" → "Gases del Caribe"
- **Beneficio**: Estandariza nombres de empresas con formato correcto

### Corrección de Productos y Servicios
- **Ejemplo**: "seguro de vida alfa" → "seguros_de_vida_alfa"
- **Beneficio**: Normaliza nombres de productos para análisis posterior

### Corrección de Frases Comunes Mal Transcritas
- **Ejemplo**: "Consortigas" → "con surtigas"
- **Beneficio**: Corrige errores comunes de transcripción donde palabras se juntan incorrectamente

## Requisitos del Sistema

- Python 3.7+
- MySQL o MariaDB
- Librerías: tkinter, mysql-connector-python

## Instalación y Configuración

Consultar el archivo INSTALL.md para instrucciones detalladas de instalación y configuración.

## Notas Importantes

- El sistema distingue entre palabras individuales y frases (secuencias de palabras)
- Las entradas se procesan en orden de longitud (las más largas primero) para evitar reemplazos parciales incorrectos
- El sistema preserva la capitalización original del texto
- Se recomienda realizar respaldos periódicos del diccionario

## Mantenimiento y Soporte

Para reportar problemas o solicitar nuevas características, contactar al equipo de desarrollo a través del sistema de tickets interno.