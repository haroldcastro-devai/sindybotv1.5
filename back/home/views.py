from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
from .models import TbRegAudio, TbRegActividad
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Q, Case, When, F, FloatField, Sum
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from itertools import groupby
from operator import attrgetter
import subprocess
import threading
from decimal import Decimal, InvalidOperation
import pandas as pd
import os
from django.conf import settings
from django.utils import timezone
import tempfile
import logging
import json
from datetime import datetime, timedelta

from django.contrib.auth import logout
from django.shortcuts import redirect



@login_required
def logout_view(request):
    """
    Vista personalizada para cerrar sesión.
    Funciona tanto para usuarios normales como para administradores.
    """
    logout(request)
    return redirect('/accounts/auth-signin/')




logger = logging.getLogger(__name__)

@login_required
def index(request):
    """
    Vista principal que muestra el dashboard con todos los datos
    """
    # Configuración de paginación
    items_per_page = 1000  # Aumentamos el número de items por página
    page_number = request.GET.get('page', 1)
    
    # Obtener todos los registros ordenados por fecha
    queryset = TbRegAudio.objects.all().order_by('-reg_fecha').select_related()
    
    # Aplicar paginación
    paginator = Paginator(queryset, items_per_page)
    tb_reg_audio = paginator.get_page(page_number)

    # Contadores para las tarjetas (usando cache si es posible)
    total_records = TbRegAudio.objects.count()
    ventas_positivasaud = TbRegAudio.objects.filter(reg_estado_venta__iexact='POSITIVA').count()
    ventas_negativasaud = TbRegAudio.objects.filter(reg_estado_venta__iexact='NEGATIVA').count()

    # Obtener ventas positivas y negativas (optimizado)
    ventas_positivas = TbRegAudio.objects.filter(
        reg_estado_venta__iexact='POSITIVA'
    ).order_by('-reg_fecha')[:items_per_page]
    
    ventas_negativas = TbRegAudio.objects.filter(
        reg_estado_venta__iexact='NEGATIVA'
    ).order_by('-reg_fecha')[:items_per_page]

    context = {
        'tbRegAudio': tb_reg_audio,
        'total_records': total_records,
        'show_chart': True,
        'ventas_positivasaud': ventas_positivasaud,
        'ventas_negativasaud': ventas_negativasaud,
        'ventas_positivas': ventas_positivas,
        'ventas_negativas': ventas_negativas,
        'page_obj': tb_reg_audio,  # Para la paginación en el template
    }

    return render(request, 'pages/index.html', context)


@login_required
def descargar_registros_fecha(request, fecha):
    """
    Vista para descargar registros de una fecha específica
    """
    try:
        # Convertir la fecha string a datetime
        fecha_obj = datetime.strptime(fecha.split('-feedback')[0], '%Y-%m-%d')

        # Verificar si es una solicitud de feedback
        es_feedback = '-feedback' in fecha

        # Filtrar registros por fecha usando __date
        registros = TbRegAudio.objects.filter(
            reg_fecha__year=fecha_obj.year,
            reg_fecha__month=fecha_obj.month,
            reg_fecha__day=fecha_obj.day
        ).values()

        # Crear DataFrame
        df = pd.DataFrame.from_records(registros)

        if df.empty:
            return HttpResponse("No hay registros para esta fecha", status=404)

        # Generar nombre del archivo
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        tipo_reporte = "feedback" if es_feedback else "registros"
        filename = f"{tipo_reporte}_{fecha_obj.strftime('%Y%m%d')}_{timestamp}.xlsx"

        # Crear archivo Excel en memoria
        with tempfile.TemporaryDirectory() as tmpdirname:
            filepath = os.path.join(tmpdirname, filename)

            # Seleccionar columnas según el tipo de reporte
            if es_feedback:
                columnas = ['reg_fecha', 'reg_n_gasera', 'reg_contrato', 'reg_fechontrat', 'reg_observ_audio']
            else:
                columnas = ['reg_fecha', 'reg_n_gasera', 'reg_contrato', 'reg_fechontrat',
                           'reg_tseguro1', 'reg_tseguro2', 'reg_estado_venta', 'reg_observ_audio']

            # Asegurarse de que solo se usen las columnas que existen en el DataFrame
            columnas_existentes = [col for col in columnas if col in df.columns]
            df_filtrado = df[columnas_existentes]

            # Guardar excel
            df_filtrado.to_excel(filepath, index=False, engine='openpyxl')

            # Preparar respuesta
            with open(filepath, 'rb') as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

    except Exception as e:
        logger.error(f"Error al generar el reporte por fecha: {str(e)}")
        return HttpResponse(f"Error al generar el reporte: {str(e)}", status=500)


