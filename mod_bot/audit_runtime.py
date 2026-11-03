"""
Rutas de estado de auditoría por usuario (SCRUM-21).
Usado por home/views.py y remote_auditor.py.
"""

import os
import threading
from typing import Dict, Optional

_ctx = threading.local()


def safe_username(username: str) -> str:
    safe = "".join(c for c in username if c.isalnum() or c in ("_", "-", "."))[:64]
    return safe or "user"


def paths_for_user(base_dir: str, username: str) -> Dict[str, str]:
    temp_dir = os.path.join(base_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    safe = safe_username(username)
    return {
        "usuario": os.path.join(temp_dir, f"usuario_{safe}.txt"),
        "toast": os.path.join(temp_dir, f"senal_toast_{safe}.txt"),
        "cancel": os.path.join(temp_dir, f"cancelar_{safe}.txt"),
        "progress": os.path.join(temp_dir, f"progreso_{safe}.json"),
    }


def legacy_paths(base_dir: str) -> Dict[str, str]:
    log_dir = os.path.join(base_dir, "Logica_Log_Err")
    return {
        "toast": os.path.join(base_dir, "senal_toast.txt"),
        "cancel": os.path.join(base_dir, "cancelar_proceso.txt"),
        "progress": os.path.join(log_dir, "progreso_auditoria.json"),
    }


def set_audit_context(base_dir: str, username: Optional[str] = None) -> None:
    """Contexto del hilo de auditoría remota (evita mezclar usuarios concurrentes)."""
    _ctx.base_dir = base_dir
    _ctx.username = username


def clear_audit_context() -> None:
    for name in ("base_dir", "username"):
        if hasattr(_ctx, name):
            delattr(_ctx, name)


def _active_paths(base_dir: str) -> Dict[str, str]:
    username = getattr(_ctx, "username", None)
    if username:
        return paths_for_user(base_dir, username)
    return legacy_paths(base_dir)


def progress_file(base_dir: str) -> str:
    return _active_paths(base_dir)["progress"]


def cancel_file(base_dir: str) -> str:
    return _active_paths(base_dir)["cancel"]


def toast_file(base_dir: str) -> str:
    return _active_paths(base_dir)["toast"]

# Desarrollado por: hcastro
