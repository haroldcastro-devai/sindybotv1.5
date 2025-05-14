"""core URL Configuration"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from home.views import index

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/auth-signin/', LoginView.as_view(template_name='accounts/auth-signin.html'), name='login'),
    #path('accounts/', include('django.contrib.auth.urls')),    
   
       
    # Main URLs
    path('accounts/', include('authentication.urls')),
    path('', login_required(index), name='index'),
    path('', include('admin_gradient.urls')),
    path('', include('home.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)