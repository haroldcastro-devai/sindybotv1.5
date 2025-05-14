# SindyBot - Sistema Inteligente de Auditoría Automática

![Logo SindyBot](static/assets/images/logo-dark.png)

## Descripción General

SindyBot es un sistema integral de auditoría automática para llamadas de ventas de seguros, desarrollado específicamente para agilizar y estandarizar el proceso de evaluación de calidad y cumplimiento normativo. El sistema procesa archivos de audio de llamadas, realiza transcripciones con separación de hablantes, extrae información clave y genera evaluaciones automáticas que determinan si la venta cumple con todos los requisitos legales y de calidad.

**Versión actual**: 0.14 (Mayo 2025)

## Características Principales

- **Interfaz web completa** desarrollada con Django y Bootstrap
- **Procesamiento automático de audio** con diarización (separación de hablantes)
- **Extracción inteligente de datos clave** de las transcripciones
- **Evaluación automatizada** utilizando modelos de IA avanzados
- **Comparación de script** contra guiones predefinidos
- **Dashboard analítico** para seguimiento de métricas y tendencias
- **Base de datos SQL** para almacenamiento y consulta de resultados
- **Sistema de corrección de texto** para mejorar la calidad de las transcripciones
- **Integración con múltiples formatos de audio** (.wav, .mp3, .gsm, etc.)
- **Procesamiento por lotes** mediante archivos Excel
- **Reportes detallados** exportables en Excel

## Arquitectura del Sistema

El sistema SindyBot está compuesto por varios módulos interconectados:

1. **Frontend (Django)**: Interfaz web para la interacción con el usuario
2. **Módulo de Procesamiento de Audio**: Realiza la diarización y transcripción
3. **Módulo de Análisis de Texto**: Extrae información clave y corrige texto
4. **Módulo de Evaluación**: Analiza el cumplimiento utilizando IA
5. **Base de Datos**: Almacena resultados, transcripciones y evaluaciones
6. **API REST**: Permite integración con sistemas externos

![Arquitectura SindyBot](static/docs/arquitectura_sindybot.png)

## Requisitos del Sistema

### Hardware Recomendado

- **CPU**: Intel i7/Ryzen 7 o superior (mínimo 4 núcleos)
- **RAM**: 64GB mínimo (128GB recomendado)
- **Almacenamiento**: SSD 1TB mínimo
- **GPU**: NVIDIA con mínimo 16GB VRAM SOPORTE CUDACORE (recomendado para procesamiento acelerado)

### Software Requerido

- **Sistema Operativo**: Windows 10/11 o Linux (Ubuntu 20.04+)
- **Python**: Versión 3.9.21+
- **Anaconda/Miniconda**: Para gestión de entornos
- **MySQL**: Versión 8.0.32+
- **FFmpeg**: Para procesamiento de audio (versión 5.0+)

## Instalación

### 1. Configuración del Entorno Conda

```bash
# Crear un nuevo entorno conda
conda create -n sindybot python=3.9.21
conda activate sindybot

# Instalar torch con soporte CUDA
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# Instalar dependencias principales
pip install django==4.2.20 mysql-connector-python==8.0.33 python-dotenv==1.0.0
```

### 2. Instalación de Dependencias Específicas

```bash
# Navegue a la carpeta del proyecto
cd /path/to/sindybot

# Instalar dependencias
pip install -r requirements.txt

# Instalar WhisperX (modificado)
cd mod_bot/whisperX
pip install -e .
cd ../..
```

### 3. Configuración de la Base de Datos

```bash
# Crear base de datos MySQL
mysql -u root -p
```

```sql
CREATE DATABASE auto_sbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'adminsbot'@'localhost' IDENTIFIED BY '&-4GWwgiw9UfFfOp';
GRANT ALL PRIVILEGES ON auto_sbot.* TO 'adminsbot'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# Aplicar migraciones
python manage.py migrate
```

### 4. Configuración de Variables de Entorno

Cree un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```
DEBUG=True
SECRET_KEY=s8hfg738hf72h3fhh20sdhf03h2f0hslfhslhf83hf2
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,192.168.X.X
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

DB_NAME=auto_sbot
DB_USER=adminsbot
DB_PASSWORD=&-4GWwgiw9UfFfOp
DB_HOST=localhost
DB_PORT=3306
```

