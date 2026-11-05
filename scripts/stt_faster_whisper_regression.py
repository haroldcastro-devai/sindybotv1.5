#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Regresión STT faster-whisper (SCRUM-34): transcribe hasta 3 audios de referencia.

Uso (desde raiz sindybotv1.5, con venv + requirements-stt-cpu.txt):

  set STT_PROVIDER=faster_whisper
  python scripts/stt_faster_whisper_regression.py ruta1.mp3 ruta2.gsm ruta3.wav

Los archivos no se versionan en Git; use muestras locales de ventas de prueba.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mod_bot"))

os.environ.setdefault("STT_PROVIDER", "faster_whisper")

from l_process.logger_config import configure_logging, logger  # noqa: E402
from l_process.stt_provider import procesar_audio_via_provider  # noqa: E402


def main() -> int:
    configure_logging()
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print(
            "Indique 1 a 3 rutas de audio. Ejemplo:\n"
            "  python scripts/stt_faster_whisper_regression.py audio1.mp3 audio2.mp3"
        )
        return 1
    if len(paths) > 3:
        print("Maximo 3 audios de referencia (SCRUM-34).")
        return 1

    ok = 0
    for path in paths:
        if not path.is_file():
            logger.error("No existe: %s", path)
            continue
        try:
            text, name, result = procesar_audio_via_provider(str(path))
            n_seg = len(result.get("segments", []))
            preview = (text or "").strip().replace("\n", " ")[:120]
            logger.info(
                "OK %s: %s segmentos, preview=%r",
                name,
                n_seg,
                preview,
            )
            ok += 1
        except Exception as exc:
            logger.error("FALLO %s: %s", path, exc)

    if ok == len(paths):
        print(f"Regresion faster-whisper: OK ({ok}/{len(paths)})")
        return 0
    print(f"Regresion faster-whisper: {ok}/{len(paths)} archivos OK")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

# Desarrollado por: hcastro
