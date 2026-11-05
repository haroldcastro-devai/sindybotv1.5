#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Transcripción STT con faster-whisper (CPU / VPS sin GPU).

Diarización limitada: un solo hablante (SPEAKER_00) por segmento.
No sustituye WhisperX+PyAnnote para separar vendedor/cliente en auditoría.

El modelo WhisperModel se cachea en memoria por (model, device, compute_type)
para lotes en diariza/unified_processing.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from threading import Lock

from .logger_config import logger

DEFAULT_SPEAKER = "SPEAKER_00"

_model_cache: dict[tuple[str, str, str], object] = {}
_model_lock = Lock()


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name, default).strip()
    return raw or default


def _env_beam_size(name: str, default: int = 5) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"{name} debe ser un entero, recibido: {raw!r}"
        ) from exc
    if value < 1 or value > 20:
        raise ValueError(f"{name} debe estar entre 1 y 20, recibido: {value}")
    return value


def _get_whisper_model(model_name: str, device: str, compute_type: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ImportError(
            "faster-whisper no instalado. Ejecute: "
            "pip install -r mod_bot/requirements-stt-cpu.txt"
        ) from exc

    key = (model_name, device, compute_type)
    with _model_lock:
        if key not in _model_cache:
            logger.info(
                "Cargando faster-whisper en cache: model=%s device=%s compute=%s",
                model_name,
                device,
                compute_type,
            )
            _model_cache[key] = WhisperModel(
                model_name, device=device, compute_type=compute_type
            )
        return _model_cache[key]


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

    model_name = _env_str("FASTER_WHISPER_MODEL", "small")
    device = _env_str("FASTER_WHISPER_DEVICE", "cpu")
    compute_type = _env_str("FASTER_WHISPER_COMPUTE_TYPE", "int8")
    beam_size = _env_beam_size("FASTER_WHISPER_BEAM_SIZE", 5)
    language = _env_str("FASTER_WHISPER_LANGUAGE", "es")

    logger.info(
        "faster-whisper: model=%s device=%s compute=%s lang=%s file=%s",
        model_name,
        device,
        compute_type,
        language,
        audio_file,
    )

    model = _get_whisper_model(model_name, device, compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=language,
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
