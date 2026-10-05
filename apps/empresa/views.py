from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.roles.decorators import permiso_requerido, superadmin_sistema_requerido

from .forms import AdministradorInicialForm, EmpresaCreateForm, EmpresaEditForm
from .models import Empresa
from .services import EmpresaError, activar_empresa, actualizar_empresa, desactivar_empresa, registrar_empresa


@login_required
def empresa_detalle(request, pk):
    """Muestra el detalle de una empresa. (Fase 3: demostración de contexto/aislamiento.)

    El tenant se determina siempre a partir de request.user.empresa;
    el pk de la URL solo se usa para detectar intentos de acceder a
    una empresa distinta a la del usuario autenticado.
    """
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.user.empresa_id != empresa.pk:
        raise PermissionDenied('No tiene acceso a esta empresa.')
    return render(request, 'empresa/detalle.html', {'empresa': empresa})


@permiso_requerido('empresa.ver')
def empresa_ver(request):
    """HU-002: consultar la empresa actual (SUPER_ADMIN_EMPRESA / roles con empresa.ver)."""
    if request.user.empresa_id is None:
        raise PermissionDenied('El usuario no tiene una empresa asociada.')
    contexto = {
        'empresa': request.user.empresa,
        'puede_editar': request.user.has_permission('empresa.editar'),
    }
    return render(request, 'empresa/ver.html', contexto)


@permiso_requerido('empresa.editar')
def empresa_editar(request):
    """HU-003: actualizar la empresa actual. Nunca opera sobre otra empresa ni acepta su id por request."""
    if request.user.empresa_id is None:
        raise PermissionDenied('El usuario no tiene una empresa asociada.')

    empresa = request.user.empresa
    if request.method == 'POST':
        form = EmpresaEditForm(request.POST, instance=empresa)
        if form.is_valid():
            try:
                actualizar_empresa(empresa, form.cleaned_data)
            except EmpresaError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, 'Empresa actualizada correctamente.')
                return redirect('empresa:ver')
    else:
        form = EmpresaEditForm(instance=empresa)
    return render(request, 'empresa/editar.html', {'form': form, 'empresa': empresa})


@superadmin_sistema_requerido
def admin_empresas_lista(request):
    """Administración global de empresas (SUPER_ADMIN_SISTEMA)."""
    empresas = Empresa.objects.all()
    return render(request, 'empresa/admin_lista.html', {'empresas': empresas})


@superadmin_sistema_requerido
def admin_empresa_crear(request):
    """HU-001: registrar empresa + administrador principal (SUPER_ADMIN_SISTEMA)."""
    if request.method == 'POST':
        empresa_form = EmpresaCreateForm(request.POST, prefix='empresa')
        admin_form = AdministradorInicialForm(request.POST, prefix='admin')
        if empresa_form.is_valid() and admin_form.is_valid():
            try:
                registrar_empresa(
                    datos_empresa=empresa_form.cleaned_data,
                    datos_administrador={
                        'email': admin_form.cleaned_data['email'],
                        'nombre': admin_form.cleaned_data['nombre'],
                        'apellido': admin_form.cleaned_data['apellido'],
                        'password': admin_form.cleaned_data['password1'],
                    },
                )
            except EmpresaError as exc:
                empresa_form.add_error(None, str(exc))
            else:
                messages.success(request, 'Empresa y administrador principal creados correctamente.')
                return redirect('empresa:admin_lista')
    else:
        empresa_form = EmpresaCreateForm(prefix='empresa')
        admin_form = AdministradorInicialForm(prefix='admin')
    return render(request, 'empresa/admin_crear.html', {'empresa_form': empresa_form, 'admin_form': admin_form})


@superadmin_sistema_requerido
def admin_empresa_detalle(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    return render(request, 'empresa/admin_detalle.html', {'empresa': empresa})


@superadmin_sistema_requerido
def admin_empresa_activar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        activar_empresa(empresa)
        messages.success(request, f'Empresa "{empresa.razon_social}" activada.')
    return redirect('empresa:admin_detalle', pk=pk)


@superadmin_sistema_requerido
def admin_empresa_desactivar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        desactivar_empresa(empresa)
        messages.success(request, f'Empresa "{empresa.razon_social}" desactivada.')
    return redirect('empresa:admin_detalle', pk=pk)
