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
        db_type: 'default' (DB_*) o 'aws' (AWS_DB_* en .env).
    """
    try:
        if db_type == 'default':
            password = os.environ.get('DB_PASSWORD')
            if not password:
                logger.error("DB_PASSWORD no configurada en el entorno")
                return None
            connection = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'auto_sbot'),
                user=os.environ.get('DB_USER', 'adminsbot'),
                password=password,
            )
        elif db_type == 'aws':
            required = (
                'AWS_DB_HOST',
                'AWS_DB_USER',
                'AWS_DB_PASSWORD',
                'AWS_DB_NAME',
            )
            missing = [k for k in required if not os.environ.get(k)]
            if missing:
                logger.error("Faltan variables AWS en entorno: %s", missing)
                return None
            connection = mysql.connector.connect(
                host=os.environ['AWS_DB_HOST'],
                database=os.environ['AWS_DB_NAME'],
                user=os.environ['AWS_DB_USER'],
                password=os.environ['AWS_DB_PASSWORD'],
                port=int(os.environ.get('AWS_DB_PORT', '3306')),
            )
        else:
            logger.error("db_type desconocido: %s", db_type)
            return None
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

def guardar_resultado_auditoria(texto, datos_procesados=None):
    """
    Guarda el resultado de la auditoría en la base de datos con mayor robustez.
    Asegura la consistencia entre el texto del reporte y la calificación guardada.
    
    Args:
        texto: Texto original del resultado
        datos_procesados: Diccionario con datos extraidos estructurados (opcional)
    """
    # Log para depuración
    logger.info("Iniciando guardado de resultado de auditoría")
    
    # Verificar que el texto del reporte tiene una calificación explícita al inicio
    from l_process.detection import extraer_calificacion
    
    # Si no hay datos procesados, crearlos con la información mínima
    if not datos_procesados:
        datos_procesados = {}
    
    # Extraer calificación del texto
    calificacion_en_texto = extraer_calificacion(texto)
    logger.info(f"Calificación detectada en el texto: {calificacion_en_texto}")
    
    # Verificar si existe una calificación en los datos procesados
    calificacion_en_datos = None
    if 'calificacion' in datos_procesados:
        calificacion_en_datos = datos_procesados['calificacion']
    elif 'decision' in datos_procesados:
        calificacion_en_datos = datos_procesados['decision']
    elif 'calificacion_final' in datos_procesados:
        calificacion_en_datos = datos_procesados['calificacion_final']
    
    logger.info(f"Calificación en datos procesados: {calificacion_en_datos}")
    
    # Determinar la calificación final a usar (priorizar POSITIVA)
    calificacion_final = calificacion_en_datos if calificacion_en_datos else calificacion_en_texto
    
    # Si ambas calificaciones existen y son diferentes, favorecer POSITIVA
    if calificacion_en_texto and calificacion_en_datos and calificacion_en_texto != calificacion_en_datos:
        if calificacion_en_texto == 'POSITIVA' or calificacion_en_datos == 'POSITIVA':
            calificacion_final = 'POSITIVA'
            logger.info("Conflicto de calificaciones resuelto en favor de POSITIVA")
    
    # Si aún no tenemos calificación, establecer POSITIVA por defecto
    if not calificacion_final:
        calificacion_final = 'POSITIVA'
        logger.info("No se detectó calificación, usando POSITIVA por defecto")
    
    # Asegurarse de que la calificación final sea válida
    calificacion_final = calificacion_final.upper().strip()
    if calificacion_final not in ['POSITIVA', 'NEGATIVA']:
        calificacion_final = 'POSITIVA'
        logger.info(f"Calificación inválida, ajustando a POSITIVA")
    
    # Actualizar los datos procesados con la calificación final
    datos_procesados['calificacion'] = calificacion_final
    
    # Asegurarse de que el texto tenga la calificación al inicio
    if 'CALIFICACIÓN FINAL' not in texto[:200]:
        logger.info("Añadiendo calificación explícita al inicio del texto")
        texto = f"**CALIFICACIÓN FINAL: [{calificacion_final}]**\n\n{texto}"
    elif calificacion_en_texto != calificacion_final:
        # Reemplazar la calificación en el texto si es diferente
        logger.info(f"Reemplazando calificación en el texto de {calificacion_en_texto} a {calificacion_final}")
        texto = texto.replace(f"CALIFICACIÓN FINAL: [{calificacion_en_texto}]", f"CALIFICACIÓN FINAL: [{calificacion_final}]")
        texto = texto.replace(f"CALIFICACIÓN FINAL: {calificacion_en_texto}", f"CALIFICACIÓN FINAL: {calificacion_final}")
    
    # Guardar en la base de datos
    connection = get_mysql_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            # Buscar el registro más reciente sin observación
            cursor.execute("""
                SELECT reg_contrato, idtb_reg_audio 
                FROM tb_reg_audio 
                WHERE (reg_observ_audio IS NULL OR reg_observ_audio = '') 
                ORDER BY idtb_reg_audio DESC LIMIT 1
            """)
            ultimo_registro = cursor.fetchone()

            if ultimo_registro:
                num_contrato, id_registro = ultimo_registro
                logger.info(f"Guardando resultado para contrato {num_contrato}, ID: {id_registro}")
                
                # Actualizar observaciones y estado de venta en una sola consulta
                cursor.execute("""
                    UPDATE tb_reg_audio
                    SET reg_observ_audio = %s, reg_estado_venta = %s
                    WHERE idtb_reg_audio = %s
                """, (texto, calificacion_final, id_registro))
                
                connection.commit()
                logger.info(f"Resultado guardado en la base de datos con calificación: {calificacion_final}")
                
                # Forzar actualización del estado de venta por si acaso
                from data_updateBD import actualizar_estado_venta
                actualizar_estado_venta(num_contrato, calificacion_final)
            else:
                logger.warning("No se encontró un registro pendiente para guardar el resultado")
        except Error as e:
            logger.error(f"Error al guardar el resultado: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        logger.error("No se pudo establecer conexión con la base de datos")
    
    # Log de finalización
    logger.info("Guardado de resultado de auditoría completado")
    
    # Crear archivo de log adicional para fines de depuración
    try:
        log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "resultados_auditoria.log"), "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] Calificación guardada: {calificacion_final}\n")
    except Exception as e:
        logger.error(f"Error al escribir archivo de log: {e}")

def actualizar_estado_venta(numero_contrato, estado_venta):
    """
    Actualiza el estado de venta en la base de datos con una lógica mejorada.
    Ahora realiza múltiples verificaciones para garantizar que el estado se guarde correctamente.
    """
    # Log de inicio
    logger.info(f"INICIO: Actualizando estado de venta para contrato {numero_contrato}")
    
    # Validar que estado_venta sea uno de los valores permitidos
    estado_venta_original = estado_venta if estado_venta else ""
    estado_venta = estado_venta.upper().strip() if estado_venta else "POSITIVA"
    
    # Si es un valor inválido, establecer a POSITIVA y registrar
    if estado_venta not in ['POSITIVA', 'NEGATIVA']:
        logger.warning(f"Valor de estado_venta no válido: '{estado_venta_original}'. Ajustando a 'POSITIVA'")
        estado_venta = 'POSITIVA'
    
    # Crear directorio de log si no existe
    log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
    os.makedirs(log_dir, exist_ok=True)
    
    # Registrar la operación en un log detallado para depuración
    log_file = os.path.join(log_dir, "estado_venta.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"[{timestamp}] Contrato: {numero_contrato}, Estado: {estado_venta}\n")
    
    # Verificar estado actual en la base de datos antes de actualizar
    connection = get_mysql_connection()
    estado_actual = None
    
    if connection is not None:
        try:
            cursor = connection.cursor()
            # Buscar el registro más reciente de este contrato
            cursor.execute(
                "SELECT idtb_reg_audio, reg_estado_venta FROM tb_reg_audio WHERE reg_contrato = %s ORDER BY idtb_reg_audio DESC LIMIT 1", 
                (numero_contrato,)
            )
            resultado = cursor.fetchone()
            
            if resultado:
                id_registro, estado_actual = resultado
                logger.info(f"Estado actual para contrato {numero_contrato}: '{estado_actual}', ID: {id_registro}")
                
                # Si el estado actual es POSITIVA y se intenta cambiar a NEGATIVA, no permitirlo
                if estado_actual == 'POSITIVA' and estado_venta == 'NEGATIVA':
                    logger.warning(f"Intento de cambiar estado de POSITIVA a NEGATIVA, manteniendo POSITIVA")
                    with open(log_file, "a", encoding='utf-8') as f:
                        f.write(f"[{timestamp}] ALERTA: Intento de cambiar {numero_contrato} de POSITIVA a NEGATIVA, bloqueado\n")
                    # No permitir degradar una venta POSITIVA a NEGATIVA
                    return True
            else:
                logger.warning(f"No se encontró registro previo para el contrato {numero_contrato}")
        except Error as e:
            logger.error(f"Error verificando estado actual: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    # Ejecutar la actualización del estado en la base de datos
    # Usamos una consulta más precisa con condiciones adicionales
    query = """
    UPDATE tb_reg_audio
    SET reg_estado_venta = %s
    WHERE reg_contrato = %s 
    AND (reg_estado_venta IS NULL OR reg_estado_venta = '' OR reg_estado_venta = 'NEGATIVA')
    ORDER BY idtb_reg_audio DESC
    LIMIT 1
    """
    params = (estado_venta, numero_contrato)
    result = execute_query(query, params)
    
    # Registrar el resultado de la actualización
    if result:
        logger.info(f"Estado de venta actualizado para el contrato {numero_contrato}: '{estado_venta}'")
        
        # Verificar que la actualización se haya realizado correctamente
        connection = get_mysql_connection()
        if connection is not None:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT reg_estado_venta FROM tb_reg_audio WHERE reg_contrato = %s ORDER BY idtb_reg_audio DESC LIMIT 1", 
                    (numero_contrato,)
                )
                resultado = cursor.fetchone()
                
                if resultado:
                    estado_final = resultado[0]
                    logger.info(f"VERIFICACIÓN: Estado actual en BD: '{estado_final}'")
                    
                    # Registrar la verificación final en el log
                    with open(log_file, "a", encoding='utf-8') as f:
                        f.write(f"[{timestamp}] VERIFICACIÓN: Contrato {numero_contrato}, Estado final: '{estado_final}'\n")
                    
                    # Si persiste la inconsistencia, hacer un último intento con FORCE UPDATE
                    if estado_final != estado_venta and estado_venta == 'POSITIVA':
                        logger.warning(f"Inconsistencia detectada. Realizando actualización forzada para {numero_contrato}")
                        
                        # Consulta de emergencia que actualiza sin condiciones
                        force_query = """
                        UPDATE tb_reg_audio
                        SET reg_estado_venta = 'POSITIVA'
                        WHERE reg_contrato = %s
                        ORDER BY idtb_reg_audio DESC
                        LIMIT 1
                        """
                        execute_query(force_query, (numero_contrato,))
                        
                        # Registrar la actualización forzada
                        with open(log_file, "a", encoding='utf-8') as f:
                            f.write(f"[{timestamp}] ACTUALIZACION FORZADA: Contrato {numero_contrato} a POSITIVA\n")
            except Error as e:
                logger.error(f"Error verificando actualización: {e}")
            finally:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
        
        # Registrar el final del proceso
        logger.info(f"FIN: Actualización de estado completada para contrato {numero_contrato}")
        return True
    else:
        logger.error(f"Error: No se pudo actualizar el estado de venta para el contrato {numero_contrato}")
        
        # Registrar el error en el log
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] ERROR: Falló actualización para contrato {numero_contrato}\n")
        
        return False

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
