#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verifica que el pipeline STT no llame a procesar_audio fuera de stt_provider (SCRUM-36).

Guarda estatica (regex): no detecta eval/exec ni codigo fuera de mod_bot/.
Amplie patrones si aparecen bypass (import alias + ap.procesar_audio).

Uso (desde raiz sindybotv1.5):
  python scripts/verify_stt_provider_wiring.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_BOT = ROOT / "mod_bot"

ALLOWED_CALLER = MOD_BOT / "l_process" / "stt_provider.py"
DEFINITION_FILES = frozenset(
    {
        MOD_BOT / "l_process" / "audio_processing.py",
        MOD_BOT / "l_process" / "stt_faster_whisper.py",
        MOD_BOT / "l_process" / "stt_google.py",
    }
)
ENTRYPOINTS = (
    MOD_BOT / "diariza.py",
    MOD_BOT / "l_process" / "unified_processing.py",
)

FORBIDDEN_IMPORT = re.compile(
    r"from\s+\.?\.?l_process\.audio_processing\s+import\s+.*\bprocesar_audio\b"
    r"|from\s+\.audio_processing\s+import\s+.*\bprocesar_audio\b"
    r"|import\s+l_process\.audio_processing\s+as\s+\w+"
    r"|from\s+l_process\s+import\s+audio_processing\s+as\s+\w+"
)
REQUIRED_IMPORT = re.compile(
    r"from\s+\.?\.?l_process\.stt_provider\s+import\s+.*\bprocesar_audio_via_provider\b"
    r"|from\s+\.stt_provider\s+import\s+.*\bprocesar_audio_via_provider\b"
)
DIRECT_CALL = re.compile(r"(?<![\w.])procesar_audio\s*\(")
INDIRECT_CALL = re.compile(
    r"(?<![\w.])audio_processing\.procesar_audio\s*\("
    r"|(?<!\w)\w+\.procesar_audio\s*\("
)


def _is_allowed_procesar_audio_call(snippet: str) -> bool:
    if "procesar_audio_via_provider" in snippet:
        return True
    if "procesar_audio_dividido" in snippet:
        return True
    if "procesar_audio_faster_whisper" in snippet:
        return True
    if "procesar_audio_google" in snippet:
        return True
    return False


def _scan_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)

    if FORBIDDEN_IMPORT.search(text):
        issues.append(f"{rel}: import de audio_processing orientado a bypass STT")

    if path not in DEFINITION_FILES:
        for pattern, label in (
            (DIRECT_CALL, "procesar_audio()"),
            (INDIRECT_CALL, "llamada indirecta a procesar_audio()"),
        ):
            for match in pattern.finditer(text):
                start = max(0, match.start() - 50)
                snippet = text[start : match.start() + 30]
                if _is_allowed_procesar_audio_call(snippet):
                    continue
                if "def procesar_audio" in snippet:
                    continue
                issues.append(f"{rel}: {label}")
                break

    if path in ENTRYPOINTS:
        if not REQUIRED_IMPORT.search(text):
            issues.append(f"{rel}: falta import de procesar_audio_via_provider")

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
