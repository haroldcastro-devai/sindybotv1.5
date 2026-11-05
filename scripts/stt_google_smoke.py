#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke Google STT (SCRUM-35): transcribe un audio con STT_PROVIDER=google."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mod_bot"))

os.environ.setdefault("STT_PROVIDER", "google")

from l_process.logger_config import configure_logging, logger  # noqa: E402
from l_process.stt_provider import procesar_audio_via_provider  # noqa: E402


def main() -> int:
    configure_logging()
    if len(sys.argv) != 2:
        print("Uso: python scripts/stt_google_smoke.py <archivo-audio>")
        return 1
    path = Path(sys.argv[1])
    if not path.is_file():
        logger.error("No existe: %s", path)
        return 1
    text, name, result = procesar_audio_via_provider(str(path))
    n = len(result.get("segments", []))
    preview = (text or "").strip().replace("\n", " ")[:160]
    print(f"Smoke Google STT OK: {name} ({n} segmentos) preview={preview!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Desarrollado por: hcastro
