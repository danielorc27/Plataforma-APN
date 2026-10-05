from django.core.exceptions import ValidationError

from .models import EstadoProducto, Producto

CAMPOS_EDITABLES = {'codigo', 'nombre', 'descripcion', 'precio', 'unidad', 'porcentaje_impuesto'}
CAMPOS_SIN_PRECIO = CAMPOS_EDITABLES - {'precio'}


class ProductoError(Exception):
    """Error de dominio para operaciones sobre Producto."""


def registrar_producto(empresa, datos):
    """Crea un Producto asociado a `empresa` (siempre request.user.empresa, nunca del cliente HTTP).

    Cualquier clave en `datos` que no sea un campo editable del producto
    (por ejemplo, un intento de enviar `empresa`) se rechaza explícitamente.
    """
    for campo in datos:
        if campo not in CAMPOS_EDITABLES:
            raise ProductoError(f'El campo "{campo}" no puede establecerse desde este caso de uso.')

    producto = Producto(empresa=empresa, **datos)
    try:
        producto.full_clean()
    except ValidationError as exc:
        raise ProductoError(str(exc)) from exc
    producto.save()
    return producto


def actualizar_producto(producto, datos, puede_cambiar_precio):
    """Actualiza un Producto existente. Nunca modifica su empresa.

    `precio` solo puede incluirse en `datos` si `puede_cambiar_precio` es
    True. Esta verificación ocurre en el backend independientemente de
    si el formulario/HTML oculta o no el campo.
    """
    campos_permitidos = CAMPOS_EDITABLES if puede_cambiar_precio else CAMPOS_SIN_PRECIO
    for campo in datos:
        if campo == 'precio' and not puede_cambiar_precio:
            raise ProductoError('No tiene permiso para modificar el precio del producto.')
        if campo not in campos_permitidos:
            raise ProductoError(f'El campo "{campo}" no puede modificarse desde este caso de uso.')

    for campo, valor in datos.items():
        setattr(producto, campo, valor)
    try:
        producto.full_clean()
    except ValidationError as exc:
        raise ProductoError(str(exc)) from exc
    producto.save()
    return producto


def activar_producto(producto):
    producto.estado = EstadoProducto.ACTIVO
    producto.save(update_fields=['estado', 'fecha_actualizacion'])
    return producto


def desactivar_producto(producto):
    producto.estado = EstadoProducto.INACTIVO
    producto.save(update_fields=['estado', 'fecha_actualizacion'])
    return producto
