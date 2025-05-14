from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Vistas web tradicionales
    path('config/', login_required(views.config), name='config'),
    path('seleccionar_directorio/', login_required(views.seleccionar_directorio), name='seleccionar_directorio'),
    path('guardar_ruta_directorio/', login_required(views.guardar_ruta_directorio), name='guardar_ruta_directorio'),
    path('abrir_ubicacion/', login_required(views.abrir_ubicacion), name='abrir_ubicacion'),
    path('descargar_reporte/', login_required(views.descargar_reporte), name='descargar_reporte'),
    path('obtener_datos_grafica/', login_required(views.obtener_datos_grafica), name='obtener_datos_grafica'),
    path('descargar-registros-fecha/<str:fecha>/', login_required(views.descargar_registros_fecha), name='descargar_registros_fecha'),
    path('logout/', views.logout_view, name='logout'),
]