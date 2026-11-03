from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario personalizado para cambio de contraseña con placeholders y clases CSS.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadir placeholders y clases a los campos
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual',
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva contraseña',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña',
        })
        
        # También podemos personalizar los mensajes de ayuda si es necesario
        self.fields['new_password1'].help_text = None  # Eliminar mensaje de ayuda complejo


class UserRegistrationForm(UserCreationForm):
    """Alta de usuario cuando ALLOW_PUBLIC_REGISTRATION=True."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
