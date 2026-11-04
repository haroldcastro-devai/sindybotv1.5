"""
Middleware de rate limit en login web y admin (SCRUM-26).
"""

from django.http import HttpResponse

from home.login_rate_limit import is_login_rate_limited, record_login_attempt

_RATE_LIMIT_MESSAGE = (
    "Demasiados intentos de inicio de sesion. "
    "Espere unos minutos e intente de nuevo."
)


def _too_many_requests_response(request) -> HttpResponse:
    accept = request.META.get("HTTP_ACCEPT", "")
    if "text/html" in accept or request.path.startswith("/admin"):
        body = (
            "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
            "<title>Demasiados intentos</title></head><body>"
            f"<p>{_RATE_LIMIT_MESSAGE}</p></body></html>"
        )
        return HttpResponse(body, status=429, content_type="text/html; charset=utf-8")
    return HttpResponse(
        _RATE_LIMIT_MESSAGE,
        status=429,
        content_type="text/plain; charset=utf-8",
    )


class LoginRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_login_rate_limited(request):
            return _too_many_requests_response(request)
        response = self.get_response(request)
        record_login_attempt(request, response)
        return response

# Desarrollado por: hcastro
