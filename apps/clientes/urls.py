from django.urls import path

from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.clientes_lista, name='lista'),
    path('crear/', views.cliente_crear, name='crear'),
    path('<int:pk>/', views.cliente_detalle, name='detalle'),
    path('<int:pk>/editar/', views.cliente_editar, name='editar'),
]
