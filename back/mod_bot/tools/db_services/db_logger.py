#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import json
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from datetime import datetime
import traceback

# Configuración del logger para base de datos
# Cambio a ruta relativa
LOG_DIR = Path(os.path.join('..', '..', 'Log_Reporte', 'log_err'))
LOG_FILE = LOG_DIR / "rep_Bdata.log"

# Crear directorio si no existe
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar logger específico para DB
db_logger = logging.getLogger("db_logger")
db_logger.setLevel(logging.DEBUG)

# Asegurarse de que el logger no tenga handlers duplicados
if not db_logger.handlers:
    # Handler de archivo
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    db_logger.addHandler(file_handler)
    
    # Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    db_logger.addHandler(console_handler)

def log_db_info(connection_config=None):
    """
    Registra información detallada sobre la conexión a la base de datos,
    tablas, columnas y relaciones.
    
    Args:
        connection_config: Configuración de conexión (opcional)
    """
    db_logger.info("=== INICIANDO DIAGNÓSTICO DE BASE DE DATOS ===")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_logger.info(f"Timestamp: {timestamp}")
    
    # Si no se proporcionó configuración, usar valores por defecto
    if not connection_config:
        connection_config = {
            'host': 'localhost',
            'user': 'adminsbot',
            'password': '&-4GWwgiw9UfFfOp',
            'database': 'auto_sbot'
        }
    
    # Registrar configuración (ocultando la contraseña)
    safe_config = connection_config.copy()
    if 'password' in safe_config:
        safe_config['password'] = '*****'  # Ocultar contraseña en logs
    db_logger.info(f"Configuración de conexión: {safe_config}")
    
    connection = None
    try:
        # Intentar conectar a la base de datos
        connection = mysql.connector.connect(**connection_config)
        db_logger.info(f"Conexión establecida: {connection.is_connected()}")
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Información del servidor
            cursor.execute("SELECT VERSION() as version")
            version = cursor.fetchone()
            db_logger.info(f"Versión de MySQL: {version['version'] if version else 'No disponible'}")
            
            # Listar bases de datos
            cursor.execute("SHOW DATABASES")
            databases = [db['Database'] for db in cursor.fetchall()]
            db_logger.info(f"Bases de datos disponibles: {databases}")
            
            # Usar la base de datos especificada
            cursor.execute(f"USE {connection_config['database']}")
            db_logger.info(f"Base de datos seleccionada: {connection_config['database']}")
            
            # Listar tablas
            cursor.execute("SHOW TABLES")
            tables = [table[f"Tables_in_{connection_config['database']}"] for table in cursor.fetchall()]
            db_logger.info(f"Tablas en la base de datos: {tables}")
            
            # Obtener información detallada de cada tabla
            for table in tables:
                db_logger.info(f"\n=== ESTRUCTURA DE TABLA: {table} ===")
                
                # Obtener columnas
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                column_info = [(col['Field'], col['Type'], col['Null'], col['Key'], col['Default']) 
                              for col in columns]
                db_logger.info(f"Columnas en {table}:")
                for col in column_info:
                    db_logger.info(f"  - {col[0]}: {col[1]}, Nullable: {col[2]}, Key: {col[3]}, Default: {col[4]}")
                
                # Obtener claves primarias
                cursor.execute(f"""
                    SELECT k.COLUMN_NAME
                    FROM information_schema.table_constraints t
                    JOIN information_schema.key_column_usage k
                    USING(constraint_name,table_schema,table_name)
                    WHERE t.constraint_type='PRIMARY KEY'
                    AND t.table_schema=DATABASE()
                    AND t.table_name='{table}'
                """)
                primary_keys = [row['COLUMN_NAME'] for row in cursor.fetchall()]
                db_logger.info(f"Claves primarias de {table}: {primary_keys}")
                
                # Obtener claves foráneas
                cursor.execute(f"""
                    SELECT 
                        k.COLUMN_NAME as column_name,
                        k.REFERENCED_TABLE_NAME as ref_table,
                        k.REFERENCED_COLUMN_NAME as ref_column
                    FROM information_schema.key_column_usage k
                    JOIN information_schema.table_constraints t
                    USING(constraint_name,table_schema,table_name)
                    WHERE t.constraint_type='FOREIGN KEY'
                    AND t.table_schema=DATABASE()
                    AND t.table_name='{table}'
                """)
                foreign_keys = [(row['column_name'], row['ref_table'], row['ref_column']) 
                               for row in cursor.fetchall()]
                
                if foreign_keys:
                    db_logger.info(f"Claves foráneas de {table}:")
                    for fk in foreign_keys:
                        db_logger.info(f"  - {fk[0]} -> {fk[1]}({fk[2]})")
                else:
                    db_logger.info(f"No se encontraron claves foráneas para {table}")
                
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                db_logger.info(f"Número de registros en {table}: {count}")
                
                # Obtener una muestra de datos si la tabla no está vacía
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    sample_rows = cursor.fetchall()
                    db_logger.info(f"Muestra de datos de {table} (max 3 registros):")
                    for row in sample_rows:
                        # Convertir valores no serializables a cadenas
                        safe_row = {}
                        for key, value in row.items():
                            if isinstance(value, (datetime, bytes)):
                                safe_row[key] = str(value)
                            else:
                                safe_row[key] = value
                        db_logger.info(f"  {safe_row}")
            
            # Verificar específicamente las tablas necesarias para SindyBot
            required_tables = {
                'gaseras': False,
                'aseguradoras': False,
                'gaseras_aseguradoras': False,
                'planes': False,
                'guiones_planes': False
            }
            
            for table in tables:
                if table in required_tables:
                    required_tables[table] = True
            
            db_logger.info("\n=== VERIFICACIÓN DE TABLAS REQUERIDAS ===")
            for table, exists in required_tables.items():
                status = "✅ PRESENTE" if exists else "❌ FALTANTE"
                db_logger.info(f"Tabla {table}: {status}")
            
            # Consultas de diagnóstico específicas para las tablas que usa SindyBot
            db_logger.info("\n=== CONSULTAS DE DIAGNÓSTICO ===")
            
            # Verificar relaciones entre gaseras y aseguradoras
            try:
                cursor.execute("""
                    SELECT g.nombre as gasera, a.nombre as aseguradora, COUNT(p.id) as planes_count
                    FROM gaseras g
                    JOIN gaseras_aseguradoras ga ON g.id = ga.gasera_id
                    JOIN aseguradoras a ON a.id = ga.aseguradora_id
                    LEFT JOIN planes p ON ga.id = p.gasera_aseguradora_id
                    WHERE g.activo = 1 AND a.activo = 1 AND ga.activo = 1
                    GROUP BY g.id, a.id
                    LIMIT 10
                """)
                relation_data = cursor.fetchall()
                
                db_logger.info("Relaciones gaseras-aseguradoras-planes:")
                for row in relation_data:
                    db_logger.info(f"  - Gasera: {row['gasera']}, Aseguradora: {row['aseguradora']}, Planes: {row['planes_count']}")
                
                # Verificar guiones
                cursor.execute("""
                    SELECT p.nombre as plan, g.id as guion_id, 
                           ga.gasera_id, gs.nombre as gasera,
                           ga.aseguradora_id, a.nombre as aseguradora
                    FROM guiones_planes g
                    JOIN planes p ON g.plan_id = p.id
                    JOIN gaseras_aseguradoras ga ON p.gasera_aseguradora_id = ga.id
                    JOIN gaseras gs ON ga.gasera_id = gs.id
                    JOIN aseguradoras a ON ga.aseguradora_id = a.id
                    WHERE g.activo = 1
                    LIMIT 10
                """)
                guion_data = cursor.fetchall()
                
                db_logger.info("Relaciones de guiones:")
                for row in guion_data:
                    db_logger.info(f"  - Plan: {row['plan']}, Gasera: {row['gasera']}, Aseguradora: {row['aseguradora']}, Guion: {row['guion_id']}")
            except Error as query_error:
                db_logger.error(f"Error en consultas de diagnóstico: {query_error}")
            
            cursor.close()
    except Error as e:
        db_logger.error(f"Error de conexión a la base de datos: {e}")
        db_logger.error(traceback.format_exc())
    finally:
        if connection and connection.is_connected():
            connection.close()
            db_logger.info("Conexión cerrada")
    
    db_logger.info("=== FIN DEL DIAGNÓSTICO DE BASE DE DATOS ===\n")

# Función para registrar consultas específicas
def log_query(query, params=None, result=None, error=None):
    """
    Registra información sobre una consulta SQL específica.
    
    Args:
        query: Consulta SQL
        params: Parámetros usados (opcional)
        result: Resultado de la consulta (opcional)
        error: Error producido (opcional)
    """
    db_logger.info(f"--- REGISTRO DE CONSULTA ---")
    db_logger.info(f"Consulta: {query}")
    
    if params:
        db_logger.info(f"Parámetros: {params}")
    
    if error:
        db_logger.error(f"Error: {error}")
    elif result is not None:
        # Limitar el tamaño de los resultados en el log
        if isinstance(result, list) and len(result) > 3:
            sample = result[:3]
            db_logger.info(f"Resultado (muestra de 3 de {len(result)} registros): {sample}")
        else:
            db_logger.info(f"Resultado: {result}")
    
    db_logger.info("--- FIN DE REGISTRO DE CONSULTA ---")

# Si se ejecuta como script principal, realizar un diagnóstico completo
if __name__ == "__main__":
    log_db_info()