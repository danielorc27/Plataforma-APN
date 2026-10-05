from django.contrib import admin

from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'empresa', 'precio', 'unidad', 'estado')
    list_filter = ('empresa', 'estado', 'unidad')
    search_fields = ('codigo', 'nombre')
    autocomplete_fields = ('empresa',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

    actions = ['activar_productos', 'desactivar_productos']

    @admin.action(description='Activar productos seleccionados')
    def activar_productos(self, request, queryset):
        queryset.update(estado='ACTIVO')

    @admin.action(description='Desactivar productos seleccionados')
    def desactivar_productos(self, request, queryset):
        queryset.update(estado='INACTIVO')
