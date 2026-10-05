from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_identificacion', 'numero_identificacion', 'empresa', 'email', 'telefono')
    list_filter = ('empresa', 'tipo_identificacion')
    search_fields = ('numero_identificacion', 'nombre')
    autocomplete_fields = ('empresa',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
