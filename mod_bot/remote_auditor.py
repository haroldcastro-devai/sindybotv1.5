import os
import pandas as pd
import sys
import json
import logging
from datetime import datetime, timedelta
import subprocess
import time
from data_updateBD import guardar_ruta_directorio, insertar_datos_audio, actualizar_conteo_archivos
from logic_utils.get_tags import obtener_gasera_seguro

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Logica_Log_Err", "remote_audit.log"),
    filemode='a'
)
logger = logging.getLogger(__name__)

# Constantes
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_BASE_DIR = r"I:\Unidades compartidas\PV-AUDIOS-AUDITORIA\AUDIOS ESCUCHA\SERVIPROTECCION"

# Archivo de progreso
PROGRESO_FILE = os.path.join(BASE_DIR, "Logica_Log_Err", "progreso_auditoria.json")

def inicializar_progreso(total_archivos):
    """
    Inicializa el archivo de progreso de la auditoría
    """
    log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
    os.makedirs(log_dir, exist_ok=True)
    
    progreso = {
        'en_progreso': True,
        'archivo_actual': '',
        'fecha_actual': '',
        'archivos_procesados': 0,
        'total_archivos': total_archivos,
        'tiempo_inicio': datetime.now().isoformat(),
        'actividad': [
            {'hora': datetime.now().strftime('%H:%M:%S'), 'mensaje': 'Iniciando proceso de auditoría...'}
        ]
    }
    
    with open(PROGRESO_FILE, 'w') as f:
        json.dump(progreso, f)

def actualizar_progreso(archivo_actual='', fecha_actual='', archivos_procesados=None, mensaje=None):
    """
    Actualiza el archivo de progreso de la auditoría
    """
    try:
        # Verificar si existe el archivo
        if not os.path.exists(PROGRESO_FILE):
            inicializar_progreso(100)  # valor por defecto

        # Leer el archivo actual
        with open(PROGRESO_FILE, 'r') as f:
            progreso = json.load(f)
        
        # Actualizar campos
        if archivo_actual:
            progreso['archivo_actual'] = archivo_actual
        
        if fecha_actual:
            progreso['fecha_actual'] = fecha_actual
        
        if archivos_procesados is not None:
            progreso['archivos_procesados'] = archivos_procesados
        
        if mensaje:
            progreso['actividad'].append({
                'hora': datetime.now().strftime('%H:%M:%S'),
                'mensaje': mensaje
            })
            # Mantener solo los últimos 20 mensajes
            if len(progreso['actividad']) > 20:
                progreso['actividad'] = progreso['actividad'][-20:]
        
        # Calcular tiempo transcurrido
        if 'tiempo_inicio' in progreso:
            inicio = datetime.fromisoformat(progreso['tiempo_inicio'])
            transcurrido = datetime.now() - inicio
            horas = transcurrido.seconds // 3600
            minutos = (transcurrido.seconds % 3600) // 60
            segundos = transcurrido.seconds % 60
            progreso['tiempo_transcurrido'] = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        
        # Guardar actualización
        with open(PROGRESO_FILE, 'w') as f:
            json.dump(progreso, f)
    
    except Exception as e:
        logger.error(f"Error al actualizar progreso: {str(e)}")

def finalizar_progreso(exito=True, mensaje=None):
    """
    Finaliza el seguimiento de progreso
    """
    try:
        # Verificar si existe el archivo
        if not os.path.exists(PROGRESO_FILE):
            return

        # Leer el archivo actual
        with open(PROGRESO_FILE, 'r') as f:
            progreso = json.load(f)
        
        # Marcar como finalizado
        progreso['en_progreso'] = False
        
        if mensaje:
            progreso['actividad'].append({
                'hora': datetime.now().strftime('%H:%M:%S'),
                'mensaje': mensaje
            })
        
        # Guardar actualización
        with open(PROGRESO_FILE, 'w') as f:
            json.dump(progreso, f)
    
    except Exception as e:
        logger.error(f"Error al finalizar progreso: {str(e)}")

def registrar_error(tipo_error, nombre_archivo, hora):
    """Registra un error en el archivo de log"""
    log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "log_err.txt"), "a") as file:
        file.write(f"Tipo de Error: {tipo_error}\n")
        file.write(f"Nombre del Archivo: {nombre_archivo}\n")
        file.write(f"Hora: {hora}\n\n")
    logger.error(f"Error: {tipo_error} - Archivo: {nombre_archivo}")

