from django.urls import path

from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.productos_lista, name='lista'),
    path('crear/', views.producto_crear, name='crear'),
    path('<int:pk>/', views.producto_detalle, name='detalle'),
    path('<int:pk>/editar/', views.producto_editar, name='editar'),
    path('<int:pk>/activar/', views.producto_activar, name='activar'),
    path('<int:pk>/desactivar/', views.producto_desactivar, name='desactivar'),
]
