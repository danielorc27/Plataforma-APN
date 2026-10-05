from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.roles.decorators import permiso_requerido

from .forms import ProductoForm
from .models import Producto
from .services import ProductoError, activar_producto, actualizar_producto, desactivar_producto, registrar_producto


@permiso_requerido('productos.ver')
def productos_lista(request):
    productos = Producto.objects.filter(empresa=request.user.empresa)

    query = request.GET.get('q', '').strip()
    if query:
        productos = productos.filter(Q(nombre__icontains=query) | Q(codigo__icontains=query))

    contexto = {
        'productos': productos,
        'query': query,
        'puede_crear': request.user.has_permission('productos.crear'),
        'puede_editar': request.user.has_permission('productos.editar'),
        'puede_activar': request.user.has_permission('productos.activar'),
        'puede_desactivar': request.user.has_permission('productos.desactivar'),
    }
    return render(request, 'productos/lista.html', contexto)


@permiso_requerido('productos.ver')
def producto_detalle(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.empresa_id != request.user.empresa_id:
        raise PermissionDenied('No tiene acceso a este producto.')
    contexto = {
        'producto': producto,
        'puede_editar': request.user.has_permission('productos.editar'),
        'puede_activar': request.user.has_permission('productos.activar'),
        'puede_desactivar': request.user.has_permission('productos.desactivar'),
    }
    return render(request, 'productos/detalle.html', contexto)


@permiso_requerido('productos.crear')
def producto_crear(request):
    if request.user.empresa_id is None:
        raise PermissionDenied('El usuario no tiene una empresa asociada.')

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            try:
                registrar_producto(request.user.empresa, form.cleaned_data)
            except ProductoError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, 'Producto registrado correctamente.')
                return redirect('productos:lista')
    else:
        form = ProductoForm()
    return render(request, 'productos/form.html', {'form': form, 'titulo': 'Nuevo producto'})


@permiso_requerido('productos.editar')
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.empresa_id != request.user.empresa_id:
        raise PermissionDenied('No tiene acceso a este producto.')

    puede_cambiar_precio = request.user.has_permission('productos.cambiar_precio')

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto, puede_cambiar_precio=puede_cambiar_precio)
        if form.is_valid():
            try:
                actualizar_producto(producto, form.cleaned_data, puede_cambiar_precio)
            except ProductoError as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, 'Producto actualizado correctamente.')
                return redirect('productos:detalle', pk=producto.pk)
    else:
        form = ProductoForm(instance=producto, puede_cambiar_precio=puede_cambiar_precio)
    return render(request, 'productos/form.html', {'form': form, 'titulo': 'Editar producto'})


@permiso_requerido('productos.activar')
def producto_activar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.empresa_id != request.user.empresa_id:
        raise PermissionDenied('No tiene acceso a este producto.')
    if request.method == 'POST':
        activar_producto(producto)
        messages.success(request, f'Producto "{producto.nombre}" activado.')
    return redirect('productos:detalle', pk=pk)


@permiso_requerido('productos.desactivar')
def producto_desactivar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if producto.empresa_id != request.user.empresa_id:
        raise PermissionDenied('No tiene acceso a este producto.')
    if request.method == 'POST':
        desactivar_producto(producto)
        messages.success(request, f'Producto "{producto.nombre}" desactivado.')
    return redirect('productos:detalle', pk=pk)