def leer_excel_y_extraer_datos(archivo_excel):
    """
    Lee el archivo Excel y extrae contratos y fechas
    Retorna: contratos, fechas, productos_por_contrato
    """
    try:
        logger.info(f"Leyendo archivo Excel: {archivo_excel}")
        actualizar_progreso(mensaje=f"Leyendo archivo Excel...")
        
        df = pd.read_excel(archivo_excel, sheet_name="Hoja1", header=None)
        
        # Verificar que tenemos las columnas necesarias
        columnas_requeridas = [3, 23, 32]  # Fecha, Producto, Contrato
        if all(col < len(df.columns) for col in columnas_requeridas):
            contratos = set(df.iloc[:, 32].astype(str))
            
            # Extraer fechas en formato DD/MM/AAAA
            fechas_contratos = {}
            fechas_set = set()
            for idx, row in df.iterrows():
                if not pd.isna(row[32]) and not pd.isna(row[3]):
                    contrato = str(row[32])
                    fecha_str = str(row[3])
                    
                    # Extraer fecha en formato DD/MM/AAAA
                    try:
                        # A veces la fecha tiene formato "DD/MM/AAAA 00:00"
                        if ' ' in fecha_str:
                            fecha_str = fecha_str.split(' ')[0]
                        
                        # Verificar formato de fecha
                        if '/' in fecha_str:
                            fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                            fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                            
                            fechas_contratos[contrato] = fecha_formateada
                            fechas_set.add(fecha_formateada)
                    except ValueError as e:
                        logger.warning(f"Error al procesar fecha '{fecha_str}': {e}")
            
            # Extraer productos por contrato
            productos_por_contrato = {}
            for idx, row in df.iterrows():
                if not pd.isna(row[32]) and not pd.isna(row[23]):
                    productos_por_contrato[str(row[32])] = str(row[23])
            
            logger.info(f"Contratos extraídos: {len(contratos)}")
            logger.info(f"Fechas extraídas: {len(fechas_set)}")
            logger.info(f"Productos extraídos: {len(productos_por_contrato)}")
            
            actualizar_progreso(mensaje=f"Analizados {len(contratos)} contratos del Excel")
            
            return contratos, fechas_contratos, productos_por_contrato
        else:
            columnas_faltantes = [col for col in columnas_requeridas if col >= len(df.columns)]
            error_msg = f"Faltan las siguientes columnas en el archivo: {columnas_faltantes}"
            logger.error(error_msg)
            actualizar_progreso(mensaje=f"Error: {error_msg}")
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Error al leer el archivo Excel: {str(e)}")
        actualizar_progreso(mensaje=f"Error al leer el archivo Excel: {str(e)}")
        raise

def construir_ruta_audio(fecha_str):
    """
    Construye la ruta del directorio donde se encuentran los archivos de audio
    basado en la fecha en formato DD/MM/AAAA
    """
    try:
        # Convertir fecha al formato necesario
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
        
        # Extraer componentes de la fecha
        dia = fecha_obj.day
        mes = fecha_obj.month
        anio = fecha_obj.year
        
        # Nombres de meses en español
        nombres_meses = {
            1: "01 ENERO", 2: "02 FEBRERO", 3: "03 MARZO", 4: "04 ABRIL",
            5: "05 MAYO", 6: "06 JUNIO", 7: "07 JULIO", 8: "08 AGOSTO",
            9: "09 SEPTIEMBRE", 10: "10 OCTUBRE", 11: "11 NOVIEMBRE", 12: "12 DICIEMBRE"
        }
        
        # Construir ruta
        ruta = os.path.join(
            AUDIO_BASE_DIR,
            str(anio),
            nombres_meses[mes],
            f"{dia:02d}"
        )
        
        if os.path.exists(ruta):
            logger.info(f"Ruta de audio encontrada: {ruta}")
            actualizar_progreso(mensaje=f"Ruta de audio encontrada: {nombres_meses[mes]}/{dia:02d}")
            return ruta
        else:
            logger.warning(f"Ruta de audio no encontrada: {ruta}")
            actualizar_progreso(mensaje=f"Buscando rutas alternativas para fecha {fecha_str}")
            # Intenta buscar alternativas si la ruta exacta no existe
            mes_dir = os.path.join(AUDIO_BASE_DIR, str(anio), nombres_meses[mes])
            if os.path.exists(mes_dir):
                # Buscar directorios que puedan contener el día
                for dir_name in os.listdir(mes_dir):
                    if dir_name.startswith(f"{dia:02d}"):
                        ruta_alt = os.path.join(mes_dir, dir_name)
                        logger.info(f"Usando ruta alternativa: {ruta_alt}")
                        actualizar_progreso(mensaje=f"Ruta alternativa encontrada: {dir_name}")
                        return ruta_alt
            
            # Si no encuentra ninguna ruta alternativa, devolver la original
            actualizar_progreso(mensaje=f"No se encontró ruta para fecha {fecha_str}")
            return ruta
    except Exception as e:
        logger.error(f"Error al construir ruta de audio: {str(e)}")
        actualizar_progreso(mensaje=f"Error al buscar ruta de audio: {str(e)}")
        return None

