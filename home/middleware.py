from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect

class AdminRedirectMiddleware(MiddlewareMixin):
    """
    Middleware para interceptar y redirigir rutas específicas del admin
    a las páginas equivalentes para usuarios regulares.
    """
    def process_request(self, request):
        # Redirigir logout del admin
        if request.path == '/admin/logout/':
            return redirect('/logout/')
            
        # Redirigir cambio de contraseña del admin
        elif request.path == '/admin/password_change/':
            return redirect('/accounts/password-change/')
            
        # Redirigir página de "cambio de contraseña exitoso" del admin
        elif request.path == '/admin/password_change/done/':
            return redirect('/accounts/password-change-done/')
            
        return None