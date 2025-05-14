#!/usr/bin/env python
# -*- coding: utf-8 -*-

import whisperx
import os
from datetime import timedelta
import gc
from pathlib import Path
from .logger_config import logger

def procesar_audio(audio_file: str) -> tuple:
    """
    Procesa el audio usando WhisperX para transcripción y diarización.
    
    Args:
        audio_file: Ruta al archivo de audio a procesar
        
    Returns:
        tuple: (texto_diarizado, nombre_archivo, resultado_procesamiento)
    """
    try:
        logger.info(f"Iniciando procesamiento de audio: {audio_file}")

        # Configuración
        device = "cuda"
        batch_size = 48
        compute_type = "float16"

        # Cargar modelo y procesar audio
        model = whisperx.load_model("large-v3", device, compute_type=compute_type)
        audio = whisperx.load_audio(audio_file)
        result = model.transcribe(audio, batch_size=batch_size, language="es")

        # Alineamiento
        model_a, metadata = whisperx.load_align_model(language_code="es", device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Diarización
        diarize_model = whisperx.DiarizationPipeline(use_auth_token="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", device=device)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)

        # Generar texto diarizado
        diarized_text = ""
        current_speaker = None
        for segment in result["segments"]:
            speaker = segment.get('speaker', 'Unknown Speaker')
            start_time = timedelta(seconds=segment['start'])
            end_time = timedelta(seconds=segment['end'])

            if speaker != current_speaker:
                diarized_text += f"\n[{speaker}]\n"
                current_speaker = speaker

            diarized_text += f"{start_time} - {end_time}: {segment['text']}\n"

        logger.info(f"Procesamiento de audio completado: {audio_file}")
        
        # Liberar memoria GPU
        del model, model_a, metadata, diarize_model
        gc.collect()
        
        return diarized_text, os.path.basename(audio_file), result

    except Exception as e:
        logger.error(f"Error en procesamiento de audio {audio_file}: {e}")
        raise

def analizar_hablantes(result: dict) -> dict:
    """
    Realiza un análisis detallado de los patrones de habla de cada participante.
    
    Args:
        result: Resultado del procesamiento de audio con diarización
        
    Returns:
        dict: Análisis detallado por hablante
    """
    try:
        hablantes = {}
        ultimo_speaker = None
        tiempo_total_llamada = 0
        last_end = 0  # Inicialización para evitar uso antes de asignación

        for segment in result["segments"]:
            speaker = segment.get('speaker', 'Unknown Speaker')
            duracion = segment['end'] - segment['start']
            palabras = len(segment['text'].split())
            tiempo_total_llamada += duracion

            if speaker not in hablantes:
                hablantes[speaker] = {
                    'tiempo_total': 0,
                    'palabras_total': 0,
                    'segmentos': 0,
                    'interrupciones': 0,
                    'velocidad_promedio': 0,
                    'pausas_largas': 0,
                    'palabras_por_intervencion': []
                }

            # Actualizar estadísticas básicas
            hablantes[speaker]['tiempo_total'] += duracion
            hablantes[speaker]['palabras_total'] += palabras
            hablantes[speaker]['segmentos'] += 1
            hablantes[speaker]['palabras_por_intervencion'].append(palabras)

            # Detectar interrupciones
            if ultimo_speaker and ultimo_speaker != speaker and duracion < 1.0:
                hablantes[speaker]['interrupciones'] += 1

            # Detectar pausas largas (> 2 segundos)
            if ultimo_speaker == speaker and segment['start'] - last_end > 2.0:
                hablantes[speaker]['pausas_largas'] += 1

            ultimo_speaker = speaker
            last_end = segment['end']

        # Calcular estadísticas adicionales
        for speaker, info in hablantes.items():
            if info['tiempo_total'] > 0:
                info['velocidad_promedio'] = info['palabras_total'] / info['tiempo_total']
                info['porcentaje_tiempo'] = (info['tiempo_total'] / tiempo_total_llamada) * 100
                info['promedio_palabras_intervencion'] = sum(info['palabras_por_intervencion']) / len(info['palabras_por_intervencion'])

        return hablantes

    except Exception as e:
        logger.error(f"Error en análisis de hablantes: {e}")
        return {}