@login_required
def config(request):
    """
    Vista de configuración
    """
    if TbRegActividad.objects.exists():
        ultimo_registro = TbRegActividad.objects.latest('idtb_actv')
        tb_reg_activ = TbRegActividad.objects.all()
        total_record = TbRegActividad.objects.count()
        data = {
            'ultimo_registro': ultimo_registro,
            'TbRegActividad': tb_reg_activ,
            'total_record': total_record
        }
        if ultimo_registro.reg_tip_consulta == "Comparativo":
            data['mensaje_fecha'] = "Fecha según Comparativa"
    else:
        data = {'mensaje': "NO HAY REGISTROS ACTUALES"}
    return render(request, 'pages/bc_typography.html', data)

def ejecutar_script():
    """
    Función para ejecutar script externo
    """
    try:        
        ruta_script = os.path.join(settings.BASE_DIR, 'mod_bot', 'logical.py')
        subprocess.Popen(['python', ruta_script], shell=True)
        print('Script ejecutado correctamente.')
    except Exception as e:
        print('Error al ejecutar el script:', str(e))

@login_required
def abrir_ubicacion(request):
    """
    Vista para abrir ubicación y ejecutar script
    """
    usuario_actual = request.user.username
    with open("usuario_temporal.txt", "w") as f:
        f.write(usuario_actual)
    ruta_script = os.path.join(settings.BASE_DIR, 'mod_bot', 'logical.py')
    subprocess.Popen(['python', ruta_script], shell=True)
    return redirect('config')

@login_required
def seleccionar_directorio(request):
    """
    Vista para seleccionar directorio
    """
    if request.method == 'POST':
        directorio_seleccionado = "/ruta/al/directorio"
        return render(request, 'pages/bc_typography.html', {'directorio_seleccionado': directorio_seleccionado})
    return HttpResponse("Método no permitido")

@login_required
def guardar_ruta_directorio(request):
    """
    Vista para guardar la ruta del directorio
    """
    if request.method == 'POST':
        ruta_directorio = request.POST.get('ruta_directorio')
        try:
            registro = TbRegActividad(reg_tip_dir=ruta_directorio)
            registro.save()
            return JsonResponse({'message': 'Ruta del directorio guardada correctamente.'})
        except Exception:
            return JsonResponse({'error': 'Error al guardar la ruta del directorio.'}, status=500)
    return JsonResponse({'error': 'Se esperaba una solicitud POST.'}, status=400)

@login_required
def obtener_datos_grafica(request):
    """
    Vista para obtener datos de la gráfica
    """
    datos = TbRegAudio.objects.annotate(
        date=TruncDate('reg_fecha')
    ).values('date').annotate(
        sales1=Count('idtb_reg_audio'),
        sales0=Count('idtb_reg_audio', filter=Q(reg_estado_venta='POSITIVA')),
        market1=Count('idtb_reg_audio', filter=Q(reg_estado_venta='NEGATIVA'))
    ).order_by('date')

    resultados = []
    for dato in datos:
        total = dato['sales1']
        resultados.append({
            'date': dato['date'].strftime('%Y-%m-%d'),
            'sales1': dato['sales1'],
            'sales0': dato['sales0'],
            'market1': dato['market1'],
            'market0': round(dato['sales0'] * 100 / total if total > 0 else 0, 2),
        })

    return JsonResponse(resultados, safe=False)

@login_required
def descargar_reporte(request):
    """
    Vista para descargar reporte
    """
    try:
        registros = TbRegAudio.objects.all().values()
        df = pd.DataFrame.from_records(registros)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_tb_reg_audio_{timestamp}.xlsx"

        with tempfile.TemporaryDirectory() as tmpdirname:
            filepath = os.path.join(tmpdirname, filename)
            df.to_excel(filepath, index=False, engine='openpyxl')

            with open(filepath, 'rb') as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response
    except Exception as e:
        return HttpResponse(f"Error al generar el reporte: {str(e)}", status=500)

