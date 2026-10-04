from django.shortcuts import render

from apps.roles.decorators import permiso_requerido

from .models import Usuario


@permiso_requerido('usuarios.ver')
def usuarios_lista(request):
    usuarios = Usuario.objects.filter(empresa=request.user.empresa)
    return render(request, 'autenticacion/usuarios_lista.html', {'usuarios': usuarios})


@permiso_requerido('usuarios.crear')
def usuarios_crear(request):
    return render(request, 'autenticacion/usuarios_crear.html')
