#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
STT con Google Cloud Speech-to-Text (API v1) — prototipo Fase B.

Requiere GOOGLE_APPLICATION_CREDENTIALS (cuenta de servicio) y API Speech habilitada.
Diarización opcional vía SpeakerDiarizationConfig (coste adicional por minuto).

Coste orientativo (consulte precios GCP vigentes): facturación por duración de audio
procesada; la diarización suele tener recargo respecto a transcripción estándar.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from datetime import timedelta
from pathlib import Path
from threading import Lock

from .logger_config import logger

_client_lock = Lock()
_speech_client = None

_INLINE_MAX_BYTES = 10 * 1024 * 1024


def _env_str(name: str, default: str) -> str:
    raw = os.environ.get(name, default).strip()
    return raw or default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int, *, min_val: int, max_val: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser entero, recibido: {raw!r}") from exc
    if value < min_val or value > max_val:
        raise ValueError(f"{name} debe estar entre {min_val} y {max_val}, recibido: {value}")
    return value


def _get_speech_client():
    global _speech_client
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS no definido. "
            "Apunte a un JSON de cuenta de servicio con Speech-to-Text."
        )
    try:
        from google.cloud import speech_v1 as speech
    except ImportError as exc:
        raise ImportError(
            "google-cloud-speech no instalado. "
            "pip install -r mod_bot/requirements-stt-google.txt"
        ) from exc

    with _client_lock:
        if _speech_client is None:
            _speech_client = speech.SpeechClient()
        return _speech_client, speech


def _convert_to_wav_16k_mono(source: Path) -> Path:
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    out.close()
    dest = Path(out.name)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffmpeg no encontrado en PATH; necesario para convertir audio a WAV 16 kHz."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffmpeg fallo al convertir {source}: {exc.stderr or exc}"
        ) from exc
    return dest


def _load_linear16_wav(path: Path) -> tuple[bytes, int]:
    suffix = path.suffix.lower()
    wav_path = path
    temp_wav: Path | None = None
    if suffix not in (".wav",):
        temp_wav = _convert_to_wav_16k_mono(path)
        wav_path = temp_wav
    try:
        data = wav_path.read_bytes()
    finally:
        if temp_wav and temp_wav.exists():
            temp_wav.unlink(missing_ok=True)
    if len(data) > _INLINE_MAX_BYTES:
        raise ValueError(
            f"Audio supera {_INLINE_MAX_BYTES // (1024*1024)} MB inline; "
            "use GCS + URI en una fase posterior o acorte el archivo."
        )
    return data, 16000


def _speaker_label(tag: int) -> str:
    if tag <= 0:
        return "SPEAKER_00"
    return f"SPEAKER_{tag - 1:02d}"


def _word_seconds(word) -> tuple[float, float]:
    start = word.start_time.seconds + word.start_time.microseconds / 1_000_000
    end = word.end_time.seconds + word.end_time.microseconds / 1_000_000
    return start, end


def _build_segments_from_words(words) -> list[dict]:
    if not words:
        return []
    segments: list[dict] = []
    current_speaker = _speaker_label(words[0].speaker_tag)
    seg_start, _ = _word_seconds(words[0])
    texts = [words[0].word]
    last_end = _word_seconds(words[0])[1]

    for word in words[1:]:
        speaker = _speaker_label(word.speaker_tag)
        w_start, w_end = _word_seconds(word)
        if speaker != current_speaker:
            segments.append(
                {
                    "start": seg_start,
                    "end": last_end,
                    "text": " ".join(texts).strip(),
                    "speaker": current_speaker,
                }
            )
            current_speaker = speaker
            seg_start = w_start
            texts = [word.word]
        else:
            texts.append(word.word)
        last_end = w_end

    segments.append(
        {
            "start": seg_start,
            "end": last_end,
            "text": " ".join(texts).strip(),
            "speaker": current_speaker,
        }
    )
    return segments


def _build_segments_from_transcript(results) -> list[dict]:
    """Fallback sin diarización por palabra: un segmento por alternativa."""
    segments = []
    for result in results:
        if not result.alternatives:
            continue
        alt = result.alternatives[0]
        text = (alt.transcript or "").strip()
        if not text:
            continue
        start = 0.0
        end = 0.0
        if alt.words:
            start, _ = _word_seconds(alt.words[0])
            _, end = _word_seconds(alt.words[-1])
        segments.append(
            {
                "start": start,
                "end": end,
                "text": text,
                "speaker": "SPEAKER_00",
            }
        )
    return segments


def _format_diarized_text(segments: list[dict]) -> str:
    diarized_text = ""
    current_speaker = None
    for segment in segments:
        speaker = segment.get("speaker", "SPEAKER_00")
        start_time = timedelta(seconds=segment["start"])
        end_time = timedelta(seconds=segment["end"])
        if speaker != current_speaker:
            diarized_text += f"\n[{speaker}]\n"
            current_speaker = speaker
        diarized_text += f"{start_time} - {end_time}: {segment['text']}\n"
    return diarized_text


def _recognize(client, speech, audio_bytes: bytes, sample_rate: int):
    language = _env_str("GOOGLE_SPEECH_LANGUAGE_CODE", "es-CO")
    enable_diar = _env_bool("GOOGLE_SPEECH_ENABLE_DIARIZATION", True)
    min_sp = _env_int("GOOGLE_SPEECH_MIN_SPEAKERS", 2, min_val=1, max_val=6)
    max_sp = _env_int("GOOGLE_SPEECH_MAX_SPEAKERS", 2, min_val=1, max_val=6)
    if min_sp > max_sp:
        raise ValueError(
            "GOOGLE_SPEECH_MIN_SPEAKERS no puede ser mayor que GOOGLE_SPEECH_MAX_SPEAKERS"
        )

    config_kwargs = {
        "encoding": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "sample_rate_hertz": sample_rate,
        "language_code": language,
        "enable_automatic_punctuation": True,
        "model": "latest_long",
    }
    if enable_diar:
        config_kwargs["diarization_config"] = speech.SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=min_sp,
            max_speaker_count=max_sp,
        )

    config = speech.RecognitionConfig(**config_kwargs)
    audio = speech.RecognitionAudio(content=audio_bytes)

    logger.info(
        "Google STT: lang=%s diar=%s min_sp=%s max_sp=%s bytes=%s",
        language,
        enable_diar,
        min_sp,
        max_sp,
        len(audio_bytes),
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=3600)
    return list(response.results)


def procesar_audio_google(audio_file: str) -> tuple:
    """
    Transcribe con Google Cloud Speech-to-Text.

    Returns:
        tuple: (texto_diarizado, nombre_archivo, dict con segments)
    """
    audio_path = Path(audio_file)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio no encontrado: {audio_file}")

    client, speech = _get_speech_client()
    audio_bytes, sample_rate = _load_linear16_wav(audio_path)
    results = _recognize(client, speech, audio_bytes, sample_rate)

    enable_diar = _env_bool("GOOGLE_SPEECH_ENABLE_DIARIZATION", True)
    words = []
    if results:
        last = results[-1]
        if last.alternatives and last.alternatives[0].words:
            words = list(last.alternatives[0].words)

    if enable_diar and words:
        segments = _build_segments_from_words(words)
    else:
        segments = _build_segments_from_transcript(results)

    result = {"segments": segments, "stt_backend": "google_speech"}
    diarized_text = _format_diarized_text(segments)
    logger.info("Google STT completado: %s segmentos", len(segments))
    return diarized_text, audio_path.name, result

# Desarrollado por: hcastro
