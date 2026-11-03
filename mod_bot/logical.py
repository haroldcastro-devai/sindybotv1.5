import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from datetime import datetime
import subprocess
import sys
import threading
import psutil
import json
from data_updateBD import guardar_ruta_directorio, insertar_datos_audio, actualizar_conteo_archivos
from logic_utils.get_tags import obtener_gasera_seguro

# Obtener directorio base del script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def convertir_fechas(df):
    fechas_convertidas = []
    for fecha in df[3]:
        try:
            fecha_obj = datetime.strptime(str(fecha), "%d/%m/%Y %H:%M")
            fecha_convertida = fecha_obj.strftime("%d-%m-%y")
            fechas_convertidas.append(fecha_convertida)
        except ValueError:
            pass
    return fechas_convertidas

def registrar_error(tipo_error, nombre_archivo, hora):
    log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "log_err.txt"), "a") as file:
        file.write(f"Tipo de Error: {tipo_error}\n")
        file.write(f"Nombre del Archivo: {nombre_archivo}\n")
        file.write(f"Hora: {hora}\n\n")

def guardar_ruta_directorio(ruta):
    usuario_file = os.environ.get("SINDYBOT_USER_FILE") or os.path.join(
        BASE_DIR, "usuario_temporal.txt"
    )
    with open(usuario_file, "r", encoding="utf-8") as f:
        usuario = f.read().strip()
    from data_updateBD import guardar_ruta_directorio as guardar_ruta_bd
    guardar_ruta_bd(ruta, usuario)

def insertar_datos_bd(gasera, numero_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3, tipo_archivo, peso_kb):
    insertar_datos_audio(gasera, numero_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3, tipo_archivo, peso_kb)

