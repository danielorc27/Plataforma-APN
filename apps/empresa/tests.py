from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Empresa, EstadoEmpresa, TipoIdentificacion

Usuario = get_user_model()


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
