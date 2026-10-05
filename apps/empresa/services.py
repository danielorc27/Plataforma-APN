from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.roles.models import Rol
from apps.roles.services import asignar_rol

from .models import Empresa, EstadoEmpresa

CAMPOS_EDITABLES_EMPRESA = {'razon_social', 'direccion', 'municipio', 'telefono', 'email'}


class EmpresaError(Exception):
    """Error de dominio para operaciones sobre Empresa."""


@transaction.atomic
def registrar_empresa(datos_empresa, datos_administrador):
    """Crea una Empresa junto con su usuario administrador principal.

    Operación atómica: si falla cualquier paso (empresa, usuario, rol o
    asignación), no debe persistir nada (ni empresa huérfana, ni usuario
    sin empresa, ni asignación incompleta).
    """
    Usuario = get_user_model()

    empresa = Empresa(**datos_empresa)
    try:
        empresa.full_clean()
    except ValidationError as exc:
        raise EmpresaError(str(exc)) from exc
    empresa.save()

    usuario = Usuario(
        email=datos_administrador['email'],
        nombre=datos_administrador['nombre'],
        apellido=datos_administrador['apellido'],
        empresa=empresa,
    )
    usuario.set_password(datos_administrador['password'])
    try:
        usuario.full_clean()
    except ValidationError as exc:
        raise EmpresaError(str(exc)) from exc
    usuario.save()

    rol_admin = Rol.objects.create(
        empresa=empresa, nombre='Administrador', es_administrador_principal=True,
    )
    asignar_rol(usuario, rol_admin)

    return empresa, usuario


def actualizar_empresa(empresa, datos):
    """Actualiza los campos editables de una Empresa.

    No permite modificar identificación (inmutable tras el registro) ni
    estado (solo lo controla SUPER_ADMIN_SISTEMA mediante activar/desactivar).
    """
    for campo in datos:
        if campo not in CAMPOS_EDITABLES_EMPRESA:
            raise EmpresaError(f'El campo "{campo}" no puede modificarse desde este caso de uso.')
    for campo, valor in datos.items():
        setattr(empresa, campo, valor)
    try:
        empresa.full_clean()
    except ValidationError as exc:
        raise EmpresaError(str(exc)) from exc
    empresa.save()
    return empresa


def activar_empresa(empresa):
    empresa.estado = EstadoEmpresa.ACTIVA
    empresa.save(update_fields=['estado', 'fecha_actualizacion'])
    return empresa


def desactivar_empresa(empresa):
    empresa.estado = EstadoEmpresa.INACTIVA
    empresa.save(update_fields=['estado', 'fecha_actualizacion'])
    return empresa
