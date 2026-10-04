from django.contrib import admin

from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'tipo_identificacion', 'numero_identificacion', 'estado')
    list_filter = ('estado', 'tipo_identificacion')
    search_fields = ('razon_social', 'numero_identificacion')
    ordering = ('razon_social',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    fieldsets = (
        (None, {'fields': ('razon_social', 'tipo_identificacion', 'numero_identificacion', 'estado')}),
        ('Contacto', {'fields': ('direccion', 'municipio', 'telefono', 'email')}),
        ('Fechas', {'fields': ('fecha_creacion', 'fecha_actualizacion')}),
    )

    actions = ['activar_empresas', 'desactivar_empresas']

    @admin.action(description='Activar empresas seleccionadas')
    def activar_empresas(self, request, queryset):
        queryset.update(estado='ACTIVA')

    @admin.action(description='Desactivar empresas seleccionadas')
    def desactivar_empresas(self, request, queryset):
        queryset.update(estado='INACTIVA')
