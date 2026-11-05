#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abstracción STT — Fase B (implementación gradual).

Variables de entorno:
  STT_PROVIDER   whisperx (default) | faster_whisper | google
  FASTER_WHISPER_MODEL, FASTER_WHISPER_DEVICE, FASTER_WHISPER_COMPUTE_TYPE (ver .env.example)
  GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_SPEECH_* (STT_PROVIDER=google)

whisperx: pipeline actual (GPU recomendada), usado vía diariza/unified_processing.
faster_whisper: CPU/VPS vía mod_bot/l_process/stt_faster_whisper.py (diarización limitada).
google: Cloud Speech-to-Text vía mod_bot/l_process/stt_google.py (credenciales GCP).
"""

from __future__ import annotations

import os

from .logger_config import logger


def get_stt_provider() -> str:
    return os.environ.get("STT_PROVIDER", "whisperx").strip().lower()


def procesar_audio_via_provider(audio_file: str):
    """Delega al backend STT configurado."""
    provider = get_stt_provider()
    if provider == "whisperx":
        from .audio_processing import procesar_audio

        return procesar_audio(audio_file)
    if provider == "faster_whisper":
        from .stt_faster_whisper import procesar_audio_faster_whisper

        return procesar_audio_faster_whisper(audio_file)
    if provider == "google":
        from .stt_google import procesar_audio_google

        return procesar_audio_google(audio_file)
    raise ValueError(f"STT_PROVIDER desconocido: {provider}")
