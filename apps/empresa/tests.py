from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.roles.models import Permiso, Rol, RolPermiso
from apps.roles.services import asignar_rol

from .models import Empresa, EstadoEmpresa, TipoIdentificacion
from .services import EmpresaError, registrar_empresa

Usuario = get_user_model()


def crear_empresa(nombre, nit):
    return Empresa.objects.create(razon_social=nombre, numero_identificacion=nit)


def crear_usuario(email, empresa, password='clave-segura-123'):
    return Usuario.objects.create_user(
        email=email, nombre='Test', apellido='User', password=password, empresa=empresa,
    )


class EmpresaModelTests(TestCase):

    def test_crear_empresa(self):
        empresa = Empresa.objects.create(
            razon_social='Empresa Uno SAS',
            tipo_identificacion=TipoIdentificacion.NIT,
            numero_identificacion='900123456',
        )
        self.assertEqual(empresa.estado, EstadoEmpresa.ACTIVA)
        self.assertTrue(empresa.esta_activa)

    def test_crear_dos_empresas_diferentes(self):
        Empresa.objects.create(razon_social='Empresa A', numero_identificacion='900000001')
        Empresa.objects.create(razon_social='Empresa B', numero_identificacion='900000002')
        self.assertEqual(Empresa.objects.count(), 2)

    def test_identificacion_duplicada_no_permitida(self):
        Empresa.objects.create(razon_social='Empresa A', numero_identificacion='900000001')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Empresa.objects.create(razon_social='Empresa Duplicada', numero_identificacion='900000001')

    def test_empresa_inactiva_mantiene_estado(self):
        empresa = Empresa.objects.create(
            razon_social='Empresa Inactiva',
            numero_identificacion='900000003',
            estado=EstadoEmpresa.INACTIVA,
        )
        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, EstadoEmpresa.INACTIVA)
        self.assertFalse(empresa.esta_activa)

    def test_numero_identificacion_invalido_no_pasa_validacion(self):
        empresa = Empresa(razon_social='Empresa X', numero_identificacion='NIT-ABC')
        with self.assertRaises(ValidationError):
            empresa.full_clean()


class UsuarioEmpresaTests(TestCase):

    def test_usuario_no_superusuario_requiere_empresa(self):
        usuario = Usuario(email='sin-empresa@example.com', nombre='Sin', apellido='Empresa')
        usuario.set_password('clave-segura-123')
        with self.assertRaises(ValidationError):
            usuario.full_clean()

    def test_superusuario_no_requiere_empresa(self):
        usuario = Usuario.objects.create_superuser(
            email='admin@example.com', nombre='Admin', apellido='Sistema', password='clave-segura-123',
        )
        usuario.full_clean()


class AislamientoMultiTenantTests(TestCase):

    def setUp(self):
        self.empresa_a = Empresa.objects.create(razon_social='Empresa A', numero_identificacion='900000001')
        self.empresa_b = Empresa.objects.create(razon_social='Empresa B', numero_identificacion='900000002')
        self.password = 'clave-segura-123'
        self.usuario_a = Usuario.objects.create_user(
            email='a@example.com', nombre='Usuario', apellido='A',
            password=self.password, empresa=self.empresa_a,
        )
        self.usuario_b = Usuario.objects.create_user(
            email='b@example.com', nombre='Usuario', apellido='B',
            password=self.password, empresa=self.empresa_b,
        )

    def test_usuario_a_pertenece_a_empresa_a(self):
        self.assertEqual(self.usuario_a.empresa, self.empresa_a)

    def test_usuario_b_pertenece_a_empresa_b(self):
        self.assertEqual(self.usuario_b.empresa, self.empresa_b)

    def test_usuario_a_no_tiene_como_actual_a_empresa_b(self):
        self.assertNotEqual(self.usuario_a.empresa, self.empresa_b)

    def test_usuario_b_no_tiene_como_actual_a_empresa_a(self):
        self.assertNotEqual(self.usuario_b.empresa, self.empresa_a)

    def test_usuario_solo_puede_ver_su_propia_empresa_por_url(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('empresa:detalle', args=[self.empresa_a.pk]))
        self.assertEqual(response.status_code, 200)

    def test_usuario_a_no_puede_ver_empresa_b_modificando_url(self):
        self.client.login(username='a@example.com', password=self.password)
        response = self.client.get(reverse('empresa:detalle', args=[self.empresa_b.pk]))
        self.assertEqual(response.status_code, 403)

    def test_usuario_b_no_puede_ver_empresa_a_modificando_url(self):
        self.client.login(username='b@example.com', password=self.password)
        response = self.client.get(reverse('empresa:detalle', args=[self.empresa_a.pk]))
        self.assertEqual(response.status_code, 403)

    def test_usuario_no_autenticado_no_accede_a_detalle_empresa(self):
        response = self.client.get(reverse('empresa:detalle', args=[self.empresa_a.pk]))
        self.assertEqual(response.status_code, 302)

    def test_usuario_no_puede_modificar_su_empresa_via_post(self):
        self.client.login(username='a@example.com', password=self.password)
        app_url = reverse('core:app_home')
        self.client.post(app_url, {'empresa_id': self.empresa_b.pk, 'empresa': self.empresa_b.pk})
        self.usuario_a.refresh_from_db()
        self.assertEqual(self.usuario_a.empresa, self.empresa_a)

    def test_usuario_no_staff_no_puede_editar_usuarios_en_admin(self):
        self.client.login(username='a@example.com', password=self.password)
        admin_url = reverse('admin:autenticacion_usuario_change', args=[self.usuario_a.pk])
        response = self.client.get(admin_url)
        self.assertNotEqual(response.status_code, 200)


