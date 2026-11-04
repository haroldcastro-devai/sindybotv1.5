#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auditoría vía Google Gemini API (SDK `google-genai`, sin LLM local).

Variables: GEMINI_API_KEY, GEMINI_MODEL (default gemini-3.8-flash).

---
SindyBot v1.5 — SCRUM-33 Gemini-only
Harold Castro (hcastro)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .logger_config import logger

_ENV_LOADED = False
_GEMINI_CLIENT = None
_GEMINI_CLIENT_KEY: Optional[str] = None


def _ensure_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env", override=False)
    _ENV_LOADED = True


def _get_gemini_client(api_key: str):
    global _GEMINI_CLIENT, _GEMINI_CLIENT_KEY
    from google import genai

    if _GEMINI_CLIENT is None or _GEMINI_CLIENT_KEY != api_key:
        _GEMINI_CLIENT = genai.Client(api_key=api_key)
        _GEMINI_CLIENT_KEY = api_key
    return _GEMINI_CLIENT


def _response_text_or_raise(response) -> str:
    text = (getattr(response, "text", None) or "").strip()
    if text:
        return text
    detail_parts = []
    feedback = getattr(response, "prompt_feedback", None)
    if feedback:
        detail_parts.append(str(feedback))
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        finish = getattr(candidates[0], "finish_reason", None)
        if finish:
            detail_parts.append(f"finish_reason={finish}")
    detail = "; ".join(detail_parts) or "desconocido"
    raise ValueError(
        f"Gemini devolvió respuesta vacía (safety, cuota o modelo: {detail})"
    )


def generate_from_prompt(
    prompt: str,
    *,
    temperature: float = 0.3,
    max_output_tokens: int = 8192,
) -> str:
    _ensure_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY no configurada. Copia .env.example a .env y añade tu clave."
        )

    from google.genai import types

    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
    logger.info("Generando auditoría con Gemini (%s)", model_name)

    client = _get_gemini_client(api_key)
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            return _response_text_or_raise(response)
        except Exception as exc:
            last_error = exc
            logger.error("Intento %s Gemini fallido: %s", attempt + 1, exc)
    raise RuntimeError(f"Gemini falló tras 3 intentos: {last_error}") from last_error

# Desarrollado por: hcastro
