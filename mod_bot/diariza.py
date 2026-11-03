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
from l_process.extractor_datos import procesar_transcripcion
from data_updateBD import guardar_resultado_auditoria, actualizar_estado_venta

from l_process.llm_client import generate_from_prompt

# Importar módulo de extracción de datos y prompts mejorados
from enhanced_prompt import generar_prompt_mejorado, procesar_respuesta_modelo

# Importar la nueva utilidad de calificación final
from logic_utils.calificador_final import determinar_calificacion_final, aplicar_calificacion_a_texto

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

                # Extraer metadatos del nombre del archivo
                from logic_utils.get_tags import obtener_gasera_seguro
                try:
                    gasera, num_contrato, fecha_contrato, seguro_1, seguro_2, seguro_3 = obtener_gasera_seguro(file_name)
                    seguro = seguro_1 if seguro_1 else seguro_2 if seguro_2 else seguro_3
                except Exception as e:
                    logger.warning(f"Error obteniendo metadatos del archivo: {e}")
                    gasera, num_contrato, fecha_contrato, seguro = "Desconocido", "Desconocido", "Desconocido", "Desconocido"

                # Extraer nombres de asesor y cliente
                from l_process.detection import extract_names
                asesor, cliente = extract_names(texto_corregido)

                # Crear metadatos para el prompt mejorado
                metadata = {
                    'gasera': gasera,
                    'contrato': num_contrato,
                    'fecha': fecha_contrato,
                    'seguro': seguro,
                    'asesor': asesor,
                    'cliente': cliente,
                    'tarifas': tarifas,
                    'guiones': guiones,
                    'analisis_hablantes': hablantes_info
                }

                # Decidir si usar el nuevo sistema de análisis o el antiguo
                # Para asegurar compatibilidad, usamos el nuevo sistema por defecto,
                # pero tenemos el antiguo como respaldo en caso de error
                try:
                    logger.info("Iniciando procesamiento con prompts mejorados")
                    
                    # Extraer datos precisos de la transcripción primero
                    logger.info("Extrayendo datos estructurados de la transcripción")
                    datos_extraidos = procesar_transcripcion(texto_corregido)
                    logger.info(f"Extracción completada: {list(datos_extraidos.keys())}")
                    
                    # Agregar datos extraídos a los metadatos
                    metadata.update({
                        'datos_extraidos': datos_extraidos,
                        'datos_personales': datos_extraidos.get('datos_personales', {}),
                        'planes': datos_extraidos.get('planes', {}),
                        'forma_pago': datos_extraidos.get('forma_pago', {})
                    })
                    
                    # Generar prompt mejorado con la transcripción y metadatos enriquecidos
                    prompt_mejorado = generar_prompt_mejorado(texto_corregido, metadata)
                    
                    logger.info("Análisis con llm_client (Gemini u Ollama)")
                    resultado_auditoria = generate_from_prompt(
                        prompt_mejorado,
                        temperature=0.3,
                        max_output_tokens=8192,
                    )
                    
                    # Extraer calificación del resultado
                    try:
                        # Procesar la respuesta estructurada
                        datos_estructurados = procesar_respuesta_modelo(resultado_auditoria)
                        logger.info(f"Respuesta procesada y estructurada: {list(datos_estructurados.keys())}")

                        # Determinar calificación a partir de los datos estructurados
                        # Priorizar la decisión POSITIVA si hay evidencia de aceptación
                        if 'decision' in datos_estructurados and datos_estructurados['decision']:
                            calificacion_inicial = datos_estructurados['decision']
                            logger.info(f"Calificación inicial basada en datos estructurados: {calificacion_inicial}")
                            
                            # Si la decisión es NEGATIVA, verificar si realmente debe serlo
                            if calificacion_inicial == 'NEGATIVA':
                                # Verificar puntos críticos - si cumplió más del 70%, considerar POSITIVA
                                cumplimiento_suficiente = False
                                if 'puntos_criticos' in datos_estructurados and datos_estructurados['puntos_criticos']:
                                    total_puntos = len(datos_estructurados['puntos_criticos'])
                                    puntos_cumplidos = sum(1 for v in datos_estructurados['puntos_criticos'].values() if v)
                                    ratio_cumplimiento = puntos_cumplidos / total_puntos if total_puntos > 0 else 0
                                    logger.info(f"Ratio de cumplimiento: {ratio_cumplimiento:.2f} ({puntos_cumplidos}/{total_puntos})")
                                    if ratio_cumplimiento >= 0.7:  # 70% o más de puntos críticos cumplidos
                                        cumplimiento_suficiente = True
                                        logger.info("Calificación cambiada a POSITIVA por alto ratio de cumplimiento")
                                
                                # Verificar patrones positivos explícitos en el texto
                                patrones_positivos = [
                                    r'\bventa\s+positiva\b',
                                    r'\baprobada\b',
                                    r'\bPOSITIVA\b',
                                    r'se\s+considera\s+(?:aprobada|positiva)',
                                    r'CALIFICACIÓN\s+FINAL\s*:\s*\[?\s*POSITIVA\s*\]?'
                                ]
                                
                                import re
                                evidencia_positiva = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                                        for patron in patrones_positivos)
                                
                                if evidencia_positiva:
                                    logger.info("Calificación cambiada a POSITIVA por evidencia explícita en el texto")
                                    calificacion = 'POSITIVA'
                                elif cumplimiento_suficiente:
                                    logger.info("Calificación cambiada a POSITIVA por suficiente cumplimiento")
                                    calificacion = 'POSITIVA'
                                else:
                                    # Verificar si hay rechazo explícito
                                    patrones_rechazo = [
                                        r'\bcliente\s+rechaz[aó]\b',
                                        r'\bno\s+(?:autoriz[aó]|acept[aó])\b',
                                        r'\bmanifest[aó]\s+(?:su\s+)?(?:rechazo|negativa)\b'
                                    ]
                                    
                                    rechazo_encontrado = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                                            for patron in patrones_rechazo)
                                    
                                    if rechazo_encontrado:
                                        logger.info("Calificación NEGATIVA confirmada por rechazo explícito")
                                        calificacion = 'NEGATIVA'
                                    else:
                                        # Por defecto, favorecemos POSITIVA si no hay rechazo claro
                                        logger.info("Calificación cambiada a POSITIVA por falta de evidencia de rechazo")
                                        calificacion = 'POSITIVA'
                            else:  # Si la decisión inicial es POSITIVA, mantenerla
                                calificacion = calificacion_inicial
                        else:  # Si no hay decisión en datos estructurados
                            # Buscar patrones en el texto completo
                            import re
                            patrones_positivos = [
                                r'\bventa\s+positiva\b',
                                r'\baprobada\b',
                                r'\bPOSITIVA\b',
                                r'CALIFICACIÓN\s+FINAL\s*:\s*\[?\s*POSITIVA\s*\]?'
                            ]
                            
                            evidencia_positiva = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                                   for patron in patrones_positivos)
                            
                            if evidencia_positiva:
                                logger.info("Calificación establecida como POSITIVA por evidencia explícita en el texto")
                                calificacion = 'POSITIVA'
                            else:
                                # Usar la función extraer_calificacion
                                calificacion = extraer_calificacion(resultado_auditoria)
                                
                                # Si aún así es NEGATIVA, verificar nuevamente
                                if calificacion == 'NEGATIVA':
                                    # Verificar si hay rechazo explícito
                                    patrones_rechazo = [
                                        r'\bcliente\s+rechaz[aó]\b',
                                        r'\bno\s+(?:autoriz[aó]|acept[aó])\b',
                                        r'\bmanifest[aó]\s+(?:su\s+)?(?:rechazo|negativa)\b'
                                    ]
                                    
                                    rechazo_encontrado = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                                           for patron in patrones_rechazo)
                                    
                                    if not rechazo_encontrado:
                                        logger.info("Calificación cambiada a POSITIVA por falta de evidencia de rechazo")
                                        calificacion = 'POSITIVA'
                        
                        # Asegurar que la calificación aparezca correctamente en el resultado
                        logger.info(f"CALIFICACIÓN FINAL DETERMINADA: {calificacion}")
                        
                        # Corregir la calificación en el texto si es necesario
                        if 'calificacion_final' in datos_estructurados:
                            patrones_reemplazo = [
                                (f"CALIFICACIÓN FINAL: [{datos_estructurados['calificacion_final']}]", 
                                 f"CALIFICACIÓN FINAL: [{calificacion}]"),
                                (f"**CALIFICACIÓN FINAL: [{datos_estructurados['calificacion_final']}]**", 
                                 f"**CALIFICACIÓN FINAL: [{calificacion}]**"),
                                (f"# CALIFICACIÓN FINAL: {datos_estructurados['calificacion_final']}", 
                                 f"# CALIFICACIÓN FINAL: {calificacion}")
                            ]
                            
                            for viejo, nuevo in patrones_reemplazo:
                                resultado_auditoria = resultado_auditoria.replace(viejo, nuevo)
                        
                        # Si no hay calificación en el texto, agregarla al inicio
                        if not any(re.search(f"CALIFICACIÓN.*?{calificacion}", resultado_auditoria, re.IGNORECASE)): 
                            resultado_auditoria = f"**CALIFICACIÓN FINAL: [{calificacion}]**\n\n{resultado_auditoria}"
                        
                        # Actualizar calificación en los datos estructurados
                        datos_estructurados['decision'] = calificacion
                        datos_estructurados['calificacion_final'] = calificacion
                        
                    except Exception as e:
                        logger.warning(f"Error procesando respuesta estructurada: {e}")
                        # Si hubo error en el procesamiento estructurado, usar método directo
                        # pero con enfoque favorable a POSITIVA
                        
                        # Buscar patrones de calificación positiva directamente
                        import re
                        patrones_positivos = [
                            r'\bventa\s+positiva\b',
                            r'\baprobada\b',
                            r'\bPOSITIVA\b',
                            r'CALIFICACIÓN\s+FINAL\s*:\s*\[?\s*POSITIVA\s*\]?'
                        ]
                        
                        evidencia_positiva = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                               for patron in patrones_positivos)
                        
                        if evidencia_positiva:
                            logger.info("Calificación establecida como POSITIVA por evidencia directa en texto")
                            calificacion = 'POSITIVA'
                        else:
                            # Usar función estándar pero con verificación adicional
                            calificacion_inicial = extraer_calificacion(resultado_auditoria)
                            
                            if calificacion_inicial == 'NEGATIVA':
                                # Verificar si hay rechazo explícito
                                patrones_rechazo = [
                                    r'\bcliente\s+rechaz[aó]\b',
                                    r'\bno\s+(?:autoriz[aó]|acept[aó])\b',
                                    r'\bmanifest[aó]\s+(?:su\s+)?(?:rechazo|negativa)\b'
                                ]
                                
                                rechazo_encontrado = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                                      for patron in patrones_rechazo)
                                
                                if rechazo_encontrado:
                                    calificacion = 'NEGATIVA'
                                    logger.info("Calificación NEGATIVA confirmada por rechazo explícito")
                                else:
                                    # Por defecto, favorecer POSITIVA
                                    calificacion = 'POSITIVA'
                                    logger.info("Calificación cambiada a POSITIVA por falta de evidencia de rechazo")
                            else:
                                calificacion = calificacion_inicial
                        
                        # Asegurar que la calificación aparezca en el resultado
                        if not any(re.search(f"CALIFICACIÓN.*?{calificacion}", resultado_auditoria, re.IGNORECASE)):
                            resultado_auditoria = f"**CALIFICACIÓN FINAL: [{calificacion}]**\n\n{resultado_auditoria}"
                        
                        # Crear datos estructurados mínimos
                        datos_estructurados = {
                            'decision': calificacion,
                            'calificacion_final': calificacion
                        }
                
                except Exception as e:
                    logger.warning(f"Error en el procesamiento mejorado: {e}. Usando método antiguo.")
                    # Caer al método antiguo en caso de error
                    resultado_auditoria = process_call(txt_file_path, guiones, tarifas)
                    calificacion = extraer_calificacion(resultado_auditoria)
                    
                    # Crear datos estructurados mínimos a partir de los datos extraídos
                    datos_estructurados_bd = {
                        'calificacion': calificacion
                    }
                    
                    # Agregar datos extraídos manualmente si están disponibles
                    if 'datos_extraidos' in metadata:
                        datos_estructurados_bd['datos_extraidos'] = metadata['datos_extraidos']
                    
                    # Agregar calificación al inicio del resultado
                    resultado_auditoria = f"**CALIFICACIÓN FINAL: [{calificacion}]**\n\n{resultado_auditoria}"
                
                # Actualizar los datos estructurados para la base de datos
                datos_estructurados_bd = {}
                
                # Copiar los datos relevantes y asegurar que la calificación sea consistente
                if 'datos_estructurados' in locals() and datos_estructurados:
                    datos_estructurados_bd = datos_estructurados.copy()
                    
                # Añadir datos extraídos si existen
                if 'datos_extraidos' in metadata and metadata['datos_extraidos']:
                    datos_estructurados_bd['datos_extraidos'] = metadata['datos_extraidos']
                
                # PUNTO CLAVE: Aplicar una política de favorecimiento a POSITIVA
                # Si hay alguna evidencia de que la venta es POSITIVA, mantenerla así
                # Solo considerar NEGATIVA si hay evidencia contundente de rechazo
                import re
                patrones_positivos = [
                    r'\bPOSITIVA\b', 
                    r'\bAPROBADA\b',
                    r'CALIFICACIÓN\s+FINAL\s*:\s*\[?\s*POSITIVA\s*\]?'
                ]
                
                # Verificar si hay evidencia explícita de calificación POSITIVA en el texto
                evidencia_positiva = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                      for patron in patrones_positivos)
                
                # Establecer la calificación final por regla de favorecimiento
                if evidencia_positiva:
                    logger.info("Se encontró evidencia explícita de calificación POSITIVA en el texto")
                    calificacion = 'POSITIVA'
                elif calificacion == 'NEGATIVA':
                    # Verificar si hay evidencia de rechazo explícito
                    patrones_rechazo = [
                        r'\bcliente\s+rechaz[aó]\b',
                        r'\bno\s+(?:autoriz[aó]|acept[aó])\b',
                        r'\bmanifest[aó]\s+(?:su\s+)?(?:rechazo|negativa)\b',
                        r'\bel\s+cliente\s+(?:se\s+negó|no\s+accedió)\b'
                    ]
                    
                    rechazo_encontrado = any(re.search(patron, resultado_auditoria, re.IGNORECASE) 
                                         for patron in patrones_rechazo)
                    
                    if not rechazo_encontrado:
                        logger.info("No se encontró evidencia clara de rechazo. Favoreciendo POSITIVA")
                        calificacion = 'POSITIVA'
                        # Modificar el texto del resultado para incluir la calificación correcta
                        if "CALIFICACIÓN FINAL: [NEGATIVA]" in resultado_auditoria:
                            resultado_auditoria = resultado_auditoria.replace(
                                "CALIFICACIÓN FINAL: [NEGATIVA]", 
                                "CALIFICACIÓN FINAL: [POSITIVA]"
                            )
                        elif "**CALIFICACIÓN FINAL: [NEGATIVA]**" in resultado_auditoria:
                            resultado_auditoria = resultado_auditoria.replace(
                                "**CALIFICACIÓN FINAL: [NEGATIVA]**", 
                                "**CALIFICACIÓN FINAL: [POSITIVA]**"
                            )
                
                # Asegurar que la calificación esté presente y sea consistente en todos los campos
                datos_estructurados_bd['calificacion'] = calificacion
                datos_estructurados_bd['decision'] = calificacion
                datos_estructurados_bd['calificacion_final'] = calificacion
                
                # Log de confirmación final
                logger.info(f"CALIFICACIÓN FINAL QUE SERÁ GUARDADA EN LA BASE DE DATOS: {calificacion}")
                
                # Agregar un archivo de log adicional para facilitar el rastreo de las decisiones
                log_dir = os.path.join(BASE_DIR, "Logica_Log_Err")
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, "calificaciones_finales.log")
                
                with open(log_path, "a", encoding="utf-8") as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] Contrato: {num_contrato}, Calificación: {calificacion}\n")
                
                # Actualizar estado
                actualizar_estado_venta(num_contrato, calificacion)

                # Guardar resultado
                audit_file_path = LOG_SALES_AUDIT / f"{file_name}_auditoria.txt"
                with open(audit_file_path, 'w', encoding='utf-8') as audit_file:
                    audit_file.write(resultado_auditoria)

                # Guardar en base de datos con datos estructurados
                guardar_resultado_auditoria(resultado_auditoria, datos_estructurados_bd)

                gc.collect()
                logger.info(f"Procesamiento y auditoría completados exitosamente. Calificación: {calificacion}")

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