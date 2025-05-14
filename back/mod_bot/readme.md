# SindyBot: Sistema de Auditoría Automatizada de Llamadas de Ventas

![Version]
![License]

SindyBot es una solución integral para la auditoría automatizada de llamadas de ventas. El sistema transcribe, analiza y evalúa conversaciones telefónicas para determinar el cumplimiento de los guiones de venta, verificar la aceptación o rechazo de productos, y generar reportes detallados de auditoría.

## 📋 Características

- **Diarización de audio**: Identifica y separa automáticamente a los diferentes hablantes.
- **Transcripción precisa**: Utiliza WhisperX para transcribir audio a texto con alta fidelidad.
- **Análisis de cumplimiento**: Compara las conversaciones con guiones preestablecidos.
- **Detección inteligente**: Identifica aceptaciones, rechazos y objeciones de clientes.
- **Evaluación automática**: Califica las ventas como positivas o negativas basándose en criterios predefinidos.
- **Procesamiento masivo**: Capacidad para procesar grandes volúmenes de audios.
- **Integración con bases de datos**: Almacena resultados para análisis posteriores.
- **Corrección de texto**: Mejora automáticamente la calidad de las transcripciones.

## 🔧 Requisitos

### Dependencias principales

- Python 3.9+
- PyQt5 (para la interfaz gráfica)
- WhisperX (para transcripción y diarización)
- MySQL Connector (para acceso a base de datos)
- Pandas (para procesamiento de datos)
- Ollama (para análisis de texto)

### Dependencias de sistema

- CUDA compatible con PyTorch (recomendado para mejor rendimiento)
- FFmpeg (para procesamiento de audio)

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone 
cd sindybot
```

2. Crear y activar entorno virtual:
```bash

- Debe estar instalado conda o miniconda
En windows
conda create -n sindybot python=3.9
conda activate sindybot

version actual estable y compatible con fedora o ubuntu


```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar la base de datos:
   - Crear una base de datos MySQL
   - Actualizar el archivo `settings.ini` con las credenciales

5. Descargar modelos necesarios (esto puede tardar dependiendo de tu conexión):
```bash
python -m whisperx.download_models
```

## 📊 Estructura del Proyecto

```
.
├── data/                      # Datos de referencia
│   └── raw/                   # Archivos JSON de configuración
│       ├── guionV2.json       # Guiones a seguir por los agentes
│       └── tarifasV2.json     # Información de tarifas y productos
├── diccionary/                # Diccionarios para corrección de texto
├── l_process/                 # Módulos de procesamiento
│   ├── audio_processing.py    # Procesamiento de audio
│   ├── call_evaluation.py     # Evaluación de llamadas
│   ├── detection.py           # Detección de patrones en texto
│   ├── file_utils.py          # Utilidades de manejo de archivos
│   ├── logger_config.py       # Configuración de logging
│   ├── text_processing.py     # Procesamiento de texto
│   └── unified_processing.py  # Procesamiento unificado
├── Log_Reporte/               # Almacenamiento de resultados
├── logic_utils/               # Utilidades lógicas
├── tools/                     # Herramientas adicionales
├── data_updateBD.py           # Actualización de base de datos
├── diariza.py                 # Script principal de diarización
├── loading.py                 # Animación de carga
└── logical.py                 # Lógica principal del negocio
```

## 🎯 Uso

### Procesamiento masivo de audios

```bash
python logical.py
```
Este comando iniciará la interfaz para seleccionar el archivo de reporte (Excel) y el directorio de audios.

### Procesamiento de un solo archivo

```bash
python diariza.py ruta/al/archivo/audio.mp3
```

### Procesamiento de un archivo dividido en múltiples partes

```bash
python diariza.py --contrato-dividido "JSON_CON_INFO_DE_CONTRATO"
```

## 📝 Flujo de trabajo

1. El sistema carga un archivo Excel con información de contratos.
2. Solicita la carpeta donde se encuentran los archivos de audio.
3. Procesa y agrupa los audios por contrato.
4. Para cada archivo:
   - Transcribe el audio a texto mediante WhisperX.
   - Identifica a los diferentes hablantes (diarización).
   - Analiza el cumplimiento del guión de ventas.
   - Detecta aceptaciones o rechazos del cliente.
   - Evalúa si la venta es positiva o negativa.
   - Genera un reporte detallado.
   - Almacena los resultados en la base de datos.

## 📊 Reportes generados

Para cada llamada evaluada, el sistema genera:

- **Transcripción completa**: Texto de la conversación con timestamps e identificación de hablantes.
- **Reporte de auditoría**: Análisis detallado del cumplimiento del guión, objeciones y resoluciones.
- **Calificación final**: Determinación si la venta es POSITIVA o NEGATIVA.
- **Registro en base de datos**: Almacenamiento de los resultados para análisis posteriores.

## 📈 Métricas clave

El sistema evalúa múltiples factores para determinar el resultado de una venta:

- Adherencia al guión establecido
- Aceptaciones explícitas del cliente
- Resolución de objeciones
- Confirmación de información personal
- Aceptación de términos y condiciones
- Aceptación del cobro en factura

## 🌐 Integración con bases de datos

El sistema se integra con dos tipos de bases de datos:
- **Base de datos local**: Para almacenamiento y procesamiento rápido
- **Base de datos en la nube**: Para respaldo y acceso remoto

## 🔍 Diagnóstico y solución de problemas

### Archivos de log

Los logs se almacenan en los siguientes directorios:
- `Log_Reporte/log_err/auditoria.log`: Registro general de actividad
- `Logica_Log_Err/log_err.txt`: Registro de errores específicos

### Problemas comunes

- **Error de transcripción**: Verifique el formato del archivo de audio y la instalación de FFmpeg.
- **Error de conexión a BD**: Confirme las credenciales en `settings.ini`.
- **Bajo rendimiento**: Asegúrese de tener GPU compatible con CUDA para mejor velocidad.


## 📄 Licencia

Este proyecto está licenciado bajo la licencia MIT - vea el archivo `LICENSE` para más detalles.

## 📞 Contacto

Si tiene preguntas o necesita asistencia, contacte a:
- Nombre - Ing Harold Castro Torres [hcastro@catalitico.com.co]

