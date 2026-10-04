from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class UsuarioManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, nombre, apellido, password, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un email.')
        email = self.normalize_email(email)
        usuario = self.model(email=email, nombre=nombre, apellido=apellido, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, nombre, apellido, password, **extra_fields)

    def create_superuser(self, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self._create_user(email, nombre, apellido, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('email', unique=True)
    nombre = models.CharField('nombre', max_length=150)
    apellido = models.CharField('apellido', max_length=150)

    empresa = models.ForeignKey(
        'empresa.Empresa',
        verbose_name='empresa',
        related_name='usuarios',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Empresa (tenant) a la que pertenece el usuario. '
                   'Vacío únicamente para administradores de plataforma (is_superuser=True).',
    )

    is_active = models.BooleanField('activo', default=True)
    is_staff = models.BooleanField('acceso al admin', default=False)

    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('fecha de actualización', auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        if not self.is_superuser and not self.empresa_id:
            raise ValidationError(
                {'empresa': 'Todo usuario debe pertenecer a una empresa, salvo los administradores de plataforma.'}
            )

    def get_full_name(self):
        return f'{self.nombre} {self.apellido}'.strip()

    def get_short_name(self):
        return self.nombre

    def has_permission(self, codigo):
        """Verifica si el usuario cuenta con el permiso indicado.

        SUPER_ADMIN_SISTEMA (is_superuser) omite la verificación de RBAC.
        Los roles de un usuario siempre pertenecen a su propia empresa
        (lo garantiza UsuarioRol), por lo que esta verificación nunca
        cruza el límite de tenant.
        """
        if not self.is_active:
            return False
        if self.is_superuser:
            return True

        from apps.roles.models import EstadoPermiso, EstadoRol

        roles_activos = self.roles.filter(estado=EstadoRol.ACTIVO)
        if roles_activos.filter(es_administrador_principal=True).exists():
            return True
        return roles_activos.filter(
            permisos__codigo=codigo,
            permisos__estado=EstadoPermiso.ACTIVO,
        ).exists()

    @property
    def es_administrador_empresa(self):
        """Identifica a SUPER_ADMIN_EMPRESA: un usuario con un rol activo marcado
        como administrador principal de su empresa."""
        if not self.is_active:
            return False

        from apps.roles.models import EstadoRol

        return self.roles.filter(estado=EstadoRol.ACTIVO, es_administrador_principal=True).exists()
