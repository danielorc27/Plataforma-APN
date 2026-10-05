from django.urls import path

from . import views

app_name = 'empresa'

urlpatterns = [
    path('', views.empresa_ver, name='ver'),
    path('editar/', views.empresa_editar, name='editar'),

    path('admin/', views.admin_empresas_lista, name='admin_lista'),
    path('admin/crear/', views.admin_empresa_crear, name='admin_crear'),
    path('admin/<int:pk>/', views.admin_empresa_detalle, name='admin_detalle'),
    path('admin/<int:pk>/activar/', views.admin_empresa_activar, name='admin_activar'),
    path('admin/<int:pk>/desactivar/', views.admin_empresa_desactivar, name='admin_desactivar'),

    path('<int:pk>/', views.empresa_detalle, name='detalle'),
]