class RegistrarEmpresaServiceTests(TestCase):
    """HU-001: registrar empresa (SUPER_ADMIN_SISTEMA)."""

    def test_superadmin_sistema_puede_crear_empresa(self):
        empresa, admin = registrar_empresa(
            datos_empresa={
                'razon_social': 'Nueva Empresa SAS',
                'tipo_identificacion': TipoIdentificacion.NIT,
                'numero_identificacion': '900111222',
            },
            datos_administrador={
                'email': 'admin@nueva.com', 'nombre': 'Ana', 'apellido': 'Admin', 'password': 'clave-segura-123',
            },
        )
        self.assertTrue(Empresa.objects.filter(pk=empresa.pk).exists())
        self.assertEqual(admin.empresa, empresa)

    def test_empresa_queda_correctamente_registrada(self):
        empresa, _admin = registrar_empresa(
            datos_empresa={
                'razon_social': 'Empresa X', 'tipo_identificacion': TipoIdentificacion.NIT,
                'numero_identificacion': '900111333',
            },
            datos_administrador={
                'email': 'x@example.com', 'nombre': 'X', 'apellido': 'Y', 'password': 'clave-segura-123',
            },
        )
        empresa.refresh_from_db()
        self.assertEqual(empresa.razon_social, 'Empresa X')
        self.assertEqual(empresa.estado, EstadoEmpresa.ACTIVA)

    def test_no_permite_identificacion_duplicada(self):
        crear_empresa('Existente', '900000001')
        with self.assertRaises(EmpresaError):
            registrar_empresa(
                datos_empresa={
                    'razon_social': 'Duplicada', 'tipo_identificacion': TipoIdentificacion.NIT,
                    'numero_identificacion': '900000001',
                },
                datos_administrador={
                    'email': 'dup@example.com', 'nombre': 'D', 'apellido': 'D', 'password': 'clave-segura-123',
                },
            )

    def test_no_permite_datos_obligatorios_faltantes(self):
        with self.assertRaises(EmpresaError):
            registrar_empresa(
                datos_empresa={
                    'razon_social': '', 'tipo_identificacion': TipoIdentificacion.NIT,
                    'numero_identificacion': '900111444',
                },
                datos_administrador={
                    'email': 'a@example.com', 'nombre': 'A', 'apellido': 'B', 'password': 'clave-segura-123',
                },
            )

    def test_email_invalido_es_rechazado(self):
        with self.assertRaises(EmpresaError):
            registrar_empresa(
                datos_empresa={
                    'razon_social': 'Empresa Email', 'tipo_identificacion': TipoIdentificacion.NIT,
                    'numero_identificacion': '900111777',
                },
                datos_administrador={
                    'email': 'correo-invalido', 'nombre': 'Z', 'apellido': 'Z', 'password': 'clave-segura-123',
                },
            )

    def test_asigna_administrador_inicial_con_rol_principal(self):
        _empresa, admin = registrar_empresa(
            datos_empresa={
                'razon_social': 'Empresa Y', 'tipo_identificacion': TipoIdentificacion.NIT,
                'numero_identificacion': '900111555',
            },
            datos_administrador={
                'email': 'y@example.com', 'nombre': 'Y', 'apellido': 'Y', 'password': 'clave-segura-123',
            },
        )
        self.assertTrue(admin.es_administrador_empresa)

    def test_operacion_es_atomica_ante_fallo(self):
        with self.assertRaises(EmpresaError):
            registrar_empresa(
                datos_empresa={
                    'razon_social': 'Empresa Z', 'tipo_identificacion': TipoIdentificacion.NIT,
                    'numero_identificacion': '900111666',
                },
                datos_administrador={
                    'email': 'correo-invalido', 'nombre': 'Z', 'apellido': 'Z', 'password': 'clave-segura-123',
                },
            )
        self.assertFalse(Empresa.objects.filter(numero_identificacion='900111666').exists())


