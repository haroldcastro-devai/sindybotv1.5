from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html

# Personalizar la visualización del administrador de usuarios
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active_icon', 'is_staff_icon', 'is_superuser_icon', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Iconos para estados booleanos
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<i class="fas fa-check-circle text-success" title="Usuario activo"></i>')
        return format_html('<i class="fas fa-times-circle text-danger" title="Usuario inactivo"></i>')
    is_active_icon.short_description = 'Activo'
    
    def is_staff_icon(self, obj):
        if obj.is_staff:
            return format_html('<i class="fas fa-check-circle text-success" title="Acceso al admin"></i>')
        return format_html('<i class="fas fa-times-circle text-danger" title="Sin acceso al admin"></i>')
    is_staff_icon.short_description = 'Staff'
    
    def is_superuser_icon(self, obj):
        if obj.is_superuser:
            return format_html('<i class="fas fa-check-circle text-success" title="Superusuario"></i>')
        return format_html('<i class="fas fa-times-circle text-danger" title="Usuario normal"></i>')
    is_superuser_icon.short_description = 'Admin'
    
    # Para el formulario de adición de usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Información Personal', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('Permisos', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
    )
    
    # Añadir acciones personalizadas
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Activar usuarios seleccionados"
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Desactivar usuarios seleccionados"

# Personalizar la visualización del administrador de grupos
class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    def user_count(self, obj):
        return obj.user_set.count()
    user_count.short_description = 'Usuarios'

# Registrar nuestros administradores personalizados
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

# Personalizar la cabecera del admin
admin.site.site_header = 'SBOT - Administración'
admin.site.site_title = 'SBOT Admin'
admin.site.index_title = 'Panel de Administración'