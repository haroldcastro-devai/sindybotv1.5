FROM python:3.9

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema, incluyendo las bibliotecas para MySQL
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    tk

# Copiar los archivos de requerimientos y instalar dependencias
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el proyecto al contenedor
COPY . .

# Crear directorios necesarios con permisos adecuados
RUN mkdir -p /app/Logica_Log_Err /app/temp /app/media /app/staticfiles
RUN chmod -R 777 /app/Logica_Log_Err /app/temp /app/media /app/staticfiles

# Script de entrada para esperar a la base de datos y ejecutar las migraciones
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

# Comando para ejecutar Gunicorn
CMD ["gunicorn", "--config", "gunicorn-cfg.py", "core.wsgi"]
