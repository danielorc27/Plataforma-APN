from django import forms
from django.contrib.auth.forms import AuthenticationForm, ReadOnlyPasswordHashField

from .models import Usuario


class EmailAuthenticationForm(AuthenticationForm):
    """Login nativo de Django, usando email en lugar de username."""

    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )


class UsuarioCreationForm(forms.ModelForm):
    """Formulario para crear usuarios desde el Django Admin."""

    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return password2

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['password1'])
        if commit:
            usuario.save()
        return usuario


class UsuarioChangeForm(forms.ModelForm):
    """Formulario para editar usuarios desde el Django Admin."""

    password = ReadOnlyPasswordHashField(
        label='Contraseña',
        help_text='Las contraseñas no se almacenan en texto plano. '
                   'Para cambiarla, usa el enlace "cambiar contraseña" del admin.',
    )

    class Meta:
        model = Usuario
        fields = ('email', 'password', 'nombre', 'apellido', 'is_active', 'is_staff')

    def clean_password(self):
        return self.initial['password']
