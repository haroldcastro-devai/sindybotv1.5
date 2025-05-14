#!/bin/bash

# Función para esperar por la disponibilidad de la base de datos MySQL
wait_for_db() {
    echo "Esperando que MySQL esté disponible..."
    for i in {1..30}; do
        python -c "
import sys
import mysql.connector
try:
    mysql.connector.connect(
        host='${DB_HOST:-mysql}',
        port=${DB_PORT:-3306},
        user='${DB_USER:-adminsbot}',
        password='${DB_PASSWORD:-&-4GWwgiw9UfFfOp}',
        database='${DB_NAME:-auto_sbot}'
    )
    sys.exit(0)
except Exception as e:
    sys.exit(1)
"
        if [ $? -eq 0 ]; then
            echo "Base de datos disponible. Continuando..."
            return 0
        fi
        echo "Esperando que la base de datos esté disponible... $i/30"
        sleep 2
    done
    echo "Error: No se pudo conectar a la base de datos después de 60 segundos."
    return 1
}

# Esperar por la base de datos
wait_for_db

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar el comando pasado a este script
exec "$@"