def show_messagebox(type, title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    if type == "info":
        messagebox.showinfo(title, message, parent=root)
    elif type == "error":
        messagebox.showerror(title, message, parent=root)
    root.destroy()

def run_loading_animation():
    # Usar ruta relativa para loading.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    loading_path = os.path.join(script_dir, "loading.py")
    subprocess.Popen([sys.executable, loading_path])

def stop_loading_animation():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'python' in proc.info['name'].lower():
            try:
                cmdline = proc.cmdline()
                if len(cmdline) > 1 and 'loading.py' in cmdline[1]:
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

def ordenar_archivos_audio(archivos_audios, productos_por_contrato=None):
    """
    Ordena y agrupa los archivos de audio por contrato
    
    Args:
        archivos_audios: Lista de rutas de archivos de audio
        productos_por_contrato: Diccionario con los productos asociados a cada contrato
    """
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
                print(f"Error procesando archivo: {nombre_archivo} - {str(e)}")
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

    return archivos_por_contrato

def procesar_archivos_ordenados(archivos_por_contrato, contratos, fechas, productos_por_contrato=None):
   total_archivos_procesados = 0
   # Obtener la ruta del directorio del script actual
   script_dir = os.path.dirname(os.path.abspath(__file__))
   # Ruta relativa al script de diarización
   diariza_path = os.path.join(script_dir, "diariza.py")

   for clave_contrato, contrato_info in archivos_por_contrato.items():
       print(f"\nProcesando contrato: {contrato_info['metadata']['contrato']}")

       if contrato_info['metadata']['contrato'] in contratos:
           try:
               if contrato_info['es_dividido']:
                   print(f"  Procesando contrato dividido con {len(contrato_info['partes'])} partes")

                   primer_archivo = os.path.basename(contrato_info['partes'][0]['ruta'])
                   gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(primer_archivo)

                   if fecha_contrato in fechas:
                       tipo_archivo = os.path.splitext(contrato_info['partes'][0]['ruta'])[-1].upper()
                       peso_kb = sum(os.path.getsize(parte['ruta'])/1024 for parte in contrato_info['partes'])

                       insertar_datos_bd(
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

               else:
                   ruta_archivo = contrato_info['partes'][0]['ruta']
                   gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(
                       os.path.basename(ruta_archivo)
                   )

                   if fecha_contrato in fechas:
                       tipo_archivo = os.path.splitext(ruta_archivo)[-1].upper()
                       peso_kb = os.path.getsize(ruta_archivo) / 1024

                       insertar_datos_bd(
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

           except Exception as e:
               hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
               registrar_error(str(e), clave_contrato, hora_actual)
               print(f"Error procesando contrato {clave_contrato}")
               print(f"Error: {str(e)}")

   return total_archivos_procesados



def seleccionar_archivo():
    mensaje_alerta_archivo = "Seleccione el archivo de reporte Ilio (Gerencial)\n\nRecuerde que los audios y el Gerencial deben pertenecer al mismo rango del mes"
    show_messagebox("info", "Mensaje de Alerta // Archivo de Reporte", mensaje_alerta_archivo)

    root = tk.Tk()
    root.withdraw()

    archivo = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xlsx;*.xls")])

    if archivo:
        print("Archivo seleccionado:", archivo)
        try:
            df = pd.read_excel(archivo, sheet_name="Hoja1", header=None)
            
            # Verificar que tenemos las columnas necesarias
            columnas_requeridas = [3, 23, 32]  # Fecha, Producto, Contrato
            if all(col < len(df.columns) for col in columnas_requeridas):
                contratos = set(df.iloc[:, 32].astype(str))
                fechas = set(convertir_fechas(df))
                
                # Extraer productos por contrato
                productos_por_contrato = {}
                for idx, row in df.iterrows():
                    if not pd.isna(row[32]) and not pd.isna(row[23]):
                        productos_por_contrato[str(row[32])] = str(row[23])
                
                print(f"Contratos extraídos: {len(contratos)}")
                print(f"Fechas extraídas: {len(fechas)}")
                print(f"Productos extraídos: {len(productos_por_contrato)}")

                if contratos and fechas:
                    mensaje_alerta_directorio = "Seleccione el directorio de Audios\n\nRecuerde que los audios y el Gerencial deben pertenecer al mismo rango del mes"
                    show_messagebox("info", "Mensaje de Alerta// Directorio de Audios", mensaje_alerta_directorio)

                    while True:
                        directorio_audios = filedialog.askdirectory()
                        if directorio_audios:
                            archivos_audios = []
                            for root, dirs, files in os.walk(directorio_audios):
                                for file in files:
                                    if file.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.gsm')):
                                        archivos_audios.append(os.path.join(root, file))

                            if archivos_audios:
                                print("Directorio de Audios seleccionado:", directorio_audios)
                                print("Cantidad de archivos en el directorio:", len(archivos_audios))
                                guardar_ruta_directorio(directorio_audios)

                                # Iniciar la animación de carga en un hilo separado
                                animation_thread = threading.Thread(target=run_loading_animation)
                                animation_thread.start()

                                try:
                                    # Ordenar y agrupar los archivos por contrato, usando la información de productos
                                    archivos_ordenados = ordenar_archivos_audio(
                                        archivos_audios, 
                                        productos_por_contrato
                                    )

                                    # Procesar los archivos ordenados, pasando la información de productos
                                    total_archivos_procesados = procesar_archivos_ordenados(
                                        archivos_ordenados,
                                        contratos,
                                        fechas,
                                        productos_por_contrato
                                    )

                                    print(f"Total de archivos procesados: {total_archivos_procesados}")

                                    # Actualizar el conteo en la base de datos
                                    actualizar_conteo_archivos(total_archivos_procesados)

                                    # Detener la animación de carga
                                    stop_loading_animation()
                                    animation_thread.join()

                                    if total_archivos_procesados > 0:
                                        show_messagebox("info", "Proceso Completado",
                                                    f"Se han procesado {total_archivos_procesados} archivos.")
                                    else:
                                        show_messagebox("error", "Error: No Existe Coincidencia",
                                                    "No hay coincidencia entre el Reporte Gerencial y los archivos de audio en el directorio seleccionado.")

                                except Exception as e:
                                    stop_loading_animation()
                                    animation_thread.join()
                                    show_messagebox("error", "Error", f"Error durante el procesamiento: {str(e)}")
                                    registrar_error(str(e), "proceso_general", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                                break
                            else:
                                show_messagebox("error", "Error", "No existen archivos de audio en el directorio seleccionado.")
                        else:
                            show_messagebox("error", "Error", "No se seleccionó ningún directorio de Audios.")
                        break
                else:
                    show_messagebox("error", "Error", "No hay contratos o fechas disponibles en el archivo.")
            else:
                columnas_faltantes = [col for col in columnas_requeridas if col >= len(df.columns)]
                show_messagebox("error", "Error", f"Faltan las siguientes columnas en el archivo: {columnas_faltantes}")
        except Exception as e:
            show_messagebox("error", "Error", f"Error al leer el archivo: {str(e)}")
    else:
        show_messagebox("error", "Error", "No se seleccionó ningún archivo de Reporte Gerencial")

if __name__ == "__main__":
    log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
    os.makedirs(log_dir, exist_ok=True)
    seleccionar_archivo()