def encontrar_archivos_audio(ruta, contrato):
    """
    Busca archivos de audio para un contrato específico en la ruta proporcionada
    """
    archivos_encontrados = []
    try:
        if os.path.exists(ruta):
            for root, _, files in os.walk(ruta):
                for file in files:
                    # Verificar si es un archivo de audio que corresponde al contrato
                    if (file.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.gsm')) and 
                        f"_{contrato}_" in file):
                        archivos_encontrados.append(os.path.join(root, file))
        
        logger.info(f"Encontrados {len(archivos_encontrados)} archivos para el contrato {contrato}")
        if len(archivos_encontrados) > 0:
            actualizar_progreso(mensaje=f"Encontrados {len(archivos_encontrados)} archivos para contrato {contrato}")
        return archivos_encontrados
    except Exception as e:
        logger.error(f"Error al buscar archivos de audio: {str(e)}")
        actualizar_progreso(mensaje=f"Error al buscar archivos para contrato {contrato}: {str(e)}")
        return []

def ordenar_archivos_audio(archivos_audios, productos_por_contrato=None):
    """
    Ordena y agrupa los archivos de audio por contrato
    
    Args:
        archivos_audios: Lista de rutas de archivos de audio
        productos_por_contrato: Diccionario con los productos asociados a cada contrato
    """
    actualizar_progreso(mensaje=f"Organizando {len(archivos_audios)} archivos de audio")
    
    archivos_por_contrato = {}
    orden_partes = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}

    for ruta_archivo in archivos_audios:
        nombre_archivo = os.path.basename(ruta_archivo)
        partes_nombre = nombre_archivo.split("_")

        if len(partes_nombre) >= 4:
            try:
                codigo_gasera = partes_nombre[0]
                numero_contrato = partes_nombre[1]
                fecha = partes_nombre[2]
                parte_audio = partes_nombre[-1].split(".")[0]

                # Extraer seguro o producto del nombre del archivo
                seguro_archivo = None
                if len(partes_nombre) >= 4:
                    seguro_archivo = partes_nombre[3].split(".")[0]

                # Clave única para agrupar partes del mismo contrato
                clave_contrato = f"{codigo_gasera}_{numero_contrato}_{fecha}"

                if clave_contrato not in archivos_por_contrato:
                    archivos_por_contrato[clave_contrato] = {
                        'partes': [],
                        'es_dividido': parte_audio in orden_partes,
                        'metadata': {
                            'gasera': codigo_gasera,
                            'contrato': numero_contrato,
                            'fecha': fecha,
                            'seguro': seguro_archivo
                        }
                    }

                archivos_por_contrato[clave_contrato]['partes'].append({
                    'orden': orden_partes.get(parte_audio, 999),
                    'ruta': ruta_archivo,
                    'parte': parte_audio,
                    'seguro': seguro_archivo
                })

            except (IndexError, KeyError) as e:
                logger.error(f"Error procesando archivo: {nombre_archivo} - {str(e)}")
                actualizar_progreso(mensaje=f"Error procesando archivo: {nombre_archivo}")
                continue

    # Ordenar partes de cada contrato y priorizar archivos según producto
    for contrato_key, contrato in archivos_por_contrato.items():
        # Separar el número de contrato de la clave
        partes_clave = contrato_key.split('_')
        if len(partes_clave) >= 2:
            numero_contrato = partes_clave[1]
            
            # Verificar si tenemos información de producto para este contrato
            producto_esperado = productos_por_contrato.get(numero_contrato) if productos_por_contrato else None
            
            if producto_esperado and contrato['partes']:
                # Mapear abreviaturas de productos a formatos en archivos
                producto_mapping = {
                    'PRACTI': 'PRACTI',
                    'PRACTISEGURO': 'PRACTI',
                    'FUNERARIO': 'FUN',
                    'FUTURO PROTEGIDO PLUS': 'FUTURO-P-P',
                    'SALVAFACTURA': 'SALVA',
                    'FACTURA PROTEGIDA': 'FACTURA-P',
                    'SEGURO MASCOTAS': 'MSCT'
                }
                
                # Convertir el producto esperado a su formato de archivo
                producto_formato_archivo = None
                for key, value in producto_mapping.items():
                    if producto_esperado.upper() in key.upper() or key.upper() in producto_esperado.upper():
                        producto_formato_archivo = value
                        break
                
                # Si tenemos un formato de archivo para el producto esperado
                if producto_formato_archivo:
                    # Filtrar partes que coincidan con el producto esperado
                    partes_coincidentes = [parte for parte in contrato['partes'] 
                                          if parte['seguro'] and producto_formato_archivo in parte['seguro']]
                    
                    if partes_coincidentes:
                        # Reemplazar todas las partes con solo las que coinciden con el producto
                        contrato['partes'] = partes_coincidentes
                        # Actualizar la metadata
                        contrato['metadata']['seguro'] = producto_formato_archivo
                
        # Ordenar las partes por orden
        if contrato['es_dividido']:
            contrato['partes'].sort(key=lambda x: x['orden'])

    actualizar_progreso(mensaje=f"Organizados {len(archivos_por_contrato)} contratos")
    return archivos_por_contrato

