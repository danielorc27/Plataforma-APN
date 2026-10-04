from django.core.exceptions import ValidationError

from .models import EstadoRol, UsuarioRol


class RBACError(Exception):
    """Error de dominio para operaciones sobre roles y asignaciones."""


def _empresa_tiene_otro_administrador(empresa_id, excluyendo_usuario_id):
    return UsuarioRol.objects.filter(
        rol__empresa_id=empresa_id,
        rol__es_administrador_principal=True,
        rol__estado=EstadoRol.ACTIVO,
    ).exclude(usuario_id=excluyendo_usuario_id).exists()


def asignar_rol(usuario, rol):
    """Asigna un rol a un usuario. El rol debe pertenecer a la empresa del usuario."""
    try:
        usuario_rol, _creado = UsuarioRol.objects.get_or_create(usuario=usuario, rol=rol)
    except ValidationError as exc:
        raise RBACError(str(exc)) from exc
    return usuario_rol


def quitar_rol(usuario, rol):
    """Quita un rol de un usuario, evitando dejar a la empresa sin administrador principal."""
    if usuario.empresa_id != rol.empresa_id:
        raise RBACError('El rol no pertenece a la empresa del usuario.')
    if rol.es_administrador_principal and not _empresa_tiene_otro_administrador(rol.empresa_id, usuario.pk):
        raise RBACError('No se puede dejar a la empresa sin administrador principal.')
    UsuarioRol.objects.filter(usuario=usuario, rol=rol).delete()


def desactivar_usuario(usuario_objetivo, ejecutor):
    """Desactiva (soft-delete) a un usuario, aplicando las reglas de protección del administrador."""
    if usuario_objetivo.pk == ejecutor.pk:
        raise RBACError('Un usuario no puede desactivarse a sí mismo.')
    if not ejecutor.is_superuser and ejecutor.empresa_id != usuario_objetivo.empresa_id:
        raise RBACError('No puede administrar usuarios de otra empresa.')

    es_admin_principal = usuario_objetivo.roles.filter(
        es_administrador_principal=True, estado=EstadoRol.ACTIVO,
    ).exists()
    if es_admin_principal and not _empresa_tiene_otro_administrador(usuario_objetivo.empresa_id, usuario_objetivo.pk):
        raise RBACError('No se puede dejar la empresa sin administrador principal.')

    usuario_objetivo.is_active = False
    usuario_objetivo.save(update_fields=['is_active'])
