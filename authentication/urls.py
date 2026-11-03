from django.conf import settings
from django.urls import path

from .views import (
    LoginView,
    RegisterView,
    LogoutView,
    UserProfileView,
    change_password,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', change_password, name='change_password'),
    path('password-change/', change_password, name='password_change'),
]

if getattr(settings, 'ALLOW_PUBLIC_REGISTRATION', False):
    urlpatterns.insert(1, path('register/', RegisterView.as_view(), name='register'))
