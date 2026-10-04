from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
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

    def get_full_name(self):
        return f'{self.nombre} {self.apellido}'.strip()

    def get_short_name(self):
        return self.nombre
