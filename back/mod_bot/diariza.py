#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import gc
import json
from pathlib import Path

# Importar configuración de logging
from l_process.logger_config import logger, configure_logging

# Importar módulos de procesamiento
from l_process.audio_processing import procesar_audio, analizar_hablantes
from l_process.call_evaluation import process_call
from l_process.text_processing import corregir_texto, cargar_diccionario
from l_process.unified_processing import procesar_audio_dividido
from l_process.file_utils import load_json_file
from l_process.detection import extraer_calificacion
from data_updateBD import guardar_resultado_auditoria, actualizar_estado_venta

# Definir rutas usando rutas relativas
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
LLAMADAS_DIR = DATA_DIR / "llamadas"

# Crear el directorio audio-text en la raíz del proyecto
AUDIO_TEXT_DIR = PROJECT_ROOT / "audio-text"
LOG_AUDIO_TO_TEXT = AUDIO_TEXT_DIR / "log_audio_to_text"
LOG_SALES_AUDIT = AUDIO_TEXT_DIR / "Log_sales_audito"
UNIFIED_FILES = AUDIO_TEXT_DIR / "uni_files_audito"

# Asegurarse de que los directorios existen
for dir_path in [AUDIO_TEXT_DIR, LOG_AUDIO_TO_TEXT, LOG_SALES_AUDIT, UNIFIED_FILES]:
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Error creando directorio {dir_path}: {e}")
        raise

def main():
    """
    Función principal del programa.
    """
    try:
        # Configurar logging
        configure_logging()
        
        if len(sys.argv) == 3 and sys.argv[1] == "--contrato-dividido":
            try:
                contrato_info = json.loads(sys.argv[2])
                resultado_auditoria = procesar_audio_dividido(contrato_info)
                logger.info("Procesamiento de contrato dividido completado")
                return
            except json.JSONDecodeError as e:
                logger.error(f"Error decodificando JSON de contrato dividido: {e}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Error procesando contrato dividido: {e}")
                sys.exit(1)

        elif len(sys.argv) == 2:
            try:
                audio_file = sys.argv[1]
                # Ruta relativa para el diccionario
                ruta_diccionario = os.path.join(BASE_DIR, "Diccionary", "diccionary.txt")

                # Cargar diccionario y verificar
                diccionario = cargar_diccionario(ruta_diccionario)
                if not diccionario:
                    logger.warning("Advertencia: Diccionario vacío o no encontrado")

                # Procesar audio
                diarized_text, file_name, result = procesar_audio(audio_file)
                hablantes_info = analizar_hablantes(result)

                # Generar resumen de hablantes
                resumen_hablantes = "Resumen de hablantes:\n"
                for speaker, info in hablantes_info.items():
                    resumen_hablantes += f"{speaker}:\n"
                    resumen_hablantes += f"  Tiempo total hablado: {info['tiempo_total']}\n"
                    resumen_hablantes += f"  Palabras totales: {info['palabras_total']}\n"
                    resumen_hablantes += f"  Número de intervenciones: {info['segmentos']}\n"
                    resumen_hablantes += f"  Velocidad promedio: {info['palabras_total'] / (info['tiempo_total'] if info['tiempo_total'] > 0 else 1):.2f} palabras/segundo\n"
                    if 'interrupciones' in info:
                        resumen_hablantes += f"  Interrupciones: {info['interrupciones']}\n"
                    if 'pausas_largas' in info:
                        resumen_hablantes += f"  Pausas largas: {info['pausas_largas']}\n"
                    if 'porcentaje_tiempo' in info:
                        resumen_hablantes += f"  Porcentaje del tiempo total: {info['porcentaje_tiempo']:.2f}%\n"
                    resumen_hablantes += "\n"

                texto_completo = resumen_hablantes + "\n" + diarized_text
                texto_corregido = corregir_texto(texto_completo, diccionario)

                # Guardar transcripción
                txt_file_path = LOG_AUDIO_TO_TEXT / f"{file_name}.txt"
                with open(txt_file_path, 'w', encoding='utf-8') as file:
                    file.write(texto_corregido)

                # Cargar datos de referencia
                guiones = load_json_file(RAW_DIR / "guionV2.json")
                tarifas = load_json_file(RAW_DIR / "tarifasV2.json")

                if not guiones or not tarifas:
                    logger.error("Error: No se pudieron cargar los datos necesarios de los archivos JSON.")
                    sys.exit(1)

                # Procesar auditoría
                resultado_auditoria = process_call(txt_file_path, guiones, tarifas)

                # Extraer calificación
                calificacion = extraer_calificacion(resultado_auditoria)
                
                # Actualizar estado
                actualizar_estado_venta(file_name.split('_')[1], calificacion)

                # Guardar resultado
                audit_file_path = LOG_SALES_AUDIT / f"{file_name}_auditoria.txt"
                with open(audit_file_path, 'w', encoding='utf-8') as audit_file:
                    audit_file.write(resultado_auditoria)

                # Guardar en base de datos
                guardar_resultado_auditoria(resultado_auditoria)

                gc.collect()
                logger.info("Procesamiento y auditoría completados exitosamente.")

            except Exception as e:
                logger.error(f"Error en el procesamiento principal: {e}")
                sys.exit(1)

        else:
            logger.error("Uso: python diariza.py [--contrato-dividido json_data | audio_file]")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error crítico en main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Error fatal en la ejecución del programa: {e}")
        sys.exit(1)