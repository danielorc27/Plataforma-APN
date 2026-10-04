from django.contrib import admin

from .models import Permiso, Rol, RolPermiso


class RolPermisoInline(admin.TabularInline):
    model = RolPermiso
    extra = 1
    autocomplete_fields = ('permiso',)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'estado', 'es_administrador_principal')
    list_filter = ('empresa', 'estado', 'es_administrador_principal')
    search_fields = ('nombre',)
    autocomplete_fields = ('empresa',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [RolPermisoInline]

    fieldsets = (
        (None, {'fields': ('empresa', 'nombre', 'descripcion', 'estado', 'es_administrador_principal')}),
        ('Fechas', {'fields': ('fecha_creacion', 'fecha_actualizacion')}),
    )

    actions = ['activar_roles', 'desactivar_roles']

    @admin.action(description='Activar roles seleccionados')
    def activar_roles(self, request, queryset):
        queryset.update(estado='ACTIVO')

    @admin.action(description='Desactivar roles seleccionados')
    def desactivar_roles(self, request, queryset):
        queryset.update(estado='INACTIVO')


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'modulo', 'estado')
    list_filter = ('modulo', 'estado')
    search_fields = ('codigo', 'nombre')
    ordering = ('modulo', 'codigo')
