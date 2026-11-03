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
import sys
from django.conf import settings
from django.utils import timezone
import tempfile
import logging
import json
from datetime import datetime, timedelta
import uuid

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST



@login_required
@require_POST
def logout_view(request):
    """
    Cierra sesión solo con POST (evita logout CSRF por enlace GET).
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
        tb_reg_activ = TbRegActividad.objects.all().order_by('-reg_activ_fecha', '-idtb_actv')  # Ordenado por fecha descendente
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
def iniciar_auditoria_remota(request):
    """
    Vista para iniciar la auditoría desde un cliente remoto
    Solo requiere el archivo Excel y automáticamente encuentra los archivos de audio
    """
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        try:
            # Obtener el archivo subido
            archivo_excel = request.FILES['archivo_excel']
            usuario_actual = request.user.username
            
            # Guardar archivo temporalmente
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"{uuid.uuid4()}.xlsx")
            
            with open(temp_file, 'wb+') as destination:
                for chunk in archivo_excel.chunks():
                    destination.write(chunk)
            
            # Registrar el usuario para el script
            with open("usuario_temporal.txt", "w") as f:
                f.write(usuario_actual)
            
            # Ejecutar proceso en un hilo separado para no bloquear la respuesta
            def proceso_background():
                try:
                    # Importar el módulo de auditoría remota
                    sys.path.append(os.path.join(settings.BASE_DIR, 'mod_bot'))
                    from remote_auditor import iniciar_proceso_remoto
                    
                    # Ejecutar el proceso
                    resultado = iniciar_proceso_remoto(temp_file, usuario_actual)
                    
                    # Registrar el resultado en el log
                    log_dir = os.path.join(settings.BASE_DIR, "Logica_Log_Err")
                    os.makedirs(log_dir, exist_ok=True)
                    with open(os.path.join(log_dir, "auditoria_remota.log"), "a") as log_file:
                        log_file.write(f"[{datetime.now()}] Usuario: {usuario_actual} - Resultado: {json.dumps(resultado)}\n")
                    
                    # Crear archivo de señal para mostrar toast
                    if resultado.get('success'):
                        with open(os.path.join(settings.BASE_DIR, "senal_toast.txt"), "w") as signal_file:
                            signal_file.write(f"success|{resultado.get('total_archivos', 0)}")
                    else:
                        with open(os.path.join(settings.BASE_DIR, "senal_toast.txt"), "w") as signal_file:
                            signal_file.write(f"error|{resultado.get('error', 'Error desconocido')}")
                    
                finally:
                    # Limpiar archivos temporales
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        if os.path.exists(temp_dir):
                            os.rmdir(temp_dir)
                    except Exception as e:
                        logger.error(f"Error al limpiar archivos temporales: {str(e)}")
            
            # Iniciar proceso en segundo plano
            thread = threading.Thread(target=proceso_background)
            thread.daemon = True
            thread.start()
            
            # Enviar respuesta inmediata
            return JsonResponse({
                'success': True,
                'message': 'Proceso de auditoría iniciado. Los resultados se mostrarán una vez completado.'
            })
            
        except Exception as e:
            logger.error(f"Error al iniciar la auditoría remota: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f"Error al iniciar la auditoría: {str(e)}"
            }, status=500)
    
    return HttpResponse("Método no permitido", status=405)

@login_required
def ver_senal_toast(request):
    """
    Vista para verificar si hay una señal para mostrar un toast
    """
    try:
        # Verificar si existe el archivo de señal
        senal_file = os.path.join(settings.BASE_DIR, "senal_toast.txt")
        if os.path.exists(senal_file):
            with open(senal_file, "r") as f:
                contenido = f.read().strip()
            
            # Eliminar el archivo después de leerlo
            os.remove(senal_file)
            
            # Procesar el contenido
            partes = contenido.split('|')
            tipo = partes[0]
            mensaje = partes[1] if len(partes) > 1 else ""
            
            return JsonResponse({
                'mostrar': True,
                'tipo': tipo,
                'mensaje': mensaje,
                'total_archivos': mensaje if tipo == 'success' else 0
            })
        else:
            return JsonResponse({'mostrar': False})
    except Exception as e:
        logger.error(f"Error al verificar señal toast: {str(e)}")
        return JsonResponse({'mostrar': False})

@login_required
def cancelar_auditoria(request):
    """
    Vista para cancelar el proceso de auditoría en curso
    """
    try:
        # Crear un archivo de señal para cancelar el proceso
        with open(os.path.join(settings.BASE_DIR, "cancelar_proceso.txt"), "w") as f:
            f.write(f"Cancelado por {request.user.username} en {datetime.now()}")
        
        # Limpiar archivo de progreso
        progreso_file = os.path.join(settings.BASE_DIR, "Logica_Log_Err", "progreso_auditoria.json")
        if os.path.exists(progreso_file):
            with open(progreso_file, "w") as f:
                json.dump({
                    'en_progreso': False,
                    'archivo_actual': '',
                    'fecha_actual': '',
                    'archivos_procesados': 0,
                    'total_archivos': 0,
                    'porcentaje': 0,
                    'pendientes': 0,
                    'tiempo_transcurrido': '00:00:00',
                    'actividad': [{
                        'hora': datetime.now().strftime('%H:%M:%S'),
                        'mensaje': f'Proceso cancelado por el usuario {request.user.username}'
                    }]
                }, f)
        
        # Registrar la cancelación en el log
        logger.info(f"Proceso de auditoría cancelado por el usuario {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Proceso cancelado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error al cancelar el proceso de auditoría: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error al cancelar el proceso: {str(e)}"
        }, status=500)

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

@login_required
def ver_progreso_auditoria(request):
    """
    Vista para obtener el progreso actual de la auditoría
    """
    try:
        # Verificar si existe el archivo de progreso
        progreso_file = os.path.join(settings.BASE_DIR, "Logica_Log_Err", "progreso_auditoria.json")
        
        if os.path.exists(progreso_file):
            with open(progreso_file, "r") as f:
                progreso = json.load(f)
            
            # Calcular porcentaje de progreso
            total = progreso.get('total_archivos', 0)
            procesados = progreso.get('archivos_procesados', 0)
            porcentaje = int((procesados / total) * 100) if total > 0 else 0
            
            # Añadir información calculada
            progreso['porcentaje'] = porcentaje
            progreso['pendientes'] = total - procesados
            
            return JsonResponse(progreso)
        else:
            # Si no existe el archivo, devolver valores por defecto
            return JsonResponse({
                'en_progreso': False,
                'archivo_actual': '',
                'fecha_actual': '',
                'archivos_procesados': 0,
                'total_archivos': 0,
                'porcentaje': 0,
                'pendientes': 0,
                'tiempo_transcurrido': '00:00:00',
                'actividad': []
            })
    except Exception as e:
        logger.error(f"Error al obtener progreso de auditoría: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)
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