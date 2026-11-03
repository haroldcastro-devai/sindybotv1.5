from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

# ---
# SindyBot v1.5 — logout admin sin GET abierto (SCRUM-16)
# Harold Castro (hcastro)


class AdminRedirectMiddleware(MiddlewareMixin):
    """
    Middleware para interceptar y redirigir rutas específicas del admin
    a las páginas equivalentes para usuarios regulares.
    """
    def process_request(self, request):
        # /admin/logout/ con GET permitía logout CSRF; solo POST cierra sesión.
        if request.path == '/admin/logout/':
            if request.method == 'POST':
                logout(request)
            return redirect('/accounts/auth-signin/')

        # Redirigir cambio de contraseña del admin
        elif request.path == '/admin/password_change/':
            return redirect('/accounts/password-change/')
            
        # Redirigir página de "cambio de contraseña exitoso" del admin
        elif request.path == '/admin/password_change/done/':
            return redirect('/accounts/password-change-done/')
            
        return None