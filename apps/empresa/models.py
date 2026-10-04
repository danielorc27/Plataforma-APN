from django.core.validators import RegexValidator
from django.db import models


class TipoIdentificacion(models.TextChoices):
    NIT = 'NIT', 'NIT'
    CC = 'CC', 'Cédula de ciudadanía'
    CE = 'CE', 'Cédula de extranjería'
    PASAPORTE = 'PASAPORTE', 'Pasaporte'


class EstadoEmpresa(models.TextChoices):
    ACTIVA = 'ACTIVA', 'Activa'
    INACTIVA = 'INACTIVA', 'Inactiva'


validar_numero_identificacion = RegexValidator(
    regex=r'^\d{5,20}$',
    message='La identificación debe contener únicamente números (5 a 20 dígitos).',
)


class Empresa(models.Model):
    razon_social = models.CharField('razón social', max_length=255)

    tipo_identificacion = models.CharField(
        'tipo de identificación',
        max_length=20,
        choices=TipoIdentificacion.choices,
        default=TipoIdentificacion.NIT,
    )
    numero_identificacion = models.CharField(
        'número de identificación',
        max_length=20,
        unique=True,
        validators=[validar_numero_identificacion],
        help_text='Identificación tributaria de la empresa (NIT u otro documento válido).',
    )

    direccion = models.CharField('dirección', max_length=255, blank=True)
    municipio = models.CharField('municipio / ciudad', max_length=150, blank=True)
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    email = models.EmailField('correo electrónico', blank=True)

    estado = models.CharField(
        'estado',
        max_length=20,
        choices=EstadoEmpresa.choices,
        default=EstadoEmpresa.ACTIVA,
    )

    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'empresa'
        verbose_name_plural = 'empresas'
        ordering = ['razon_social']

    def __str__(self):
        return self.razon_social

    @property
    def esta_activa(self):
        return self.estado == EstadoEmpresa.ACTIVA
