#!/usr/bin/env python
"""Smoke test Gemini API (google-genai) — ver Docs--Readme/IA-STT-ARQUITECTURA.md (LLM)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mod_bot"))

from l_process.llm_client import generate_from_prompt  # noqa: E402

if __name__ == "__main__":
    reply = generate_from_prompt("Responde una sola palabra: OK")
    print("Smoke Gemini:", reply.strip()[:200])

# Desarrollado por: hcastro