### 5. Configuración de Ollama (Modelo de IA)

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Iniciar servicio Ollama
systemctl start ollama

# Descargar modelo Qwen2.5
ollama pull qwen2.5:14b-instruct-q6_K
```

### 6. Creación de Usuario Administrador

```bash
python manage.py createsuperuser
```

## Ejecución del Sistema

### Modo Desarrollo

```bash
# Iniciar servidor Django
python manage.py runserver 0.0.0.0:8000
```

### Modo Producción

```bash
# Iniciar con Gunicorn
gunicorn --bind 0.0.0.0:8000 core.wsgi:application --workers 4 --threads 2

# Alternativamente, usar el script de build
./build.sh
```

### Iniciar Procesamiento de Auditoría

```bash
# Procesar un archivo individual
python mod_bot/diariza.py /ruta/al/archivo/audio.mp3

# Procesar contrato dividido (múltiples archivos)
python mod_bot/diariza.py --contrato-dividido '{"contrato": "12345", "archivos": ["parte1.mp3", "parte2.mp3"]}'
```

## Estructura de Directorios

```
sindybot/
├── admin_gradient/     # Personalización del admin Django
├── audio-text/         # Directorio de salida para transcripciones
│   ├── log_audio_to_text/    # Transcripciones de audio
│   ├── Log_sales_audito/     # Resultados de auditoría
│   └── uni_files_audito/     # Archivos unificados (contratos divididos)
├── authentication/     # Módulo de autenticación
├── core/               # Configuración principal de Django
├── home/               # Aplicación principal (vistas y lógica)
├── mod_bot/            # Módulo de procesamiento y IA
│   ├── data/           # Datos de referencia (guiones, tarifas)
│   ├── Diccionary/     # Diccionario para corrección de texto
│   ├── l_process/      # Módulos de procesamiento
│   ├── logic_utils/    # Utilidades para lógica de negocio
│   ├── tools/          # Herramientas auxiliares
│   └── whisperX/       # Motor de transcripción modificado
├── static/             # Archivos estáticos
├── staticfiles/        # Archivos estáticos recopilados
├── templates/          # Plantillas HTML
└── temp/               # Archivos temporales y sesiones
```

## Entorno Conda

El proyecto utiliza un entorno Conda específico con las siguientes dependencias principales:

```
# Nombre del entorno: Origen2-0
# Python: 3.9.21

