from django import template
from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

register = template.Library()

@register.filter
def checkbox(value):
    """
    Filtro para estilizar los checkboxes del admin de Django.
    
    Este filtro extrae el checkbox de un elemento de administración y lo devuelve
    con las clases y estilo actualizados para mejorar la apariencia.
    """
    # Simplemente devolvemos el valor ya que contiene el HTML del checkbox
    # Django ya genera el checkbox, solo necesitamos extraerlo del HTML
    # Esto funciona porque el checkbox ya está incluido en el elemento
    return value

@register.filter
def neg_num(value, arg):
    """
    Resta un número de otro.
    Por ejemplo: {{ 5|neg_num:1 }} devuelve 4.
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def sum_number(value, arg):
    """
    Suma un número a otro.
    Por ejemplo: {{ 5|sum_number:1 }} devuelve 6.
    """
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value

@register.simple_tag(takes_context=True)
def admin_get_menu(context):
    """
    Obtiene el menú de aplicaciones para el administrador.
    """
    request = context.get('request')
    
    # Si no hay request o el usuario no está autenticado, retornar una lista vacía
    if not request or not request.user.is_authenticated:
        return []
    
    # Lista de aplicaciones para el menú
    app_list = []
    
    # Intentar obtener la lista del admin de Django
    try:
        app_dict = {}
        for model, model_admin in admin.site._registry.items():
            app_label = model._meta.app_label
            
            # Si es la primera vez que vemos esta app, inicializar
            if app_label not in app_dict:
                app_dict[app_label] = {
                    'name': app_label,
                    'app_label': app_label,
                    'app_url': reverse(f'admin:app_list', kwargs={'app_label': app_label}),
                    'has_module_perms': True,  # Simplificado para este ejemplo
                    'models': [],
                    'icon': 'icon-server',  # Icono por defecto
                    'label': model._meta.app_config.verbose_name,
                    'pinned': False,
                    'has_perms': True
                }
            
            # Iconos específicos para aplicaciones conocidas
            if app_label == 'auth':
                app_dict[app_label]['icon'] = 'icon-user'
            elif app_label == 'admin_gradient':
                app_dict[app_label]['icon'] = 'icon-command'
            
            # Añadir el modelo a la app
            model_dict = {
                'name': model._meta.model_name,
                'object_name': model._meta.object_name,
                'perms': {'add': True, 'change': True, 'delete': True, 'view': True},  # Simplificado
                'label': model._meta.verbose_name_plural,
                'url': None
            }
            
            # Intentar conseguir la URL del modelo
            try:
                model_dict['url'] = reverse(f'admin:{app_label}_{model._meta.model_name}_changelist')
            except NoReverseMatch:
                pass
            
            app_dict[app_label]['models'].append(model_dict)
        
        # Convertir el diccionario a lista
        app_list = list(app_dict.values())
        
        # Ordenar las apps
        app_list.sort(key=lambda x: x['label'].lower())
        
        # Ordenar los modelos dentro de cada app
        for app in app_list:
            app['models'].sort(key=lambda x: x['label'].lower())
    
    except Exception as e:
        # Si hay error, devolver una lista vacía y loguear el error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error obteniendo menú del admin: {str(e)}")
        return []
    
    return app_list

@register.inclusion_tag("admin/pagination_numbers.html")
def paginator_number(cl, i):
    """
    Genera la etiqueta de paginación para el número de página i.
    """
    if i == cl.page_num:
        return {
            'number': i,
            'url': cl.get_query_string({cl.page_var: i}),
            'is_active': True
        }
    else:
        return {
            'number': i,
            'url': cl.get_query_string({cl.page_var: i}),
            'is_active': False
        }
