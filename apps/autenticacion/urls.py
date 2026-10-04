from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailAuthenticationForm

app_name = 'autenticacion'

urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='autenticacion/login.html',
            authentication_form=EmailAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('app/usuarios/', views.usuarios_lista, name='usuarios_lista'),
    path('app/usuarios/crear/', views.usuarios_crear, name='usuarios_crear'),
]
