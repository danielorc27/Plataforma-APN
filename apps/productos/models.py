from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UnidadMedida(models.TextChoices):
    UNIDAD = 'UNIDAD', 'Unidad'
    KILOGRAMO = 'KILOGRAMO', 'Kilogramo'
    GRAMO = 'GRAMO', 'Gramo'
    LITRO = 'LITRO', 'Litro'
    MILILITRO = 'MILILITRO', 'Mililitro'
    METRO = 'METRO', 'Metro'
    CAJA = 'CAJA', 'Caja'
    SERVICIO = 'SERVICIO', 'Servicio'


class EstadoProducto(models.TextChoices):
    ACTIVO = 'ACTIVO', 'Activo'
    INACTIVO = 'INACTIVO', 'Inactivo'


class Producto(models.Model):
    """Catálogo comercial de una Empresa. El stock/inventario se maneja en un módulo aparte."""

    empresa = models.ForeignKey(
        'empresa.Empresa', verbose_name='empresa', related_name='productos', on_delete=models.PROTECT,
    )

    codigo = models.CharField('código / referencia', max_length=50)
    nombre = models.CharField('nombre', max_length=255)
    descripcion = models.TextField('descripción', blank=True)

    precio = models.DecimalField(
        'precio', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))],
    )
    unidad = models.CharField('unidad', max_length=20, choices=UnidadMedida.choices, default=UnidadMedida.UNIDAD)

    porcentaje_impuesto = models.DecimalField(
        'porcentaje de impuesto', max_digits=5, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        help_text='Tasa aplicable (p. ej. 19.00 para un IVA del 19%). La codificación tributaria '
                   'específica de DIAN/Factus (tipo de impuesto, código) se definirá en la fase de Facturación.',
    )

    estado = models.CharField('estado', max_length=20, choices=EstadoProducto.choices, default=EstadoProducto.ACTIVO)

    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'codigo'], name='unique_producto_codigo_por_empresa'),
        ]

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'

    @property
    def esta_activo(self):
        return self.estado == EstadoProducto.ACTIVO
