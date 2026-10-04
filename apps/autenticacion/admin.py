from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.roles.models import UsuarioRol

from .forms import UsuarioChangeForm, UsuarioCreationForm
from .models import Usuario


class UsuarioRolInline(admin.TabularInline):
    model = UsuarioRol
    fk_name = 'usuario'
    extra = 1
    autocomplete_fields = ('rol',)


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm

    model = Usuario

    list_display = ('email', 'nombre', 'apellido', 'empresa', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'empresa')
    search_fields = ('email', 'nombre', 'apellido')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')
    autocomplete_fields = ('empresa',)
    inlines = [UsuarioRolInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'apellido')}),
        ('Empresa', {'fields': ('empresa',)}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'fecha_creacion', 'fecha_actualizacion')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'apellido', 'empresa', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login', 'fecha_creacion', 'fecha_actualizacion')

    actions = ['activar_usuarios', 'desactivar_usuarios']

    @admin.action(description='Activar usuarios seleccionados')
    def activar_usuarios(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Desactivar usuarios seleccionados')
    def desactivar_usuarios(self, request, queryset):
        queryset.update(is_active=False)
