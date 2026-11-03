"""core URL Configuration"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from home.views import index, protected_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/auth-signin/', LoginView.as_view(template_name='accounts/auth-signin.html'), name='login'),
    path('accounts/', include('authentication.urls')),
    path('', login_required(index), name='index'),
    path('', include('home.urls')),
    path('media/<path:path>', protected_media, name='protected_media'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
