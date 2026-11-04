#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Transcripción STT con faster-whisper (CPU / VPS sin GPU).

Diarización limitada: un solo hablante (SPEAKER_00) por segmento.
Compatible con analizar_hablantes() y el formato de whisperx.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from .logger_config import logger

DEFAULT_SPEAKER = "SPEAKER_00"


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name, default).strip()
    return raw or default


def _segments_to_result(segments) -> dict:
    result_segments = []
    for seg in segments:
        result_segments.append(
            {
                "start": float(seg.start),
                "end": float(seg.end),
                "text": (seg.text or "").strip(),
                "speaker": DEFAULT_SPEAKER,
            }
        )
    return {"segments": result_segments, "stt_backend": "faster_whisper"}


def _format_diarized_text(result: dict) -> str:
    diarized_text = ""
    current_speaker = None
    for segment in result["segments"]:
        speaker = segment.get("speaker", DEFAULT_SPEAKER)
        start_time = timedelta(seconds=segment["start"])
        end_time = timedelta(seconds=segment["end"])
        if speaker != current_speaker:
            diarized_text += f"\n[{speaker}]\n"
            current_speaker = speaker
        diarized_text += f"{start_time} - {end_time}: {segment['text']}\n"
    return diarized_text


def procesar_audio_faster_whisper(audio_file: str) -> tuple:
    """
    Transcribe audio con faster-whisper.

    Returns:
        tuple: (texto_diarizado, nombre_archivo, resultado dict con segments)
    """
    audio_path = Path(audio_file)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio no encontrado: {audio_file}")

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ImportError(
            "faster-whisper no instalado. Ejecute: "
            "pip install -r mod_bot/requirements-stt-cpu.txt"
        ) from exc

    model_name = _env_str("FASTER_WHISPER_MODEL", "small")
    device = _env_str("FASTER_WHISPER_DEVICE", "cpu")
    compute_type = _env_str("FASTER_WHISPER_COMPUTE_TYPE", "int8")
    beam_size = int(os.environ.get("FASTER_WHISPER_BEAM_SIZE", "5"))

    logger.info(
        "faster-whisper: model=%s device=%s compute=%s file=%s",
        model_name,
        device,
        compute_type,
        audio_file,
    )

    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language="es",
        beam_size=beam_size,
        vad_filter=True,
    )
    segments = list(segments_iter)
    logger.info(
        "faster-whisper completado: %s segmentos, duracion=%.1fs",
        len(segments),
        getattr(info, "duration", 0.0) or 0.0,
    )

    result = _segments_to_result(segments)
    diarized_text = _format_diarized_text(result)
    return diarized_text, audio_path.name, result

# Desarrollado por: hcastro
