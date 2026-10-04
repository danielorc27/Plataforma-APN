from django.urls import path

from . import views

app_name = 'empresa'

urlpatterns = [
    path('<int:pk>/', views.empresa_detalle, name='detalle'),
]
