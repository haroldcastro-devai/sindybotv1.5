from django.contrib.auth.views import LoginView, LogoutView as AuthLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

from django.urls import reverse_lazy

from .forms import CustomPasswordChangeForm, UserRegistrationForm

# ---
# SindyBot v1.5 — auth endurecida (SCRUM-15/16)
# Harold Castro (hcastro)


class LoginView(LoginView):
    template_name = 'accounts/auth-signin.html'


class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/auth-signup.html'
    success_url = reverse_lazy('login')


class UserProfileView(LoginRequiredMixin, TemplateView):
    """Perfil basico del usuario autenticado (SCRUM-27)."""

    template_name = "accounts/profile.html"


class LogoutView(AuthLogoutView):
    """Cierre de sesión solo vía POST (CSRF)."""

    http_method_names = ["post", "options"]
    next_page = "/accounts/auth-signin/"


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido actualizada con éxito.')
            return redirect('profile')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
