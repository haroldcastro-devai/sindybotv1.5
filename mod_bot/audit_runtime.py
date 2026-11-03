"""
Rutas de estado de auditoría por usuario y por ejecución (SCRUM-21).

- Cada auditoría remota usa un ``job_id`` (UUID) → ``temp/audit/<user>/<job>/``.
- ``remote_auditor`` debe arrancar con ``iniciar_proceso_remoto`` (contexto por hilo).
"""

import logging
import os
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)
_ctx = threading.local()


def safe_username(username: str) -> str:
    safe = "".join(c for c in username if c.isalnum() or c in ("_", "-", "."))[:64]
    return safe or "user"


def safe_job_id(job_id: str) -> str:
    safe = "".join(c for c in job_id if c.isalnum())[:32]
    return safe or "job"


def paths_for_user(
    base_dir: str, username: str, job_id: Optional[str] = None
) -> Dict[str, str]:
    temp_dir = os.path.join(base_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    safe = safe_username(username)

    if job_id:
        run_dir = os.path.join(temp_dir, "audit", safe, safe_job_id(job_id))
        os.makedirs(run_dir, exist_ok=True)
        return {
            "usuario": os.path.join(temp_dir, f"usuario_{safe}.txt"),
            "toast": os.path.join(run_dir, "toast.txt"),
            "cancel": os.path.join(run_dir, "cancel.txt"),
            "progress": os.path.join(run_dir, "progress.json"),
        }

    return {
        "usuario": os.path.join(temp_dir, f"usuario_{safe}.txt"),
        "toast": os.path.join(temp_dir, f"senal_toast_{safe}.txt"),
        "cancel": os.path.join(temp_dir, f"cancelar_{safe}.txt"),
        "progress": os.path.join(temp_dir, f"progreso_{safe}.json"),
    }


def set_audit_context(
    base_dir: str,
    username: Optional[str] = None,
    job_id: Optional[str] = None,
) -> None:
    """Contexto del hilo de auditoría remota."""
    _ctx.base_dir = base_dir
    _ctx.username = username
    _ctx.job_id = job_id


def clear_audit_context() -> None:
    for name in ("base_dir", "username", "job_id"):
        if hasattr(_ctx, name):
            delattr(_ctx, name)


def _active_paths(base_dir: str) -> Dict[str, str]:
    username = getattr(_ctx, "username", None)
    if not username:
        raise RuntimeError(
            "audit_runtime: falta contexto de usuario. "
            "Use iniciar_proceso_remoto() o set_audit_context(base_dir, username, job_id)."
        )
    job_id = getattr(_ctx, "job_id", None)
    return paths_for_user(base_dir, username, job_id)


def progress_file(base_dir: str) -> str:
    return _active_paths(base_dir)["progress"]


def cancel_file(base_dir: str) -> str:
    return _active_paths(base_dir)["cancel"]


def toast_file(base_dir: str) -> str:
    return _active_paths(base_dir)["toast"]

# Desarrollado por: hcastro
