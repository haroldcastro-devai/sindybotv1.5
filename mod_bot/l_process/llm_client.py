#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Auditoría vía Google Gemini API (sin LLM local).

Variables: GEMINI_API_KEY, GEMINI_MODEL (default gemini-2.0-flash).

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


def _ensure_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env", override=False)
    _ENV_LOADED = True


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

    import google.generativeai as genai

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    logger.info("Generando auditoría con Gemini (%s)", model_name)

    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            if not response.text:
                raise ValueError("Gemini devolvió respuesta vacía")
            return response.text
        except Exception as exc:
            last_error = exc
            logger.error("Intento %s Gemini fallido: %s", attempt + 1, exc)
    raise RuntimeError(f"Gemini falló tras 3 intentos: {last_error}") from last_error
