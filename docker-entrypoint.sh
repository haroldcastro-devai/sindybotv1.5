#!/bin/bash
set -euo pipefail

wait_for_db() {
    if [ "${USE_SQLITE_DEMO:-False}" = "True" ]; then
        echo "USE_SQLITE_DEMO=True — omitiendo espera MySQL."
        return 0
    fi
    if [ -z "${DB_PASSWORD:-}" ]; then
        echo "Error: DB_PASSWORD no definida (configure .env)."
        return 1
    fi
    echo "Esperando que MySQL esté disponible..."
    for i in $(seq 1 30); do
        python -c "
import os, sys
import mysql.connector
try:
    mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'mysql'),
        port=int(os.environ.get('DB_PORT', '3306')),
        user=os.environ.get('DB_USER', 'adminsbot'),
        password=os.environ['DB_PASSWORD'],
        database=os.environ.get('DB_NAME', 'auto_sbot'),
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
"
        if [ $? -eq 0 ]; then
            echo "Base de datos disponible."
            return 0
        fi
        echo "Esperando MySQL... $i/30"
        sleep 2
    done
    echo "Error: MySQL no disponible tras 60s."
    return 1
}

wait_for_db

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

exec "$@"

# Desarrollado por: hcastro