# Dependencias críticas
django==4.2.20
mysql-connector-python==8.0.33
python-dotenv==1.0.0
torch==2.0.1
torchaudio==2.0.2
numpy==1.24.3
pandas==2.0.2
openpyxl==3.1.2
ollama==0.1.20
whisper==1.1.10
librosa==0.10.1
pyannote.audio==2.1.1
transformers==4.30.2
ffmpeg-python==0.2.0
nltk==3.8.1
matplotlib==3.7.1
seaborn==0.12.2
scikit-learn==1.2.2
```

## Librerías Python y Dependencias

El proyecto depende de varias librerías Python, categorizadas por funcionalidad:

### Web y Backend
- Django 4.2.20: Framework web principal
- Django REST Framework: Para APIs
- Gunicorn: Servidor WSGI para producción
- Python-dotenv: Para gestión de variables de entorno

### Procesamiento de Audio
- Whisper: Modelo base de reconocimiento de voz
- WhisperX: Versión modificada con diarización
- PyAnnote Audio: Para diarización de hablantes
- Librosa: Procesamiento de señales de audio
- FFmpeg-Python: Manipulación de archivos de audio

### Inteligencia Artificial
- Ollama: Cliente para modelos locales de IA
- Transformers: Modelos pre-entrenados de Hugging Face
- Torch: Framework para aprendizaje profundo
- HunSpell: Para corrección ortográfica
- NLTK: Procesamiento de lenguaje natural

### Análisis de Datos
- Pandas: Manipulación y análisis de datos
- NumPy: Computación numérica
- Matplotlib y Seaborn: Visualización de datos
- Scikit-learn: Algoritmos de aprendizaje automático

### Base de Datos
- MySQL Connector Python: Conexión a base de datos MySQL

### Utilitarios
- OpenpPyXL: Manipulación de archivos Excel
- STR2BOOL: Conversión de strings a booleanos
- Requests: Para peticiones HTTP
- Tqdm: Barras de progreso
- Loguru: Logging avanzado

## Configuración Avanzada

### Configuración de Modelos

Puede ajustar los parámetros del modelo en `mod_bot/diariza.py`:

```python
# Aumentar temperatura para respuestas más creativas y detalladas
response = model.generate(
    model="qwen2.5:14b-instruct-q6_K", 
    prompt=prompt_mejorado,
    temperature=0.3,  # Valor ajustable (0.1-0.5 recomendado)
    num_ctx=8192,     # Tamaño del contexto 
    num_predict=5000  # Longitud máxima de la respuesta
)
```

### Configuración de Extracción de Datos

Puede personalizar los patrones de extracción en `mod_bot/l_process/extractor_datos.py`:

```python
# Ejemplo: Añadir nuevos patrones para correos electrónicos
patron_correo = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
```

### Configuración de Sesiones

Puede ajustar el comportamiento de las sesiones en `core/settings.py`:

```python
# Configuración de sesiones - usando almacenamiento en archivos 
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = os.path.join(BASE_DIR, 'temp', 'sessions')
SESSION_COOKIE_AGE = 86400  # 24 horas en segundos
SESSION_COOKIE_SECURE = False  # Cambiar a True en producción con HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = False
```

## Despliegue en Producción

### Opción 1: Servidor Dedicado

1. Configure Nginx como proxy inverso:

```nginx
server {
    listen 80;
    server_name sindybot.tudominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /path/to/sindybot;
    }

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. Configure systemd para gestionar el servicio:

```ini
[Unit]
Description=SindyBot service
After=network.target

[Service]
User=sindybot
Group=sindybot
WorkingDirectory=/path/to/sindybot
ExecStart=/path/to/anaconda3/envs/sindybot/bin/gunicorn --bind 0.0.0.0:8000 core.wsgi:application --workers 4 --threads 2
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Opción 2: Contenedores Docker

Un archivo `Dockerfile` y `docker-compose.yml` están disponibles en la raíz del proyecto:

```bash
# Construir imagen
docker-compose build

# Ejecutar servicios
docker-compose up -d
```

## Mantenimiento

### Respaldo de Base de Datos

```bash
# Respaldo manual
mysqldump -u adminsbot -p auto_sbot > backup_$(date +"%Y%m%d").sql

# Restauración
mysql -u adminsbot -p auto_sbot < backup_20250512.sql
```

### Optimización de Rendimiento

Para mejorar el rendimiento del sistema en servidores con recursos limitados:

1. Reduzca los workers de Gunicorn según la RAM disponible:
   - 2GB RAM: 2 workers
   - 4GB RAM: 4 workers
   - 8GB RAM: 6-8 workers

2. Optimice el modelo de IA:
   - Use modelos más pequeños (e.j. Llama3:8b)
   - Reduzca el tamaño del contexto (num_ctx)
   - Implemente caché de resultados similares

### Solución de Problemas Comunes

#### Errores de Sesión

Si experimenta errores de sesión ("Session data corrupted"):

1. Limpie el directorio de sesiones:
   ```bash
   rm -rf temp/sessions/*
   ```

2. Verifique que SECRET_KEY no haya cambiado

#### Problemas con WhisperX

Si experimenta problemas con la diarización:

1. Verifique la instalación de FFmpeg:
   ```bash
   ffmpeg -version
   ```

2. Reinstale PyAnnote Audio:
   ```bash
   pip uninstall pyannote.audio
   pip install pyannote.audio==2.1.1
   ```

#### Errores de Memoria

Si encuentra errores de memoria durante el procesamiento:

1. Implemente limpieza de memoria:
   ```python
   import gc
   gc.collect()
   ```

2. Procese los archivos en lotes más pequeños

## Licenciamiento

Este software es propiedad de la empresa y está disponible exclusivamente para uso interno. No está permitida su distribución, modificación o uso no autorizado.
