from django import forms
from django.contrib.auth import get_user_model

from .models import Empresa


class EmpresaCreateForm(forms.ModelForm):
    """Usado por SUPER_ADMIN_SISTEMA para registrar una empresa (HU-001)."""

    class Meta:
        model = Empresa
        fields = [
            'razon_social', 'tipo_identificacion', 'numero_identificacion',
            'direccion', 'municipio', 'telefono', 'email',
        ]


class EmpresaEditForm(forms.ModelForm):
    """Usado por SUPER_ADMIN_EMPRESA para actualizar SU empresa (HU-003).

    No incluye tipo/número de identificación (inmutables tras el registro,
    ver decisión en apps/empresa/services.py) ni estado (solo lo controla
    SUPER_ADMIN_SISTEMA). Al no exponer `empresa` ni `estado` como campos,
    el formulario no permite seleccionar/cambiar de empresa ni su estado.
    """

    class Meta:
        model = Empresa
        fields = ['razon_social', 'direccion', 'municipio', 'telefono', 'email']


class AdministradorInicialForm(forms.Form):
    """Datos del usuario administrador principal creado junto con la empresa."""

    email = forms.EmailField(label='Correo electrónico')
    nombre = forms.CharField(label='Nombre', max_length=150)
    apellido = forms.CharField(label='Apellido', max_length=150)
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    def clean_email(self):
        Usuario = get_user_model()
        email = self.cleaned_data['email'].lower()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned
