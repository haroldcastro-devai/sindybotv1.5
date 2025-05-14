import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json
import logging
import os

# Crear la carpeta de logs si no existe usando rutas relativas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(BASE_DIR, 'Logica_Log_Err', 'log_err')
os.makedirs(log_dir, exist_ok=True)

# Configuración del logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'auditoria.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_mysql_connection(db_type='default'):
    """
    Establece y retorna una conexión a la base de datos MySQL.
    Args:
        db_type: 'default' para local, 'aws' para AWS (comentado)
    """
    try:
        if db_type == 'default':
            connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'auto_sbot'),
                user=os.environ.get('DB_USER', 'adminsbot'),
                password=os.environ.get('DB_PASSWORD', '&-4GWwgiw9UfFfOp')
            )
        # Conexión a AWS comentada
        # elif db_type == 'aws':
        #     connection = mysql.connector.connect(
        #         host=os.environ.get('AWS_DB_HOST', '34.229.113.3'),
        #         database=os.environ.get('AWS_DB_NAME', 'sindybot_dev'),
        #         user=os.environ.get('AWS_DB_USER', 'dev_user'),
        #         password=os.environ.get('AWS_DB_PASSWORD', 'DevPassword123!')
        #     )
        return connection
    except Error as e:
        logger.error(f"Error al conectar a MySQL ({db_type}): {e}")
        return None

def execute_query(query, params=None):
    """
    Ejecuta una consulta en la base de datos local.
    """
    connection = get_mysql_connection()
    result = None
    if connection is not None:
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            result = True
        except Error as e:
            logger.error(f"Error en la consulta: {e}")
            result = False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return result

def validar_datos(transcripcion, resultado_auditoria, detalles_evaluacion):
    """
    Valida los datos antes de insertarlos en la base de datos.
    """
    if not transcripcion or not isinstance(transcripcion, str):
        raise ValueError("La transcripción no puede estar vacía y debe ser una cadena de texto.")
    if resultado_auditoria not in ["POSITIVA", "NEGATIVA"]:
        raise ValueError("El resultado de la auditoría debe ser 'POSITIVA' o 'NEGATIVA'.")
    if not isinstance(detalles_evaluacion, dict):
        raise ValueError("Los detalles de la evaluación deben ser un diccionario.")

def notificar_error_a_administrador(error):
    """
    Notifica al administrador sobre errores críticos.
    """
    logger.critical(f"Error crítico notificado al administrador: {error}")

def guardar_ruta_directorio(ruta, usuario):
    """
    Guarda la ruta del directorio en la base de datos.
    """
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    query = """
    INSERT INTO tb_reg_activ 
    (reg_tip_dir, reg_tip_consulta, reg_activ_fecha, reg_activ_user) 
    VALUES (%s, %s, %s, %s)
    """
    params = (ruta, "Auditoria", fecha_actual, usuario)
    result = execute_query(query, params)
    
    if not result:
        logger.error("Error: No se pudo guardar en la base de datos")

def insertar_datos_audio(gasera, numero_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3, tipo_archivo, peso_kb):
    """
    Inserta datos de audio en la base de datos.
    """
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    try:
        if fecha_contrato:
            fecha_contrato = datetime.strptime(fecha_contrato, "%d-%m-%y").strftime("%Y-%m-%d")
    except ValueError:
        fecha_contrato = fecha_actual
    
    if seguro_3 and "Parte" in seguro_3:
        seguro_3 = None

    query = """
    INSERT INTO tb_reg_audio 
    (reg_n_gasera, reg_contrato, reg_fechontrat, reg_tseguro1, reg_tseguro2, 
    reg_partaudioventa, reg_tipoarchivo, reg_estado_venta, reg_observ_audio, 
    reg_pesoarch, reg_fecha) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (gasera, numero_contrato, fecha_contrato, seguro_1, seguro_2, 
             seguro_3, tipo_archivo, '', '', str(peso_kb), fecha_actual)
    
    result = execute_query(query, params)
    
    if result:
        logger.info(f"Datos de audio insertados para contrato: {numero_contrato}")
    else:
        logger.error(f"Error: No se pudo insertar en la base de datos")

def actualizar_conteo_archivos(total_archivos_procesados):
    """
    Actualiza el conteo de archivos procesados en la base de datos.
    """
    connection = get_mysql_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM tb_reg_activ")
            count = cursor.fetchone()[0]
            
            if count > 0:
                update_query = """
                UPDATE tb_reg_activ 
                SET reg_activ_archproc = %s 
                WHERE idtb_actv = (SELECT MAX(idtb_actv) 
                FROM (SELECT idtb_actv FROM tb_reg_activ) AS t)
                """
                cursor.execute(update_query, (total_archivos_procesados,))
            else:
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_query = """
                INSERT INTO tb_reg_activ 
                (reg_activ_fecha, reg_activ_user, reg_activ_archproc, 
                reg_tip_consulta, reg_tip_dir) 
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, 
                             (fecha_actual, 'hcastro', total_archivos_procesados, 
                              'Auditoria', 'directorio'))
            
            connection.commit()
            logger.info(f"Conteo actualizado en la base de datos")
            
        except Error as e:
            logger.error(f"Error en la actualización: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def guardar_resultado_auditoria(texto):
    """
    Guarda el resultado de la auditoría en la base de datos.
    """
    connection = get_mysql_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT reg_contrato 
                FROM tb_reg_audio 
                WHERE reg_observ_audio IS NULL OR reg_observ_audio = '' 
                ORDER BY idtb_reg_audio DESC LIMIT 1
            """)
            ultimo_registro = cursor.fetchone()

            if ultimo_registro:
                cursor.execute("""
                    UPDATE tb_reg_audio
                    SET reg_observ_audio = %s
                    WHERE reg_contrato = %s
                """, (texto, ultimo_registro[0]))
                connection.commit()
                logger.info(f"Resultado guardado en la base de datos")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

def actualizar_estado_venta(numero_contrato, estado_venta):
    """
    Actualiza el estado de venta en la base de datos.
    """
    query = """
    UPDATE tb_reg_audio
    SET reg_estado_venta = %s
    WHERE reg_contrato = %s
    ORDER BY idtb_reg_audio DESC
    LIMIT 1
    """
    params = (estado_venta, numero_contrato)
    result = execute_query(query, params)
    
    if result:
        logger.info(f"Estado de venta actualizado para el contrato {numero_contrato}: {estado_venta}")
    else:
        logger.error(f"Error: No se pudo actualizar en la base de datos")

def obtener_datos_por_dia(fecha_inicio, fecha_fin):
    """
    Obtiene datos de ventas por día desde la base de datos.
    """
    connection = get_mysql_connection()
    if connection is not None:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT
                COALESCE(DATE(reg_fecha), CURRENT_DATE) as date,
                COUNT(CASE WHEN reg_estado_venta = 'Positiva' THEN 1 END) as sales0,
                COUNT(CASE WHEN reg_estado_venta = 'Negativa' THEN 1 END) as market1,
                COUNT(*) as sales1,
                ROUND(COUNT(CASE WHEN reg_estado_venta = 'Positiva' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0), 2) as market0
            FROM
                tb_reg_audio
            WHERE
                reg_fecha BETWEEN %s AND %s
                AND reg_fecha IS NOT NULL
            GROUP BY
                DATE(reg_fecha)
            ORDER BY
                DATE(reg_fecha)
            """
            cursor.execute(query, (fecha_inicio, fecha_fin))
            resultados = cursor.fetchall()

            for resultado in resultados:
                if resultado['date'] is None:
                    resultado['date'] = datetime.now().date()

            return resultados
        except Error as e:
            logger.error(f"Error al obtener datos por día: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        logger.error("No se pudo establecer conexión con la base de datos.")
        return []

def insertar_datos_aprendizaje(transcripcion, resultado_auditoria, detalles_evaluacion):
    """
    Inserta datos de aprendizaje en la base de datos.
    """
    try:
        validar_datos(transcripcion, resultado_auditoria, detalles_evaluacion)
        query = """
        INSERT INTO learning_sbot 
        (transcripcion, resultado_auditoria, detalles_evaluacion, fecha_registro)
        VALUES (%s, %s, %s, NOW())
        """
        params = (transcripcion, resultado_auditoria, json.dumps(detalles_evaluacion))
        result = execute_query(query, params)
        
        if result:
            logger.info("Datos de aprendizaje insertados correctamente en la base de datos")
        else:
            logger.error("Error: No se pudo insertar en la base de datos")
            
    except ValueError as e:
        logger.error(f"Error de validación: {e}")
        notificar_error_a_administrador(e)

def obtener_datos_aprendizaje(limit=100):
    """
    Obtiene datos de aprendizaje desde la base de datos.
    """
    connection = get_mysql_connection()
    if connection is not None:
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM learning_sbot ORDER BY fecha_registro DESC LIMIT %s"
            cursor.execute(query, (limit,))
            resultados = cursor.fetchall()
            return resultados
        except Error as e:
            logger.error(f"Error al obtener datos de aprendizaje: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        logger.error("No se pudo establecer conexión con la base de datos.")
        return []

def planuno_detectado(nombre_pluno, calificacion):
    """
    Registra la detección de un plan uno.
    """
    logger.info(f"Plan uno detectado: {nombre_pluno}, Calificación: {calificacion}")

def plandos_detectad(nombre_pldos, calificacion):
    """
    Registra la detección de un plan dos.
    """
    logger.info(f"Plan dos detectado: {nombre_pldos}, Calificación: {calificacion}")