class AdministracionGlobalViewTests(TestCase):
    """HU-001 (interfaz) + aislamiento: pantallas de SUPER_ADMIN_SISTEMA."""

    def setUp(self):
        self.password = 'clave-segura-123'
        self.superadmin = Usuario.objects.create_superuser(
            email='root@example.com', nombre='Root', apellido='Sistema', password=self.password,
        )

    def test_superadmin_sistema_puede_listar_y_crear_empresa_por_http(self):
        self.client.login(username='root@example.com', password=self.password)
        response = self.client.get(reverse('empresa:admin_lista'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('empresa:admin_crear'), {
            'empresa-razon_social': 'Empresa HTTP',
            'empresa-tipo_identificacion': TipoIdentificacion.NIT,
            'empresa-numero_identificacion': '900999001',
            'empresa-direccion': '', 'empresa-municipio': '', 'empresa-telefono': '', 'empresa-email': '',
            'admin-email': 'adminhttp@example.com', 'admin-nombre': 'Admin', 'admin-apellido': 'Http',
            'admin-password1': 'clave-segura-123', 'admin-password2': 'clave-segura-123',
        })
        self.assertRedirects(response, reverse('empresa:admin_lista'))
        empresa_creada = Empresa.objects.get(numero_identificacion='900999001')
        admin_creado = Usuario.objects.get(email='adminhttp@example.com')
        self.assertEqual(admin_creado.empresa, empresa_creada)
        self.assertTrue(admin_creado.es_administrador_empresa)

    def test_usuario_normal_no_puede_acceder_a_administracion_global(self):
        empresa = crear_empresa('Empresa A', '900999002')
        crear_usuario('user@example.com', empresa, self.password)
        self.client.login(username='user@example.com', password=self.password)
        response = self.client.get(reverse('empresa:admin_lista'))
        self.assertEqual(response.status_code, 403)


class ConsultarEmpresaViewTests(TestCase):
    """HU-002: consultar la empresa actual."""

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900222001')
        self.empresa_b = crear_empresa('Empresa B', '900222002')
        self.rol_admin_a = Rol.objects.create(
            empresa=self.empresa_a, nombre='Administrador', es_administrador_principal=True,
        )
        self.password = 'clave-segura-123'
        self.admin_a = crear_usuario('admin_a2@example.com', self.empresa_a, self.password)
        asignar_rol(self.admin_a, self.rol_admin_a)

    def test_superadmin_empresa_puede_consultar_su_empresa(self):
        self.client.login(username='admin_a2@example.com', password=self.password)
        response = self.client.get(reverse('empresa:ver'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Empresa A')

    def test_superadmin_empresa_no_puede_consultar_otra_empresa_via_url(self):
        self.client.login(username='admin_a2@example.com', password=self.password)
        response = self.client.get(reverse('empresa:detalle', args=[self.empresa_b.pk]))
        self.assertEqual(response.status_code, 403)

    def test_usuario_empresa_a_no_obtiene_info_de_empresa_b(self):
        self.client.login(username='admin_a2@example.com', password=self.password)
        response = self.client.get(reverse('empresa:ver'))
        self.assertNotContains(response, 'Empresa B')

    def test_acceso_sin_permiso_empresa_ver_recibe_403(self):
        crear_usuario('sinrol@example.com', self.empresa_a, self.password)
        self.client.login(username='sinrol@example.com', password=self.password)
        response = self.client.get(reverse('empresa:ver'))
        self.assertEqual(response.status_code, 403)


class ActualizarEmpresaViewTests(TestCase):
    """HU-003: actualizar la empresa actual."""

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900222101')
        self.empresa_b = crear_empresa('Empresa B', '900222102')
        self.rol_admin_a = Rol.objects.create(
            empresa=self.empresa_a, nombre='Administrador', es_administrador_principal=True,
        )
        self.password = 'clave-segura-123'
        self.admin_a = crear_usuario('admin_a3@example.com', self.empresa_a, self.password)
        asignar_rol(self.admin_a, self.rol_admin_a)

    def _datos_validos(self, **overrides):
        datos = {
            'razon_social': 'Empresa A', 'direccion': 'Calle 1', 'municipio': 'Bogotá',
            'telefono': '3000000000', 'email': 'contacto@a.com',
        }
        datos.update(overrides)
        return datos

    def test_superadmin_empresa_puede_actualizar_su_empresa(self):
        self.client.login(username='admin_a3@example.com', password=self.password)
        response = self.client.post(reverse('empresa:editar'), self._datos_validos(razon_social='Empresa A Nueva'))
        self.assertRedirects(response, reverse('empresa:ver'))
        self.empresa_a.refresh_from_db()
        self.assertEqual(self.empresa_a.razon_social, 'Empresa A Nueva')

    def test_datos_modificados_quedan_persistidos(self):
        self.client.login(username='admin_a3@example.com', password=self.password)
        self.client.post(reverse('empresa:editar'), self._datos_validos(direccion='Nueva Dirección', municipio='Medellín'))
        self.empresa_a.refresh_from_db()
        self.assertEqual(self.empresa_a.direccion, 'Nueva Dirección')
        self.assertEqual(self.empresa_a.municipio, 'Medellín')

    def test_validaciones_funcionan_email_invalido(self):
        self.client.login(username='admin_a3@example.com', password=self.password)
        response = self.client.post(reverse('empresa:editar'), self._datos_validos(email='no-es-email'))
        self.assertEqual(response.status_code, 200)
        self.empresa_a.refresh_from_db()
        self.assertNotEqual(self.empresa_a.email, 'no-es-email')

    def test_superadmin_empresa_no_puede_actualizar_otra_empresa(self):
        self.client.login(username='admin_a3@example.com', password=self.password)
        self.client.post(reverse('empresa:editar'), self._datos_validos(razon_social='Hackeada'))
        self.empresa_b.refresh_from_db()
        self.assertNotEqual(self.empresa_b.razon_social, 'Hackeada')

    def test_identificacion_no_se_puede_modificar_desde_formulario(self):
        self.client.login(username='admin_a3@example.com', password=self.password)
        self.client.post(reverse('empresa:editar'), self._datos_validos(numero_identificacion='999999999'))
        self.empresa_a.refresh_from_db()
        self.assertEqual(self.empresa_a.numero_identificacion, '900222101')


class RBACEmpresaTests(TestCase):
    """RBAC aplicado a los casos de uso de empresa."""

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900222201')
        self.password = 'clave-segura-123'

    def test_usuario_sin_empresa_editar_no_puede_modificar(self):
        rol_solo_lectura = Rol.objects.create(empresa=self.empresa_a, nombre='Solo lectura')
        RolPermiso.objects.create(rol=rol_solo_lectura, permiso=Permiso.objects.get(codigo='empresa.ver'))
        usuario = crear_usuario('lector@example.com', self.empresa_a, self.password)
        asignar_rol(usuario, rol_solo_lectura)
        self.client.login(username='lector@example.com', password=self.password)
        response = self.client.get(reverse('empresa:editar'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_sin_empresa_ver_no_puede_consultar(self):
        crear_usuario('nadie@example.com', self.empresa_a, self.password)
        self.client.login(username='nadie@example.com', password=self.password)
        response = self.client.get(reverse('empresa:ver'))
        self.assertEqual(response.status_code, 403)

    def test_superadmin_sistema_conserva_acceso_global(self):
        Usuario.objects.create_superuser(
            email='root2@example.com', nombre='Root', apellido='Sistema', password=self.password,
        )
        self.client.login(username='root2@example.com', password=self.password)
        response = self.client.get(reverse('empresa:admin_lista'))
        self.assertEqual(response.status_code, 200)


class EmpresaInactivaAccesoTests(TestCase):
    """Empresa INACTIVA bloquea operaciones de negocio; SUPER_ADMIN_SISTEMA conserva acceso."""

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900222301')
        self.rol_admin_a = Rol.objects.create(
            empresa=self.empresa_a, nombre='Administrador', es_administrador_principal=True,
        )
        self.password = 'clave-segura-123'
        self.admin_a = crear_usuario('admin_inactiva@example.com', self.empresa_a, self.password)
        asignar_rol(self.admin_a, self.rol_admin_a)

    def test_empresa_inactiva_bloquea_operaciones_de_usuarios_de_negocio(self):
        self.empresa_a.estado = EstadoEmpresa.INACTIVA
        self.empresa_a.save()
        self.client.login(username='admin_inactiva@example.com', password=self.password)
        response = self.client.get(reverse('empresa:ver'))
        self.assertEqual(response.status_code, 403)

    def test_superadmin_sistema_puede_seguir_administrando_empresa_inactiva(self):
        self.empresa_a.estado = EstadoEmpresa.INACTIVA
        self.empresa_a.save()
        Usuario.objects.create_superuser(
            email='root3@example.com', nombre='Root', apellido='Sistema', password=self.password,
        )
        self.client.login(username='root3@example.com', password=self.password)
        response = self.client.get(reverse('empresa:admin_detalle', args=[self.empresa_a.pk]))
        self.assertEqual(response.status_code, 200)
