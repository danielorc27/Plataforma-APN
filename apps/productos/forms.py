from django import forms

from .models import Producto


class ProductoForm(forms.ModelForm):
    """Usado para crear y editar un Producto.

    No incluye `empresa`: el tenant siempre se determina en la vista/
    servicio a partir de request.user.empresa, nunca del formulario.

    Si `puede_cambiar_precio=False`, el campo `precio` se elimina del
    formulario por completo (no solo se oculta visualmente): el backend
    (apps.productos.services.actualizar_producto) también rechaza
    explícitamente cualquier intento de modificarlo.
    """

    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'precio', 'unidad', 'porcentaje_impuesto']

    def __init__(self, *args, puede_cambiar_precio=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not puede_cambiar_precio:
            self.fields.pop('precio')
