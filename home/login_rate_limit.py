"""
Rate limiting para intentos de login (SCRUM-26).
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache

LOGIN_POST_PATHS = frozenset(
    {
        "/accounts/auth-signin/",
        "/accounts/login/",
        "/admin/login/",
    }
)


def _client_ip(request) -> str:
    if getattr(settings, "TRUST_X_FORWARDED_PROTO", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _limits():
    max_attempts = int(getattr(settings, "SINDYBOT_LOGIN_RATE_LIMIT", 10))
    window = int(getattr(settings, "SINDYBOT_LOGIN_RATE_WINDOW", 300))
    return max(1, max_attempts), max(60, window)


def login_path_is_rate_limited(path: str) -> bool:
    normalized = path if path.endswith("/") else f"{path}/"
    return normalized in LOGIN_POST_PATHS


def is_login_rate_limited(request) -> bool:
    if request.method != "POST":
        return False
    if not login_path_is_rate_limited(request.path):
        return False
    max_attempts, _window = _limits()
    key = f"sindybot:login_rl:{_client_ip(request)}"
    try:
        count = cache.get(key, 0)
    except Exception:
        return False
    return int(count) >= max_attempts


def record_login_attempt(request, response) -> None:
    if request.method != "POST":
        return
    if not login_path_is_rate_limited(request.path):
        return
    if response.status_code == 302:
        location = (response.get("Location") or "").lower()
        if "login" not in location:
            return
    _, window = _limits()
    key = f"sindybot:login_rl:{_client_ip(request)}"
    try:
        if cache.add(key, 1, window):
            return
        cache.incr(key)
    except Exception:
        cache.set(key, 1, window)

# Desarrollado por: hcastro