def procesar_archivos_ordenados(archivos_por_contrato, contratos, producto_contrato=None):
   total_archivos_procesados = 0
   # Obtener la ruta del directorio del script actual
   script_dir = os.path.dirname(os.path.abspath(__file__))
   # Ruta relativa al script de diarización
   diariza_path = os.path.join(script_dir, "diariza.py")

   for clave_contrato, contrato_info in archivos_por_contrato.items():
       # Verificar si el proceso ha sido cancelado
       if comprobar_cancelacion():
           logger.info("Proceso cancelado. Interrumpiendo procesamiento de archivos.")
           actualizar_progreso(mensaje="Proceso cancelado. Interrumpiendo procesamiento de archivos.")
           return total_archivos_procesados
       logger.info(f"Procesando contrato: {contrato_info['metadata']['contrato']}")
       
       # Actualizar progreso
       archivo_actual = f"{contrato_info['metadata']['gasera']}_{contrato_info['metadata']['contrato']}"
       fecha_actual = contrato_info['metadata']['fecha']
       actualizar_progreso(
           archivo_actual=archivo_actual, 
           fecha_actual=fecha_actual, 
           mensaje=f"Procesando contrato {contrato_info['metadata']['contrato']}"
       )

       if contrato_info['metadata']['contrato'] in contratos:
           try:
               if contrato_info['es_dividido']:
                   logger.info(f"  Procesando contrato dividido con {len(contrato_info['partes'])} partes")
                   actualizar_progreso(mensaje=f"Procesando contrato dividido con {len(contrato_info['partes'])} partes")

                   primer_archivo = os.path.basename(contrato_info['partes'][0]['ruta'])
                   gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(primer_archivo)

                   tipo_archivo = os.path.splitext(contrato_info['partes'][0]['ruta'])[-1].upper()
                   peso_kb = sum(os.path.getsize(parte['ruta'])/1024 for parte in contrato_info['partes'])

                   insertar_datos_audio(
                       gasera,
                       num_contrato,
                       fecha_contrato,
                       seguro_1,
                       seguro_2,
                       seguro_3,
                       tipo_archivo,
                       peso_kb
                   )

                   contrato_json = json.dumps(contrato_info)

                   subprocess.run([
                       sys.executable,
                       diariza_path,
                       "--contrato-dividido",
                       contrato_json
                   ])

                   total_archivos_procesados += 1
                   actualizar_progreso(
                       archivos_procesados=total_archivos_procesados, 
                       mensaje=f"Completado contrato: {contrato_info['metadata']['contrato']}"
                   )

               else:
                   ruta_archivo = contrato_info['partes'][0]['ruta']
                   gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(
                       os.path.basename(ruta_archivo)
                   )

                   tipo_archivo = os.path.splitext(ruta_archivo)[-1].upper()
                   peso_kb = os.path.getsize(ruta_archivo) / 1024

                   insertar_datos_audio(
                       gasera, num_contrato, fecha_contrato,
                       seguro_1, seguro_2, seguro_3,
                       tipo_archivo, peso_kb
                   )

                   subprocess.run([
                       sys.executable,
                       diariza_path,
                       ruta_archivo
                   ])

                   total_archivos_procesados += 1
                   actualizar_progreso(
                       archivos_procesados=total_archivos_procesados, 
                       mensaje=f"Completado contrato: {contrato_info['metadata']['contrato']}"
                   )
                   
               # Breve pausa para dar tiempo al UI a actualizarse
               time.sleep(0.5)

           except Exception as e:
               hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
               registrar_error(str(e), clave_contrato, hora_actual)
               logger.error(f"Error procesando contrato {clave_contrato}: {str(e)}")
               actualizar_progreso(mensaje=f"Error procesando contrato {clave_contrato}: {str(e)}")

   return total_archivos_procesados

