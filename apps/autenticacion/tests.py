from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()


class UsuarioManagerTests(TestCase):

    def test_crear_usuario(self):
        usuario = Usuario.objects.create_user(
            email='ana@example.com', nombre='Ana', apellido='Pérez', password='clave-segura-123',
        )
        self.assertEqual(usuario.email, 'ana@example.com')
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)

    def test_no_permite_email_duplicado(self):
        Usuario.objects.create_user(
            email='ana@example.com', nombre='Ana', apellido='Pérez', password='clave-segura-123',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Usuario.objects.create_user(
                    email='ana@example.com', nombre='Otra', apellido='Persona', password='otra-clave-123',
                )

    def test_password_queda_hasheado(self):
        usuario = Usuario.objects.create_user(
            email='ana@example.com', nombre='Ana', apellido='Pérez', password='clave-segura-123',
        )
        self.assertNotEqual(usuario.password, 'clave-segura-123')
        self.assertTrue(usuario.check_password('clave-segura-123'))


class LoginLogoutTests(TestCase):

    def setUp(self):
        self.password = 'clave-segura-123'
        self.usuario = Usuario.objects.create_user(
            email='ana@example.com', nombre='Ana', apellido='Pérez', password=self.password,
        )
        self.login_url = reverse('autenticacion:login')
        self.logout_url = reverse('autenticacion:logout')
        self.app_url = reverse('core:app_home')

    def test_login_exitoso(self):
        response = self.client.post(self.login_url, {'username': 'ana@example.com', 'password': self.password})
        self.assertRedirects(response, self.app_url)

    def test_login_password_incorrecto(self):
        response = self.client.post(self.login_url, {'username': 'ana@example.com', 'password': 'incorrecta'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_usuario_inactivo_no_puede_autenticarse(self):
        self.usuario.is_active = False
        self.usuario.save()
        response = self.client.post(self.login_url, {'username': 'ana@example.com', 'password': self.password})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_usuario_no_autenticado_no_accede_a_app(self):
        response = self.client.get(self.app_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_usuario_autenticado_accede_a_app(self):
        self.client.login(username='ana@example.com', password=self.password)
        response = self.client.get(self.app_url)
        self.assertEqual(response.status_code, 200)

    def test_logout_funciona(self):
        self.client.login(username='ana@example.com', password=self.password)
        self.client.post(self.logout_url)
        response = self.client.get(self.app_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)
