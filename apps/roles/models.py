from django.core.exceptions import ValidationError
from django.db import models


class EstadoRol(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    INACTIVO = 'INACTIVO', 'Inactivo'


class EstadoPermiso(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    INACTIVO = 'INACTIVO', 'Inactivo'


class ModuloPermiso(models.TextChoices):
    EMPRESA = 'empresa', 'Empresa'
    USUARIOS = 'usuarios', 'Usuarios'
    ROLES = 'roles', 'Roles'
    CLIENTES = 'clientes', 'Clientes'
    PRODUCTOS = 'productos', 'Productos'
    INVENTARIO = 'inventario', 'Inventario'
    VENTAS = 'ventas', 'Ventas'
    FACTURACION = 'facturacion', 'Facturación'
    REPORTES = 'reportes', 'Reportes'


class Permiso(models.Model):
    """Catálogo global de capacidades de la plataforma. No pertenece a una Empresa."""

    codigo = models.CharField('código', max_length=100, unique=True)
    nombre = models.CharField('nombre', max_length=150)
    descripcion = models.TextField('descripción', blank=True)
    modulo = models.CharField('módulo', max_length=20, choices=ModuloPermiso.choices)
    estado = models.CharField('estado', max_length=20, choices=EstadoPermiso.choices, default=EstadoPermiso.ACTIVO)

    class Meta:
        verbose_name = 'permiso'
        verbose_name_plural = 'permisos'
        ordering = ['modulo', 'codigo']

    def __str__(self):
        return self.codigo

    def clean(self):
        if self.modulo and self.codigo and not self.codigo.startswith(f'{self.modulo}.'):
            raise ValidationError({'codigo': 'El código debe iniciar con "<modulo>."'})


class Rol(models.Model):
    """Rol configurable por Empresa. Agrupa permisos del catálogo global."""

    empresa = models.ForeignKey(
        'empresa.Empresa', verbose_name='empresa', related_name='roles', on_delete=models.PROTECT,
    )
    nombre = models.CharField('nombre', max_length=100)
    descripcion = models.TextField('descripción', blank=True)
    estado = models.CharField('estado', max_length=20, choices=EstadoRol.choices, default=EstadoRol.ACTIVO)

    es_administrador_principal = models.BooleanField(
        'administrador principal de la empresa',
        default=False,
        help_text='Rol con control total sobre su empresa (equivalente a SUPER_ADMIN_EMPRESA). '
                   'Solo puede existir un rol con esta marca por empresa.',
    )

    usuarios = models.ManyToManyField(
        'autenticacion.Usuario', through='UsuarioRol', related_name='roles', blank=True,
    )
    permisos = models.ManyToManyField(
        Permiso, through='RolPermiso', related_name='roles', blank=True,
    )

    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'rol'
        verbose_name_plural = 'roles'
        ordering = ['empresa_id', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'nombre'], name='unique_rol_nombre_por_empresa'),
            models.UniqueConstraint(
                fields=['empresa'],
                condition=models.Q(es_administrador_principal=True),
                name='unique_admin_principal_por_empresa',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.empresa.razon_social})'

    @property
    def esta_activo(self):
        return self.estado == EstadoRol.ACTIVO


class UsuarioRol(models.Model):
    """Asignación de un Rol a un Usuario. Debe pertenecer a la misma Empresa."""

    usuario = models.ForeignKey(
        'autenticacion.Usuario', on_delete=models.CASCADE, related_name='asignaciones_rol',
    )
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='asignaciones_usuario')
    fecha_asignacion = models.DateTimeField('fecha de asignación', auto_now_add=True)

    class Meta:
        verbose_name = 'asignación de rol'
        verbose_name_plural = 'asignaciones de rol'
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'rol'], name='unique_usuario_rol'),
        ]

    def __str__(self):
        return f'{self.usuario.email} → {self.rol.nombre}'

    def clean(self):
        if self.usuario_id and self.rol_id and self.usuario.empresa_id != self.rol.empresa_id:
            raise ValidationError('El rol debe pertenecer a la misma empresa que el usuario.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RolPermiso(models.Model):
    """Asignación de un Permiso del catálogo global a un Rol."""

    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='asignaciones_permiso')
    permiso = models.ForeignKey(Permiso, on_delete=models.PROTECT, related_name='asignaciones_rol')
    fecha_asignacion = models.DateTimeField('fecha de asignación', auto_now_add=True)

    class Meta:
        verbose_name = 'permiso de rol'
        verbose_name_plural = 'permisos de rol'
        constraints = [
            models.UniqueConstraint(fields=['rol', 'permiso'], name='unique_rol_permiso'),
        ]

    def __str__(self):
        return f'{self.rol.nombre} → {self.permiso.codigo}'
