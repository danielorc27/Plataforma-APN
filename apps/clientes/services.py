from django.core.exceptions import ValidationError

from .models import Cliente

CAMPOS_EDITABLES = {'tipo_identificacion', 'numero_identificacion', 'nombre', 'email', 'telefono', 'direccion'}


class ClienteError(Exception):
    """Error de dominio para operaciones sobre Cliente."""


def registrar_cliente(empresa, datos):
    """Crea un Cliente asociado a `empresa`.

    `empresa` siempre proviene de request.user.empresa (nunca del
    formulario/cliente HTTP). Cualquier clave en `datos` que no sea un
    campo editable del cliente (por ejemplo, un intento de enviar
    `empresa`) se rechaza explícitamente.
    """
    for campo in datos:
        if campo not in CAMPOS_EDITABLES:
            raise ClienteError(f'El campo "{campo}" no puede establecerse desde este caso de uso.')

    cliente = Cliente(empresa=empresa, **datos)
    try:
        cliente.full_clean()
    except ValidationError as exc:
        raise ClienteError(str(exc)) from exc
    cliente.save()
    return cliente


def actualizar_cliente(cliente, datos):
    """Actualiza los campos editables de un Cliente. Nunca modifica su empresa."""
    for campo in datos:
        if campo not in CAMPOS_EDITABLES:
            raise ClienteError(f'El campo "{campo}" no puede modificarse desde este caso de uso.')

    for campo, valor in datos.items():
        setattr(cliente, campo, valor)
    try:
        cliente.full_clean()
    except ValidationError as exc:
        raise ClienteError(str(exc)) from exc
    cliente.save()
    return cliente
