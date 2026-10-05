from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.roles.decorators import permiso_requerido

from .forms import ClienteForm
from .models import Cliente
from .services import ClienteError, actualizar_cliente, registrar_cliente


@permiso_requerido('clientes.ver')
def clientes_lista(request):
    clientes = Cliente.objects.filter(empresa=request.user.empresa)

    query = request.GET.get('q', '').strip()
    if query:
        clientes = clientes.filter(Q(nombre__icontains=query) | Q(numero_identificacion__icontains=query))

    contexto = {
        'clientes': clientes,
        'query': query,
        'puede_crear': request.user.has_permission('clientes.crear'),
        'puede_editar': request.user.has_permission('clientes.editar'),
    }
    return render(request, 'clientes/lista.html', contexto)


@permiso_requerido('clientes.ver')
def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if cliente.empresa_id != request.user.empresa_id:
        raise PermissionDenied('No tiene acceso a este cliente.')
    contexto = {
        'cliente': cliente,
        'puede_editar': request.user.has_permission('clientes.editar'),
    }
    return render(request, 'clientes/detalle.html', contexto)


@permiso_requerido('clientes.crear')
def cliente_crear(request):
    if request.user.empresa_id is None:
        raise PermissionDenied('El usuario no tiene una empresa asociada.')

    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                registrar_cliente(request.user.empresa, form.cleaned_data)
            except ClienteError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, 'Cliente registrado correctamente.')
                return redirect('clientes:lista')
    else:
        form = ClienteForm()
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Nuevo cliente'})


@permiso_requerido('clientes.editar')
def cliente_editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if cliente.empresa_id != request.user.empresa_id:
        raise PermissionDenied('No tiene acceso a este cliente.')

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            try:
                actualizar_cliente(cliente, form.cleaned_data)
            except ClienteError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, 'Cliente actualizado correctamente.')
                return redirect('clientes:detalle', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/form.html', {'form': form, 'titulo': 'Editar cliente'})