def comprobar_cancelacion():
    """
    Comprueba si el proceso ha sido cancelado
    
    Returns:
        bool: True si el proceso ha sido cancelado, False en caso contrario
    """
    try:
        archivo_cancelacion = os.path.join(BASE_DIR, "cancelar_proceso.txt")
        if os.path.exists(archivo_cancelacion):
            logger.info("Proceso cancelado por el usuario")
            actualizar_progreso(mensaje="Proceso cancelado por el usuario")
            # Eliminar el archivo de cancelación
            try:
                os.remove(archivo_cancelacion)
            except Exception as e:
                logger.error(f"Error al eliminar archivo de cancelación: {str(e)}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error al comprobar cancelación: {str(e)}")
        return False

def iniciar_proceso_remoto(archivo_excel, usuario):
    """
    Función principal que inicia el proceso de auditoría desde un cliente remoto
    
    Args:
        archivo_excel: Ruta del archivo Excel
        usuario: Nombre de usuario que inicia el proceso
    
    Returns:
        dict: Resultados del proceso con éxito/error
    """
    try:
        # Verificar si hay un proceso en curso que fue cancelado
        if os.path.exists(os.path.join(BASE_DIR, "cancelar_proceso.txt")):
            os.remove(os.path.join(BASE_DIR, "cancelar_proceso.txt"))
            logger.info("Eliminado archivo de cancelación anterior")
        
        logger.info(f"Iniciando proceso remoto para usuario {usuario} con archivo {archivo_excel}")
        
        # Inicializar seguimiento de progreso con valores temporales
        # Usamos 100 como valor inicial, luego se actualizará con el valor real
        inicializar_progreso(100)  
        actualizar_progreso(mensaje=f"Iniciando proceso remoto para usuario {usuario}")
        
        # Leer el archivo Excel y extraer los datos
        contratos, fechas_contratos, productos_por_contrato = leer_excel_y_extraer_datos(archivo_excel)
        
        if not contratos or not fechas_contratos:
            logger.error("No hay contratos o fechas disponibles en el archivo")
            finalizar_progreso(exito=False, mensaje="No hay contratos o fechas disponibles en el archivo")
            return {"success": False, "error": "No hay contratos o fechas disponibles en el archivo"}
        
        actualizar_progreso(mensaje=f"Encontrados {len(contratos)} contratos en el archivo Excel")
        
        # Proceso por cada contrato
        archivos_audio_totales = []
        directorios_procesados = set()
        
        # Para cada contrato, buscar su fecha correspondiente y los archivos de audio
        for contrato in contratos:
            if contrato in fechas_contratos:
                fecha = fechas_contratos[contrato]
                logger.info(f"Procesando contrato {contrato} con fecha {fecha}")
                actualizar_progreso(mensaje=f"Buscando archivos para contrato {contrato} con fecha {fecha}")
                
                # Construir la ruta donde deberían estar los archivos de audio
                ruta_audio = construir_ruta_audio(fecha)
                
                if ruta_audio and os.path.exists(ruta_audio):
                    directorios_procesados.add(ruta_audio)
                    
                    # Buscar archivos de audio para este contrato
                    archivos_audio = encontrar_archivos_audio(ruta_audio, contrato)
                    archivos_audio_totales.extend(archivos_audio)
                    actualizar_progreso(mensaje=f"Encontrados {len(archivos_audio)} archivos para contrato {contrato}")
                else:
                    actualizar_progreso(mensaje=f"No se encontró ruta de audio para fecha {fecha}")
        
        # Registrar los directorios procesados
        if directorios_procesados:
            rutas_str = ", ".join(directorios_procesados)
            guardar_ruta_directorio(rutas_str, usuario)
            logger.info(f"Directorios procesados: {rutas_str}")
            actualizar_progreso(mensaje=f"Directorios a procesar: {len(directorios_procesados)}")
        
        # Si se encontraron archivos de audio, procesarlos
        if archivos_audio_totales:
            # Verificar cancelación
            if comprobar_cancelacion():
                logger.info("Proceso cancelado antes de procesar archivos")
                finalizar_progreso(exito=False, mensaje="Proceso cancelado por el usuario")
                return {"success": False, "error": "Proceso cancelado por el usuario", "cancelado": True}
            
            logger.info(f"Se encontraron {len(archivos_audio_totales)} archivos de audio")
            actualizar_progreso(mensaje=f"Total de archivos de audio encontrados: {len(archivos_audio_totales)}")
            
            # Ordenar y agrupar los archivos por contrato, usando la información de productos
            archivos_ordenados = ordenar_archivos_audio(
                archivos_audio_totales, 
                productos_por_contrato
            )
            
            # Verificar cancelación
            if comprobar_cancelacion():
                logger.info("Proceso cancelado después de ordenar archivos")
                finalizar_progreso(exito=False, mensaje="Proceso cancelado por el usuario")
                return {"success": False, "error": "Proceso cancelado por el usuario", "cancelado": True}
            
            # Actualizar el total de archivos en el seguimiento de progreso
            inicializar_progreso(len(archivos_ordenados))
            
            # Procesar los archivos ordenados, pasando la información de productos
            total_archivos_procesados = procesar_archivos_ordenados(
                archivos_ordenados,
                contratos,
                productos_por_contrato
            )
            
            # Verificar si se canceló el proceso
            if comprobar_cancelacion():
                logger.info("Proceso cancelado después de procesar algunos archivos")
                finalizar_progreso(exito=False, mensaje=f"Proceso cancelado por el usuario. Se procesaron {total_archivos_procesados} archivos.")
                return {"success": False, "error": "Proceso cancelado por el usuario", "cancelado": True, "archivos_procesados": total_archivos_procesados}
            
            # Actualizar el conteo en la base de datos
            actualizar_conteo_archivos(total_archivos_procesados)
            
            logger.info(f"Proceso completado. Total de archivos procesados: {total_archivos_procesados}")
            finalizar_progreso(exito=True, mensaje=f"Proceso completado. Se procesaron {total_archivos_procesados} archivos.")
            
            return {
                "success": True, 
                "total_archivos": total_archivos_procesados,
                "directorios_procesados": list(directorios_procesados)
            }
        else:
            logger.warning("No se encontraron archivos de audio para los contratos del Excel")
            finalizar_progreso(exito=False, mensaje="No hay coincidencia entre el Reporte Gerencial y los archivos de audio")
            return {
                "success": False, 
                "error": "No hay coincidencia entre el Reporte Gerencial y los archivos de audio"
            }
            
    except Exception as e:
        logger.error(f"Error en el proceso remoto: {str(e)}")
        registrar_error(str(e), "proceso_remoto", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        finalizar_progreso(exito=False, mensaje=f"Error en el proceso: {str(e)}")
        return {"success": False, "error": str(e)}

# Para probar individualmente
if __name__ == "__main__":
    if len(sys.argv) > 1:
        archivo_excel = sys.argv[1]
        usuario = sys.argv[2] if len(sys.argv) > 2 else "usuario_test"
        
        resultado = iniciar_proceso_remoto(archivo_excel, usuario)
        print(json.dumps(resultado, indent=2))
    else:
        print("Uso: python remote_auditor.py <ruta_excel> [usuario]")