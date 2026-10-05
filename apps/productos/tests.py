from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.empresa.models import Empresa
from apps.roles.models import Permiso, Rol, RolPermiso
from apps.roles.services import asignar_rol

from .models import EstadoProducto, Producto, UnidadMedida
from .services import ProductoError, activar_producto, actualizar_producto, desactivar_producto, registrar_producto

Usuario = get_user_model()


def crear_empresa(nombre, nit):
    return Empresa.objects.create(razon_social=nombre, numero_identificacion=nit)


def crear_usuario(email, empresa, password='clave-segura-123'):
    return Usuario.objects.create_user(
        email=email, nombre='Test', apellido='User', password=password, empresa=empresa,
    )


def otorgar_permiso(empresa, usuario, *codigos):
    rol = Rol.objects.create(empresa=empresa, nombre=f'Rol para {usuario.email}')
    for codigo in codigos:
        RolPermiso.objects.create(rol=rol, permiso=Permiso.objects.get(codigo=codigo))
    asignar_rol(usuario, rol)
    return rol


def datos_producto(**overrides):
    datos = {
        'codigo': 'P-001', 'nombre': 'Producto Base', 'descripcion': '',
        'precio': Decimal('100.00'), 'unidad': UnidadMedida.UNIDAD, 'porcentaje_impuesto': Decimal('0'),
    }
    datos.update(overrides)
    return datos


class ProductoModelTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900444001')
        self.empresa_b = crear_empresa('Empresa B', '900444002')

    def test_crear_producto(self):
        producto = Producto.objects.create(empresa=self.empresa_a, **datos_producto())
        self.assertEqual(producto.nombre, 'Producto Base')

    def test_campos_obligatorios(self):
        producto = Producto(empresa=self.empresa_a, precio=Decimal('10.00'))
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_codigo_unico_dentro_de_empresa(self):
        Producto.objects.create(empresa=self.empresa_a, **datos_producto())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Producto.objects.create(empresa=self.empresa_a, **datos_producto(nombre='Otro'))

    def test_mismo_codigo_permitido_en_empresas_diferentes(self):
        Producto.objects.create(empresa=self.empresa_a, **datos_producto())
        Producto.objects.create(empresa=self.empresa_b, **datos_producto())
        self.assertEqual(Producto.objects.filter(codigo='P-001').count(), 2)

    def test_precio_no_puede_ser_negativo(self):
        producto = Producto(empresa=self.empresa_a, **datos_producto(precio=Decimal('-1.00')))
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_estado_inicial_correcto(self):
        producto = Producto.objects.create(empresa=self.empresa_a, **datos_producto())
        self.assertEqual(producto.estado, EstadoProducto.ACTIVO)
        self.assertTrue(producto.esta_activo)


class ProductoServiceTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900444101')
        self.empresa_b = crear_empresa('Empresa B', '900444102')

    def test_registrar_producto_crea_en_tenant_correcto(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        self.assertEqual(producto.empresa, self.empresa_a)

    def test_intento_de_inyectar_empresa_es_rechazado(self):
        with self.assertRaises(ProductoError):
            registrar_producto(self.empresa_a, datos_producto(empresa=self.empresa_b))
        self.assertFalse(Producto.objects.filter(codigo='P-001').exists())

    def test_actualizar_producto_modifica_correctamente(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        actualizar_producto(producto, {'nombre': 'Producto Editado'}, puede_cambiar_precio=True)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Producto Editado')

    def test_actualizar_producto_no_permite_cambiar_empresa(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        with self.assertRaises(ProductoError):
            actualizar_producto(producto, {'empresa': self.empresa_b}, puede_cambiar_precio=True)
        producto.refresh_from_db()
        self.assertEqual(producto.empresa, self.empresa_a)

    def test_service_rechaza_cambio_de_precio_sin_permiso(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        with self.assertRaises(ProductoError):
            actualizar_producto(producto, {'precio': Decimal('999.00')}, puede_cambiar_precio=False)
        producto.refresh_from_db()
        self.assertEqual(producto.precio, Decimal('100.00'))

    def test_activar_producto_funciona(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        desactivar_producto(producto)
        activar_producto(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.estado, EstadoProducto.ACTIVO)

    def test_desactivar_producto_funciona(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        desactivar_producto(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.estado, EstadoProducto.INACTIVO)


class RBACProductoTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900444201')
        self.password = 'clave-segura-123'

    def test_usuario_con_productos_crear_puede_crear(self):
        usuario = crear_usuario('crea@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.crear', 'productos.ver')
        self.client.login(username='crea@example.com', password=self.password)
        response = self.client.post(reverse('productos:crear'), datos_producto())
        self.assertRedirects(response, reverse('productos:lista'))
        self.assertTrue(Producto.objects.filter(codigo='P-001', empresa=self.empresa_a).exists())

    def test_usuario_sin_productos_crear_recibe_403(self):
        crear_usuario('nocrea@example.com', self.empresa_a, self.password)
        self.client.login(username='nocrea@example.com', password=self.password)
        response = self.client.get(reverse('productos:crear'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_productos_ver_puede_consultar(self):
        usuario = crear_usuario('ve@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.ver')
        self.client.login(username='ve@example.com', password=self.password)
        response = self.client.get(reverse('productos:lista'))
        self.assertEqual(response.status_code, 200)

    def test_usuario_sin_productos_ver_recibe_403(self):
        crear_usuario('nove@example.com', self.empresa_a, self.password)
        self.client.login(username='nove@example.com', password=self.password)
        response = self.client.get(reverse('productos:lista'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_productos_editar_puede_editar(self):
        usuario = crear_usuario('edita@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.editar', 'productos.ver')
        producto = registrar_producto(self.empresa_a, datos_producto())
        self.client.login(username='edita@example.com', password=self.password)
        response = self.client.post(
            reverse('productos:editar', args=[producto.pk]),
            {'codigo': 'P-001', 'nombre': 'Producto Editado', 'descripcion': '', 'unidad': UnidadMedida.UNIDAD,
             'porcentaje_impuesto': '0'},
        )
        self.assertRedirects(response, reverse('productos:detalle', args=[producto.pk]))
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Producto Editado')

    def test_usuario_sin_productos_editar_recibe_403(self):
        crear_usuario('noedita@example.com', self.empresa_a, self.password)
        producto = registrar_producto(self.empresa_a, datos_producto())
        self.client.login(username='noedita@example.com', password=self.password)
        response = self.client.get(reverse('productos:editar', args=[producto.pk]))
        self.assertEqual(response.status_code, 403)

    def test_usuario_sin_cambiar_precio_no_puede_cambiar_precio(self):
        usuario = crear_usuario('editorsp@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.editar', 'productos.ver')
        producto = registrar_producto(self.empresa_a, datos_producto())
        self.client.login(username='editorsp@example.com', password=self.password)
        response = self.client.post(
            reverse('productos:editar', args=[producto.pk]),
            {'codigo': 'P-001', 'nombre': 'Nombre Nuevo', 'descripcion': '', 'precio': '999.00',
             'unidad': UnidadMedida.UNIDAD, 'porcentaje_impuesto': '0'},
        )
        self.assertRedirects(response, reverse('productos:detalle', args=[producto.pk]))
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Nombre Nuevo')
        self.assertEqual(producto.precio, Decimal('100.00'))

    def test_usuario_con_cambiar_precio_puede_cambiar_precio(self):
        usuario = crear_usuario('editorcp@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.editar', 'productos.ver', 'productos.cambiar_precio')
        producto = registrar_producto(self.empresa_a, datos_producto())
        self.client.login(username='editorcp@example.com', password=self.password)
        response = self.client.post(
            reverse('productos:editar', args=[producto.pk]),
            {'codigo': 'P-001', 'nombre': 'Producto Base', 'descripcion': '', 'precio': '150.00',
             'unidad': UnidadMedida.UNIDAD, 'porcentaje_impuesto': '0'},
        )
        self.assertRedirects(response, reverse('productos:detalle', args=[producto.pk]))
        producto.refresh_from_db()
        self.assertEqual(producto.precio, Decimal('150.00'))

    def test_usuario_sin_productos_activar_no_puede_activar(self):
        usuario = crear_usuario('noactiva@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.ver')
        producto = registrar_producto(self.empresa_a, datos_producto())
        desactivar_producto(producto)
        self.client.login(username='noactiva@example.com', password=self.password)
        response = self.client.post(reverse('productos:activar', args=[producto.pk]))
        self.assertEqual(response.status_code, 403)

    def test_usuario_sin_productos_desactivar_no_puede_desactivar(self):
        usuario = crear_usuario('nodesactiva@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'productos.ver')
        producto = registrar_producto(self.empresa_a, datos_producto())
        self.client.login(username='nodesactiva@example.com', password=self.password)
        response = self.client.post(reverse('productos:desactivar', args=[producto.pk]))
        self.assertEqual(response.status_code, 403)


class MultiTenancyProductoTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900444301')
        self.empresa_b = crear_empresa('Empresa B', '900444302')
        self.password = 'clave-segura-123'

        self.usuario_a = crear_usuario('a@example.com', self.empresa_a, self.password)
        otorgar_permiso(
            self.empresa_a, self.usuario_a,
            'productos.ver', 'productos.crear', 'productos.editar', 'productos.activar', 'productos.desactivar',
        )
        self.usuario_b = crear_usuario('b@example.com', self.empresa_b, self.password)
        otorgar_permiso(self.empresa_b, self.usuario_b, 'productos.ver')

        self.producto_a = registrar_producto(self.empresa_a, datos_producto(codigo='A-001', nombre='Producto A'))
        self.producto_b = registrar_producto(self.empresa_b, datos_producto(codigo='B-001', nombre='Producto B'))

    def test_empresa_a_solo_ve_productos_a(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('productos:lista'))
        self.assertContains(response, 'Producto A')
        self.assertNotContains(response, 'Producto B')

    def test_empresa_b_solo_ve_productos_b(self):
        self.client.login(username='b@example.com', password=self.password)
        response = self.client.get(reverse('productos:lista'))
        self.assertContains(response, 'Producto B')
        self.assertNotContains(response, 'Producto A')

    def test_empresa_a_no_puede_consultar_producto_b(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('productos:detalle', args=[self.producto_b.pk]))
        self.assertEqual(response.status_code, 403)

    def test_empresa_b_no_puede_consultar_producto_a(self):
        self.client.login(username='b@example.com', password=self.password)
        response = self.client.get(reverse('productos:detalle', args=[self.producto_a.pk]))
        self.assertEqual(response.status_code, 403)

    def test_idor_mediante_url_recibe_403(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('productos:editar', args=[self.producto_b.pk]))
        self.assertEqual(response.status_code, 403)

    def test_empresa_id_enviado_por_post_no_cambia_tenant(self):
        self.client.login(username='a@example.com', password=self.password)
        self.client.post(reverse('productos:crear'), {
            **datos_producto(codigo='A-002', nombre='Producto Inyectado'),
            'empresa': self.empresa_b.pk, 'empresa_id': self.empresa_b.pk,
        })
        producto_creado = Producto.objects.get(codigo='A-002')
        self.assertEqual(producto_creado.empresa, self.empresa_a)


class EstadoProductoTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900444401')

    def test_producto_inactivo_conserva_sus_datos(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        desactivar_producto(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.estado, EstadoProducto.INACTIVO)
        self.assertEqual(producto.nombre, 'Producto Base')
        self.assertEqual(producto.precio, Decimal('100.00'))

    def test_producto_puede_volver_a_activarse(self):
        producto = registrar_producto(self.empresa_a, datos_producto())
        desactivar_producto(producto)
        activar_producto(producto)
        producto.refresh_from_db()
        self.assertEqual(producto.estado, EstadoProducto.ACTIVO)
