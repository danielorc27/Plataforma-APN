from django.core.validators import RegexValidator
from django.db import models


class TipoIdentificacionCliente(models.TextChoices):
    CC = 'CC', 'Cédula de ciudadanía'
    NIT = 'NIT', 'NIT'
    CE = 'CE', 'Cédula de extranjería'
    TI = 'TI', 'Tarjeta de identidad'
    PASAPORTE = 'PASAPORTE', 'Pasaporte'


validar_numero_identificacion = RegexValidator(
    regex=r'^[A-Za-z0-9-]{3,20}$',
    message='La identificación debe tener entre 3 y 20 caracteres alfanuméricos.',
)


class Cliente(models.Model):
    """Cliente de una Empresa (tenant). No se comparte entre empresas."""

    empresa = models.ForeignKey(
        'empresa.Empresa', verbose_name='empresa', related_name='clientes', on_delete=models.PROTECT,
    )

    tipo_identificacion = models.CharField(
        'tipo de identificación', max_length=20,
        choices=TipoIdentificacionCliente.choices, default=TipoIdentificacionCliente.CC,
    )
    numero_identificacion = models.CharField(
        'número de identificación', max_length=20, validators=[validar_numero_identificacion],
    )

    nombre = models.CharField('nombre / razón social', max_length=255)
    email = models.EmailField('correo electrónico', blank=True)
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    direccion = models.CharField('dirección', max_length=255, blank=True)

    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'tipo_identificacion', 'numero_identificacion'],
                name='unique_cliente_identificacion_por_empresa',
            ),
        ]

    def __str__(self):
        return self.nombre

    @property
    def es_persona_juridica(self):
        return self.tipo_identificacion == TipoIdentificacionCliente.NIT
