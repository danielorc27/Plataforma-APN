from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.empresa.models import Empresa
from apps.roles.models import Permiso, Rol, RolPermiso
from apps.roles.services import asignar_rol

from .models import Cliente, TipoIdentificacionCliente
from .services import ClienteError, actualizar_cliente, registrar_cliente

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


class ClienteModelTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900333001')
        self.empresa_b = crear_empresa('Empresa B', '900333002')

    def test_crear_cliente(self):
        cliente = Cliente.objects.create(
            empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.CC,
            numero_identificacion='123456', nombre='Juan Pérez',
        )
        self.assertEqual(cliente.nombre, 'Juan Pérez')

    def test_campos_obligatorios(self):
        cliente = Cliente(empresa=self.empresa_a, numero_identificacion='123456')
        with self.assertRaises(ValidationError):
            cliente.full_clean()

    def test_email_invalido_es_rechazado(self):
        cliente = Cliente(
            empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.CC,
            numero_identificacion='123456', nombre='Juan', email='no-es-email',
        )
        with self.assertRaises(ValidationError):
            cliente.full_clean()

    def test_identificacion_unica_dentro_de_empresa(self):
        Cliente.objects.create(
            empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.CC,
            numero_identificacion='123456', nombre='Juan',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Cliente.objects.create(
                    empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.CC,
                    numero_identificacion='123456', nombre='Otro Juan',
                )

    def test_misma_identificacion_permitida_en_empresas_diferentes(self):
        Cliente.objects.create(
            empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.CC,
            numero_identificacion='123456', nombre='Juan',
        )
        Cliente.objects.create(
            empresa=self.empresa_b, tipo_identificacion=TipoIdentificacionCliente.CC,
            numero_identificacion='123456', nombre='Juan Otro',
        )
        self.assertEqual(Cliente.objects.filter(numero_identificacion='123456').count(), 2)

    def test_restriccion_incluye_tipo_identificacion(self):
        Cliente.objects.create(
            empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.CC,
            numero_identificacion='123456', nombre='Juan',
        )
        cliente_nit = Cliente.objects.create(
            empresa=self.empresa_a, tipo_identificacion=TipoIdentificacionCliente.NIT,
            numero_identificacion='123456', nombre='Empresa Juan SAS',
        )
        self.assertIsNotNone(cliente_nit.pk)


class RegistrarClienteServiceTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900333101')
        self.empresa_b = crear_empresa('Empresa B', '900333102')

    def test_registrar_cliente_crea_en_empresa_correcta(self):
        cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '555111', 'nombre': 'Ana',
        })
        self.assertEqual(cliente.empresa, self.empresa_a)

    def test_no_es_posible_forzar_otra_empresa_desde_los_datos(self):
        with self.assertRaises(ClienteError):
            registrar_cliente(self.empresa_a, {
                'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '555222',
                'nombre': 'Ana', 'empresa': self.empresa_b,
            })
        self.assertFalse(Cliente.objects.filter(numero_identificacion='555222').exists())

    def test_actualizar_cliente_modifica_solo_cliente_de_su_empresa(self):
        cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '555333', 'nombre': 'Ana',
        })
        actualizar_cliente(cliente, {'nombre': 'Ana María'})
        cliente.refresh_from_db()
        self.assertEqual(cliente.nombre, 'Ana María')
        self.assertEqual(cliente.empresa, self.empresa_a)

    def test_actualizar_cliente_no_permite_cambiar_empresa(self):
        cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '555444', 'nombre': 'Ana',
        })
        with self.assertRaises(ClienteError):
            actualizar_cliente(cliente, {'nombre': 'Ana', 'empresa': self.empresa_b})
        cliente.refresh_from_db()
        self.assertEqual(cliente.empresa, self.empresa_a)


class RBACClienteTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900333201')
        self.password = 'clave-segura-123'

    def test_usuario_con_clientes_crear_puede_crear(self):
        usuario = crear_usuario('crea@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'clientes.crear', 'clientes.ver')
        self.client.login(username='crea@example.com', password=self.password)
        response = self.client.post(reverse('clientes:crear'), {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '700001',
            'nombre': 'Cliente Uno', 'email': '', 'telefono': '', 'direccion': '',
        })
        self.assertRedirects(response, reverse('clientes:lista'))
        self.assertTrue(Cliente.objects.filter(numero_identificacion='700001', empresa=self.empresa_a).exists())

    def test_usuario_sin_clientes_crear_recibe_403(self):
        crear_usuario('nocrea@example.com', self.empresa_a, self.password)
        self.client.login(username='nocrea@example.com', password=self.password)
        response = self.client.get(reverse('clientes:crear'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_clientes_ver_puede_consultar(self):
        usuario = crear_usuario('ve@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'clientes.ver')
        self.client.login(username='ve@example.com', password=self.password)
        response = self.client.get(reverse('clientes:lista'))
        self.assertEqual(response.status_code, 200)

    def test_usuario_sin_clientes_ver_recibe_403(self):
        crear_usuario('nove@example.com', self.empresa_a, self.password)
        self.client.login(username='nove@example.com', password=self.password)
        response = self.client.get(reverse('clientes:lista'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_clientes_editar_puede_editar(self):
        usuario = crear_usuario('edita@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, usuario, 'clientes.editar', 'clientes.ver')
        cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '700002',
            'nombre': 'Cliente Dos',
        })
        self.client.login(username='edita@example.com', password=self.password)
        response = self.client.post(reverse('clientes:editar', args=[cliente.pk]), {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '700002',
            'nombre': 'Cliente Dos Editado', 'email': '', 'telefono': '', 'direccion': '',
        })
        self.assertRedirects(response, reverse('clientes:detalle', args=[cliente.pk]))
        cliente.refresh_from_db()
        self.assertEqual(cliente.nombre, 'Cliente Dos Editado')

    def test_usuario_sin_clientes_editar_recibe_403(self):
        crear_usuario('noedita@example.com', self.empresa_a, self.password)
        cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '700003',
            'nombre': 'Cliente Tres',
        })
        self.client.login(username='noedita@example.com', password=self.password)
        response = self.client.get(reverse('clientes:editar', args=[cliente.pk]))
        self.assertEqual(response.status_code, 403)


class MultiTenancyClienteTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900333301')
        self.empresa_b = crear_empresa('Empresa B', '900333302')
        self.password = 'clave-segura-123'

        self.usuario_a = crear_usuario('a@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, self.usuario_a, 'clientes.ver', 'clientes.crear', 'clientes.editar')

        self.usuario_b = crear_usuario('b@example.com', self.empresa_b, self.password)
        otorgar_permiso(self.empresa_b, self.usuario_b, 'clientes.ver', 'clientes.crear', 'clientes.editar')

        self.cliente_a = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '800001',
            'nombre': 'Cliente A',
        })
        self.cliente_b = registrar_cliente(self.empresa_b, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '800002',
            'nombre': 'Cliente B',
        })

    def test_empresa_a_solamente_ve_clientes_a(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('clientes:lista'))
        self.assertContains(response, 'Cliente A')
        self.assertNotContains(response, 'Cliente B')

    def test_empresa_b_solamente_ve_clientes_b(self):
        self.client.login(username='b@example.com', password=self.password)
        response = self.client.get(reverse('clientes:lista'))
        self.assertContains(response, 'Cliente B')
        self.assertNotContains(response, 'Cliente A')

    def test_empresa_a_no_accede_al_detalle_de_cliente_b(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('clientes:detalle', args=[self.cliente_b.pk]))
        self.assertEqual(response.status_code, 403)

    def test_empresa_b_no_accede_al_detalle_de_cliente_a(self):
        self.client.login(username='b@example.com', password=self.password)
        response = self.client.get(reverse('clientes:detalle', args=[self.cliente_a.pk]))
        self.assertEqual(response.status_code, 403)

    def test_usuario_a_puede_acceder_a_su_propio_cliente(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('clientes:detalle', args=[self.cliente_a.pk]))
        self.assertEqual(response.status_code, 200)

    def test_idor_en_edicion_es_rechazado(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('clientes:editar', args=[self.cliente_b.pk]))
        self.assertEqual(response.status_code, 403)

    def test_empresa_id_enviado_por_post_no_cambia_el_tenant(self):
        self.client.login(username='a@example.com', password=self.password)
        self.client.post(reverse('clientes:crear'), {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '800003',
            'nombre': 'Cliente Inyectado', 'email': '', 'telefono': '', 'direccion': '',
            'empresa': self.empresa_b.pk, 'empresa_id': self.empresa_b.pk,
        })
        cliente_creado = Cliente.objects.get(numero_identificacion='800003')
        self.assertEqual(cliente_creado.empresa, self.empresa_a)


class EdicionIdentificacionClienteTests(TestCase):
    """HU-010: la identificación del Cliente sí puede corregirse (a diferencia de Empresa)."""

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900333401')
        self.password = 'clave-segura-123'
        self.usuario = crear_usuario('editor@example.com', self.empresa_a, self.password)
        otorgar_permiso(self.empresa_a, self.usuario, 'clientes.ver', 'clientes.editar')
        self.cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '900001',
            'nombre': 'Cliente Original',
        })
        self.otro_cliente = registrar_cliente(self.empresa_a, {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '900002',
            'nombre': 'Otro Cliente',
        })

    def test_puede_corregir_numero_identificacion(self):
        self.client.login(username='editor@example.com', password=self.password)
        response = self.client.post(reverse('clientes:editar', args=[self.cliente.pk]), {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '900099',
            'nombre': 'Cliente Original', 'email': '', 'telefono': '', 'direccion': '',
        })
        self.assertRedirects(response, reverse('clientes:detalle', args=[self.cliente.pk]))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.numero_identificacion, '900099')

    def test_edicion_no_puede_generar_duplicados(self):
        self.client.login(username='editor@example.com', password=self.password)
        response = self.client.post(reverse('clientes:editar', args=[self.cliente.pk]), {
            'tipo_identificacion': TipoIdentificacionCliente.CC, 'numero_identificacion': '900002',
            'nombre': 'Cliente Original', 'email': '', 'telefono': '', 'direccion': '',
        })
        self.assertEqual(response.status_code, 200)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.numero_identificacion, '900001')
