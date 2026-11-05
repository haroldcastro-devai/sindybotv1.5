#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verifica que el pipeline STT no llame a procesar_audio fuera de stt_provider (SCRUM-36).

Uso (desde raiz sindybotv1.5):
  python scripts/verify_stt_provider_wiring.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_BOT = ROOT / "mod_bot"

ALLOWED_CALLER = MOD_BOT / "l_process" / "stt_provider.py"
ENTRYPOINTS = (
    MOD_BOT / "diariza.py",
    MOD_BOT / "l_process" / "unified_processing.py",
)

FORBIDDEN_IMPORT = re.compile(
    r"from\s+\.?\.?l_process\.audio_processing\s+import\s+.*\bprocesar_audio\b"
    r"|from\s+\.audio_processing\s+import\s+.*\bprocesar_audio\b"
)
REQUIRED_IMPORT = re.compile(
    r"from\s+\.?\.?l_process\.stt_provider\s+import\s+.*\bprocesar_audio_via_provider\b"
    r"|from\s+\.stt_provider\s+import\s+.*\bprocesar_audio_via_provider\b"
)
DIRECT_CALL = re.compile(r"(?<![\w.])procesar_audio\s*\(")


def _scan_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    if FORBIDDEN_IMPORT.search(text):
        issues.append(f"{path.relative_to(ROOT)}: import directo de procesar_audio")
    if path in ENTRYPOINTS:
        if not REQUIRED_IMPORT.search(text):
            issues.append(
                f"{path.relative_to(ROOT)}: falta import de procesar_audio_via_provider"
            )
        for match in DIRECT_CALL.finditer(text):
            start = max(0, match.start() - 40)
            snippet = text[start : match.start() + 20]
            if "procesar_audio_via_provider" in snippet:
                continue
            if "procesar_audio_dividido" in snippet:
                continue
            issues.append(
                f"{path.relative_to(ROOT)}: llamada directa a procesar_audio()"
            )
            break
    return issues


def main() -> int:
    issues: list[str] = []
    for py in MOD_BOT.rglob("*.py"):
        if py == ALLOWED_CALLER:
            continue
        issues.extend(_scan_file(py))
    if issues:
        print("verify_stt_provider_wiring: FALLO")
        for line in issues:
            print(f"  - {line}")
        return 1
    print("verify_stt_provider_wiring: OK (entrypoints usan stt_provider)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Desarrollado por: hcastro
