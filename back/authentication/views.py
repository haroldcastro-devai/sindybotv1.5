from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Definir las clases originales manteniendo sus nombres

class LoginView(LoginView):
    template_name = 'accounts/auth-signin.html'

class RegisterView(CreateView):
    template_name = 'accounts/auth-signup.html'
    # Completa esta clase según tu implementación actual

class UserProfileView(View):
    # Completa esta clase según tu implementación actual
    pass

# Modificar la clase LogoutView para aceptar peticiones GET
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')
    
    def post(self, request):
        logout(request)
        return redirect('login')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido actualizada con éxito.')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})