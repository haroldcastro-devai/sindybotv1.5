#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abstracción STT — Fase B (implementación gradual).

Variables de entorno:
  STT_PROVIDER   whisperx (default) | faster_whisper | google

whisperx: pipeline actual (GPU recomendada), usado vía diariza/unified_processing.
faster_whisper / google: por implementar (Fase B); error explícito si se eligen.
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
        raise NotImplementedError(
            "STT_PROVIDER=faster_whisper pendiente (Fase B). Ver GEMINI-STT-MIGRATION.md"
        )
    if provider == "google":
        raise NotImplementedError(
            "STT_PROVIDER=google pendiente (Fase B). Ver GEMINI-STT-MIGRATION.md"
        )
    raise ValueError(f"STT_PROVIDER desconocido: {provider}")
