from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Usado para crear y editar un Cliente.

    No incluye `empresa`: el tenant siempre se determina en la vista/
    servicio a partir de request.user.empresa, nunca del formulario.
    """

    class Meta:
        model = Cliente
        fields = ['tipo_identificacion', 'numero_identificacion', 'nombre', 'email', 'telefono', 'direccion']
