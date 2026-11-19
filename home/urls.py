from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Vistas web tradicionales
    path('config/', login_required(views.config), name='config'),
    path('seleccionar_directorio/', login_required(views.seleccionar_directorio), name='seleccionar_directorio'),
    path('validar_directorio_audios/', login_required(views.validar_directorio_audios), name='validar_directorio_audios'),
    path('guardar_ruta_directorio/', login_required(views.guardar_ruta_directorio), name='guardar_ruta_directorio'),
    path('abrir_ubicacion/', login_required(views.abrir_ubicacion), name='abrir_ubicacion'),
    path('iniciar_auditoria_remota/', login_required(views.iniciar_auditoria_remota), name='iniciar_auditoria_remota'),
    path('ver_senal_toast/', login_required(views.ver_senal_toast), name='ver_senal_toast'),
    path('ver_progreso_auditoria/', login_required(views.ver_progreso_auditoria), name='ver_progreso_auditoria'),
    path('cancelar_auditoria/', login_required(views.cancelar_auditoria), name='cancelar_auditoria'),
    path('descargar_reporte/', login_required(views.descargar_reporte), name='descargar_reporte'),
    path('obtener_datos_grafica/', login_required(views.obtener_datos_grafica), name='obtener_datos_grafica'),
    path('descargar-registros-fecha/<str:fecha>/', login_required(views.descargar_registros_fecha), name='descargar_registros_fecha'),
    path('logout/', views.logout_view, name='logout'),
    # API REST dashboard (SCRUM-20) — alineado con static/assets/js/api/config.js
    path('api/dashboard/stats/', views.DashboardStatsAPIView.as_view(), name='api_dashboard_stats'),
    path('api/dashboard/graph-data/', views.GraphDataAPIView.as_view(), name='api_dashboard_graph'),
    path('api/activity-log/', views.ActivityLogAPIView.as_view(), name='api_activity_log'),
    path('api/generate-report/', views.generate_report, name='api_generate_report'),
]
