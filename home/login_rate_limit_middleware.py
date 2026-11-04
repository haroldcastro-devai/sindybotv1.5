"""
Middleware de rate limit en login web y admin (SCRUM-26).
"""

from django.http import HttpResponse

from home.login_rate_limit import is_login_rate_limited, record_login_attempt


class LoginRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_login_rate_limited(request):
            return HttpResponse(
                "Demasiados intentos de inicio de sesion. "
                "Espere unos minutos e intente de nuevo.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
        response = self.get_response(request)
        record_login_attempt(request, response)
        return response

# Desarrollado por: hcastro
