from django.db import migrations

PERMISOS = [
    ('empresa', 'empresa.ver', 'Ver empresa'),
    ('empresa', 'empresa.editar', 'Editar empresa'),

    ('usuarios', 'usuarios.ver', 'Ver usuarios'),
    ('usuarios', 'usuarios.crear', 'Crear usuarios'),
    ('usuarios', 'usuarios.editar', 'Editar usuarios'),
    ('usuarios', 'usuarios.desactivar', 'Desactivar usuarios'),

    ('roles', 'roles.ver', 'Ver roles'),
    ('roles', 'roles.crear', 'Crear roles'),
    ('roles', 'roles.editar', 'Editar roles'),
    ('roles', 'roles.asignar_permisos', 'Asignar permisos a roles'),

    ('clientes', 'clientes.ver', 'Ver clientes'),
    ('clientes', 'clientes.crear', 'Crear clientes'),
    ('clientes', 'clientes.editar', 'Editar clientes'),

    ('productos', 'productos.ver', 'Ver productos'),
    ('productos', 'productos.crear', 'Crear productos'),
    ('productos', 'productos.editar', 'Editar productos'),
    ('productos', 'productos.cambiar_precio', 'Cambiar precio de productos'),
    ('productos', 'productos.activar', 'Activar productos'),
    ('productos', 'productos.desactivar', 'Desactivar productos'),

    ('inventario', 'inventario.ver', 'Ver inventario'),
    ('inventario', 'inventario.entrada', 'Registrar entrada de inventario'),
    ('inventario', 'inventario.salida', 'Registrar salida de inventario'),
    ('inventario', 'inventario.ajuste', 'Ajustar inventario'),

    ('ventas', 'ventas.ver', 'Ver ventas'),
    ('ventas', 'ventas.crear', 'Crear ventas'),
    ('ventas', 'ventas.editar', 'Editar ventas'),
    ('ventas', 'ventas.anular', 'Anular ventas'),

    ('facturacion', 'facturacion.ver', 'Ver facturación'),
    ('facturacion', 'facturacion.preparar', 'Preparar factura'),
    ('facturacion', 'facturacion.emitir', 'Emitir factura'),
    ('facturacion', 'facturacion.descargar', 'Descargar factura'),
    ('facturacion', 'facturacion.enviar_correo', 'Enviar factura por correo'),

    ('reportes', 'reportes.ver', 'Ver reportes'),
]


def crear_permisos(apps, schema_editor):
    Permiso = apps.get_model('roles', 'Permiso')
    for modulo, codigo, nombre in PERMISOS:
        Permiso.objects.get_or_create(
            codigo=codigo,
            defaults={'nombre': nombre, 'modulo': modulo, 'estado': 'ACTIVO'},
        )


def eliminar_permisos(apps, schema_editor):
    Permiso = apps.get_model('roles', 'Permiso')
    codigos = [codigo for _, codigo, _ in PERMISOS]
    Permiso.objects.filter(codigo__in=codigos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_permisos, eliminar_permisos),
    ]
