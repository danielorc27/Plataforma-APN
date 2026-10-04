from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.empresa.models import Empresa

from .models import EstadoRol, ModuloPermiso, Permiso, Rol, RolPermiso, UsuarioRol
from .services import RBACError, asignar_rol, desactivar_usuario, quitar_rol

Usuario = get_user_model()


def crear_empresa(nombre, nit):
    return Empresa.objects.create(razon_social=nombre, numero_identificacion=nit)


def crear_usuario(email, empresa, password='clave-segura-123'):
    return Usuario.objects.create_user(
        email=email, nombre='Test', apellido='User', password=password, empresa=empresa,
    )


class RolModelTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900000001')
        self.empresa_b = crear_empresa('Empresa B', '900000002')

    def test_crear_rol(self):
        rol = Rol.objects.create(empresa=self.empresa_a, nombre='Vendedor')
        self.assertEqual(rol.estado, EstadoRol.ACTIVO)

    def test_nombre_duplicado_misma_empresa_no_permitido(self):
        Rol.objects.create(empresa=self.empresa_a, nombre='Vendedor')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Rol.objects.create(empresa=self.empresa_a, nombre='Vendedor')

    def test_mismo_nombre_en_empresas_diferentes_permitido(self):
        Rol.objects.create(empresa=self.empresa_a, nombre='Vendedor')
        Rol.objects.create(empresa=self.empresa_b, nombre='Vendedor')
        self.assertEqual(Rol.objects.filter(nombre='Vendedor').count(), 2)

    def test_activar_inactivar_rol(self):
        rol = Rol.objects.create(empresa=self.empresa_a, nombre='Auditor')
        rol.estado = EstadoRol.INACTIVO
        rol.save()
        rol.refresh_from_db()
        self.assertFalse(rol.esta_activo)

    def test_unico_administrador_principal_por_empresa(self):
        Rol.objects.create(empresa=self.empresa_a, nombre='Admin1', es_administrador_principal=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Rol.objects.create(empresa=self.empresa_a, nombre='Admin2', es_administrador_principal=True)


class PermisoModelTests(TestCase):

    def test_crear_y_consultar_permiso(self):
        permiso = Permiso.objects.create(
            codigo='clientes.exportar', nombre='Exportar clientes', modulo=ModuloPermiso.CLIENTES,
        )
        self.assertEqual(Permiso.objects.get(codigo='clientes.exportar'), permiso)

    def test_codigo_unico(self):
        Permiso.objects.create(
            codigo='clientes.exportar', nombre='Exportar clientes', modulo=ModuloPermiso.CLIENTES,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Permiso.objects.create(
                    codigo='clientes.exportar', nombre='Duplicado', modulo=ModuloPermiso.CLIENTES,
                )

    def test_catalogo_sembrado_por_migracion(self):
        self.assertTrue(Permiso.objects.filter(codigo='usuarios.crear').exists())
        self.assertTrue(Permiso.objects.filter(codigo='usuarios.ver').exists())

    def test_asociar_permiso_a_rol(self):
        empresa = crear_empresa('Empresa A', '900000001')
        rol = Rol.objects.create(empresa=empresa, nombre='Vendedor')
        permiso = Permiso.objects.get(codigo='ventas.crear')
        RolPermiso.objects.create(rol=rol, permiso=permiso)
        self.assertIn(permiso, rol.permisos.all())


class UsuarioRolTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900000001')
        self.empresa_b = crear_empresa('Empresa B', '900000002')
        self.rol_vendedor_a = Rol.objects.create(empresa=self.empresa_a, nombre='Vendedor')
        self.rol_inventario_a = Rol.objects.create(empresa=self.empresa_a, nombre='Inventario')
        self.rol_b = Rol.objects.create(empresa=self.empresa_b, nombre='Administrador', es_administrador_principal=True)
        self.usuario_a = crear_usuario('a@example.com', self.empresa_a)

    def test_usuario_puede_tener_multiples_roles(self):
        asignar_rol(self.usuario_a, self.rol_vendedor_a)
        asignar_rol(self.usuario_a, self.rol_inventario_a)
        self.assertEqual(self.usuario_a.roles.count(), 2)

    def test_usuario_puede_consultar_sus_roles(self):
        asignar_rol(self.usuario_a, self.rol_vendedor_a)
        nombres = list(self.usuario_a.roles.values_list('nombre', flat=True))
        self.assertEqual(nombres, ['Vendedor'])

    def test_usuario_no_puede_obtener_rol_de_otra_empresa(self):
        with self.assertRaises(RBACError):
            asignar_rol(self.usuario_a, self.rol_b)

    def test_validacion_de_modelo_tambien_rechaza_rol_cruzado(self):
        usuario_rol = UsuarioRol(usuario=self.usuario_a, rol=self.rol_b)
        with self.assertRaises(ValidationError):
            usuario_rol.save()


class AutorizacionTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900000001')
        self.empresa_b = crear_empresa('Empresa B', '900000002')
        self.rol_vendedor = Rol.objects.create(empresa=self.empresa_a, nombre='Vendedor')
        RolPermiso.objects.create(rol=self.rol_vendedor, permiso=Permiso.objects.get(codigo='ventas.crear'))
        self.password = 'clave-segura-123'
        self.usuario = crear_usuario('vendedor@example.com', self.empresa_a, self.password)
        asignar_rol(self.usuario, self.rol_vendedor)

    def test_usuario_con_permiso_puede_ejecutar_accion(self):
        self.assertTrue(self.usuario.has_permission('ventas.crear'))

    def test_usuario_sin_permiso_recibe_403_en_vista(self):
        self.client.login(username='vendedor@example.com', password=self.password)
        response = self.client.get(reverse('autenticacion:usuarios_crear'))
        self.assertEqual(response.status_code, 403)

    def test_usuario_con_permiso_accede_a_vista_protegida(self):
        RolPermiso.objects.create(rol=self.rol_vendedor, permiso=Permiso.objects.get(codigo='usuarios.ver'))
        self.client.login(username='vendedor@example.com', password=self.password)
        response = self.client.get(reverse('autenticacion:usuarios_lista'))
        self.assertEqual(response.status_code, 200)

    def test_usuario_no_autenticado_recibe_redirect_a_login(self):
        response = self.client.get(reverse('autenticacion:usuarios_lista'))
        self.assertEqual(response.status_code, 302)

    def test_usuario_inactivo_no_tiene_permisos(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.assertFalse(self.usuario.has_permission('ventas.crear'))

    def test_rol_inactivo_no_otorga_permisos(self):
        self.rol_vendedor.estado = EstadoRol.INACTIVO
        self.rol_vendedor.save()
        self.assertFalse(self.usuario.has_permission('ventas.crear'))

    def test_usuario_empresa_a_no_hereda_roles_de_empresa_b(self):
        usuario_b = crear_usuario('otro@example.com', self.empresa_b)
        rol_b = Rol.objects.create(empresa=self.empresa_b, nombre='Vendedor')
        RolPermiso.objects.create(rol=rol_b, permiso=Permiso.objects.get(codigo='ventas.crear'))
        asignar_rol(usuario_b, rol_b)
        self.assertFalse(self.usuario.roles.filter(empresa=self.empresa_b).exists())


class SuperAdminTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900000001')
        self.empresa_b = crear_empresa('Empresa B', '900000002')
        self.rol_admin_a = Rol.objects.create(
            empresa=self.empresa_a, nombre='Administrador', es_administrador_principal=True,
        )
        self.admin_empresa_a = crear_usuario('admin_a@example.com', self.empresa_a)
        asignar_rol(self.admin_empresa_a, self.rol_admin_a)
        self.superadmin = Usuario.objects.create_superuser(
            email='root@example.com', nombre='Root', apellido='Sistema', password='clave-segura-123',
        )

    def test_superadmin_sistema_puede_administrar_empresas_globalmente(self):
        self.assertTrue(self.superadmin.has_permission('empresa.editar'))

    def test_superadmin_sistema_no_necesita_empresa(self):
        self.assertIsNone(self.superadmin.empresa)
        self.superadmin.full_clean()

    def test_admin_empresa_pertenece_a_una_empresa(self):
        self.assertEqual(self.admin_empresa_a.empresa, self.empresa_a)
        self.assertTrue(self.admin_empresa_a.es_administrador_empresa)

    def test_admin_empresa_no_puede_administrar_otra_empresa(self):
        rol_b = Rol.objects.create(empresa=self.empresa_b, nombre='Otro')
        with self.assertRaises(RBACError):
            asignar_rol(self.admin_empresa_a, rol_b)

    def test_admin_empresa_no_puede_eliminarse_a_si_mismo(self):
        with self.assertRaises(RBACError):
            desactivar_usuario(self.admin_empresa_a, ejecutor=self.admin_empresa_a)

    def test_no_se_puede_dejar_empresa_sin_administrador_principal_al_quitar_rol(self):
        with self.assertRaises(RBACError):
            quitar_rol(self.admin_empresa_a, self.rol_admin_a)

    def test_no_se_puede_desactivar_al_ultimo_administrador(self):
        otro_usuario = crear_usuario('empleado_a@example.com', self.empresa_a)
        with self.assertRaises(RBACError):
            desactivar_usuario(self.admin_empresa_a, ejecutor=otro_usuario)


class HerenciaPermisosTests(TestCase):

    def setUp(self):
        self.empresa_a = crear_empresa('Empresa A', '900000001')
        self.empresa_b = crear_empresa('Empresa B', '900000002')
        self.usuario = crear_usuario('multi@example.com', self.empresa_a)

        self.rol_ventas = Rol.objects.create(empresa=self.empresa_a, nombre='Ventas')
        self.rol_inventario = Rol.objects.create(empresa=self.empresa_a, nombre='Inventario')
        RolPermiso.objects.create(rol=self.rol_ventas, permiso=Permiso.objects.get(codigo='ventas.crear'))
        RolPermiso.objects.create(rol=self.rol_inventario, permiso=Permiso.objects.get(codigo='inventario.ajuste'))
        asignar_rol(self.usuario, self.rol_ventas)
        asignar_rol(self.usuario, self.rol_inventario)

    def test_permisos_de_todos_los_roles_activos_se_consideran(self):
        self.assertTrue(self.usuario.has_permission('ventas.crear'))
        self.assertTrue(self.usuario.has_permission('inventario.ajuste'))

    def test_permisos_de_otra_empresa_nunca_cuentan(self):
        rol_b = Rol.objects.create(empresa=self.empresa_b, nombre='Ventas')
        RolPermiso.objects.create(rol=rol_b, permiso=Permiso.objects.get(codigo='facturacion.emitir'))
        self.assertFalse(self.usuario.has_permission('facturacion.emitir'))