# API Views
class DashboardStatsAPIView(APIView):
    """
    Vista API para estadísticas del dashboard
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Obtener todos los registros
            tb_reg_audio = TbRegAudio.objects.all().order_by('-reg_fecha')

            # Contadores
            total_records = TbRegAudio.objects.count()
            ventas_positivas = TbRegAudio.objects.filter(reg_estado_venta__iexact='POSITIVA').count()
            ventas_negativas = TbRegAudio.objects.filter(reg_estado_venta__iexact='NEGATIVA').count()

            # Formatear registros para la API
            registros = [{
                'reg_n_gasera': reg.reg_n_gasera,
                'reg_contrato': reg.reg_contrato,
                'reg_fechontrat': reg.reg_fechontrat,
                'reg_tseguro1': reg.reg_tseguro1,
                'reg_tseguro2': reg.reg_tseguro2,
                'reg_partaudioventa': reg.reg_partaudioventa,
                'reg_estado_venta': reg.reg_estado_venta,
                'reg_fecha': reg.reg_fecha.strftime('%Y-%m-%d') if reg.reg_fecha else None,
                'reg_observ_audio': reg.reg_observ_audio,
                'reg_tipoarchivo': reg.reg_tipoarchivo,
                'reg_pesoarch': reg.reg_pesoarch
            } for reg in tb_reg_audio]

            return Response({
                'stats': {
                    'total_records': total_records,
                    'ventas_positivas': ventas_positivas,
                    'ventas_negativas': ventas_negativas,
                    'porcentaje_positivas': round((ventas_positivas/total_records)*100 if total_records > 0 else 0, 2)
                },
                'registros': registros
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GraphDataAPIView(APIView):
    """
    Vista API para datos de gráficas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            datos = TbRegAudio.objects.annotate(
                date=TruncDate('reg_fecha')
            ).values('date').annotate(
                total_ventas=Count('idtb_reg_audio'),
                ventas_positivas=Count('idtb_reg_audio', filter=Q(reg_estado_venta='POSITIVA')),
                ventas_negativas=Count('idtb_reg_audio', filter=Q(reg_estado_venta='NEGATIVA'))
            ).order_by('date')

            resultados = []
            for dato in datos:
                total = dato['total_ventas']
                resultados.append({
                    'date': dato['date'].strftime('%Y-%m-%d'),
                    'total_ventas': dato['total_ventas'],
                    'ventas_positivas': dato['ventas_positivas'],
                    'ventas_negativas': dato['ventas_negativas'],
                    'porcentaje_positivas': round(dato['ventas_positivas'] * 100 / total if total > 0 else 0, 2),
                })

            return Response(resultados)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ActivityLogAPIView(APIView):
    """
    Vista API para log de actividades
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            actividades = TbRegActividad.objects.all().order_by('-reg_activ_fecha')
            data = [{
                'id': act.idtb_actv,
                'fecha': act.reg_activ_fecha.strftime('%Y-%m-%d %H:%M:%S') if act.reg_activ_fecha else None,
                'usuario': act.reg_activ_user,
                'archivos_procesados': act.reg_activ_archproc,
                'ventas_positivas': act.reg_sum_ventpos,
                'ventas_negativas': act.reg_sum_ventneg,
                'tipo_consulta': act.reg_tip_consulta,
                'directorio': act.reg_tip_dir,
            } for act in actividades]

            return Response(data)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report(request):
    """
    Vista API para generar reporte
    """
    try:
        registros = TbRegAudio.objects.all().values()
        df = pd.DataFrame.from_records(registros)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_tb_reg_audio_{timestamp}.xlsx"

        with tempfile.TemporaryDirectory() as tmpdirname:
            filepath = os.path.join(tmpdirname, filename)
            df.to_excel(filepath, index=False, engine='openpyxl')

            with open(filepath, 'rb') as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response
    except Exception as e:
        return Response({
            'error': f'Error al generar el reporte: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)