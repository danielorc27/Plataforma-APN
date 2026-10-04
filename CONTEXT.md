# CONTEXTO MAESTRO DEL PROYECTO
# Plataforma de Administración para Pequeños Negocios

## 1. PROPÓSITO DEL DOCUMENTO

Este documento contiene el contexto técnico, funcional y arquitectónico oficial del proyecto.

Debe ser leído antes de realizar cualquier tarea de desarrollo, modificación de arquitectura, creación de modelos, implementación de funcionalidades o integración externa.

Las decisiones definidas aquí deben considerarse la fuente principal de verdad del proyecto.

No modificar decisiones arquitectónicas o funcionales importantes sin solicitar confirmación explícita.

---

# 2. DESCRIPCIÓN DEL PROYECTO

El proyecto consiste en desarrollar una plataforma web de administración para pequeños negocios.

El objetivo es permitir que una empresa gestione desde una única plataforma:

- Información de la empresa.
- Usuarios.
- Roles y permisos.
- Clientes.
- Productos.
- Inventario.
- Ventas.
- Medios de pago.
- Facturación electrónica.
- Notas crédito.
- Dashboard y reportes.

La plataforma está orientada inicialmente a pequeños negocios que necesitan organizar su operación comercial y posteriormente integrarse con un proveedor de facturación electrónica.

El proyecto se desarrolla inicialmente sin consumir la API externa de facturación.

Primero debe construirse y validarse toda la lógica interna del negocio.

Posteriormente se implementará la integración real con Factus.

---

# 3. PRINCIPIO ARQUITECTÓNICO FUNDAMENTAL

La plataforma es responsable de la lógica del negocio.

Factus NO es el núcleo de la aplicación.

Factus será tratado como un proveedor externo de servicios de facturación electrónica.

La aplicación debe funcionar conceptualmente así:

    Usuario
       ↓
    Plataforma
       ↓
    Lógica de negocio
       ↓
    Base de datos

La integración externa aparecerá únicamente cuando una operación requiera comunicación con el proveedor de facturación.

    Plataforma
       ↓
    FacturacionService
       ↓
    FactusService
       ↓
    Factus API

La lógica de ventas, clientes, productos, inventario y demás módulos NO debe depender directamente de Factus.

---

# 4. STACK TECNOLÓGICO

## Backend

- Python
- Django
- Django ORM
- Django Authentication
- Django Forms

## Base de datos

- PostgreSQL

## Frontend

- Django Templates
- HTML
- CSS
- JavaScript

No se utilizará Flutter para este proyecto.

No se utilizará React inicialmente.

No es obligatorio utilizar Django REST Framework para el MVP.

La aplicación será inicialmente una aplicación web monolítica.

---

# 5. ARQUITECTURA GENERAL

Se utilizará una arquitectura:

> Monolítica modular con separación por capas.

No se utilizarán microservicios.

La estructura conceptual es:

    ┌──────────────────────────────┐
    │ PRESENTACIÓN                 │
    │ Django Templates             │
    │ HTML / CSS / JavaScript      │
    └──────────────┬───────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ VIEWS                        │
    │ HTTP / navegación / Forms    │
    └──────────────┬───────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ SERVICES                     │
    │ Casos de uso / negocio       │
    └──────────────┬───────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ DJANGO ORM / MODELS          │
    └──────────────┬───────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ POSTGRESQL                   │
    └──────────────────────────────┘

Para integraciones externas:

    Service
       ↓
    Provider / Adapter
       ↓
    External API

---

# 6. ESTRUCTURA MODULAR

La aplicación debe organizarse por dominios funcionales.

Estructura inicial propuesta:

    project/
    │
    ├── config/
    │   ├── settings.py
    │   ├── urls.py
    │   ├── asgi.py
    │   └── wsgi.py
    │
    ├── apps/
    │   ├── core/
    │   ├── autenticacion/
    │   ├── plataforma/
    │   ├── empresa/
    │   ├── usuarios/
    │   ├── clientes/
    │   ├── productos/
    │   ├── inventario/
    │   ├── ventas/
    │   ├── facturacion/
    │   └── dashboard/
    │
    ├── templates/
    ├── static/
    ├── manage.py
    └── requirements.txt

Cada módulo debe mantener una responsabilidad clara.

No crear una aplicación Django genérica que concentre toda la lógica.

No colocar toda la lógica de negocio directamente en views.py.

---

# 7. MULTIEMPRESA / TENANCY

La plataforma debe diseñarse desde el inicio como un sistema multiempresa.

Una empresa representa un tenant lógico.

Ejemplo:

    Empresa A
       ├── Usuarios
       ├── Clientes
       ├── Productos
       ├── Inventario
       └── Ventas

    Empresa B
       ├── Usuarios
       ├── Clientes
       ├── Productos
       ├── Inventario
       └── Ventas

Los datos de una empresa nunca deben quedar disponibles para otra empresa.

La mayoría de las entidades de negocio deben estar relacionadas directa o indirectamente con Empresa.

Ejemplo:

    Cliente
    ├── empresa
    └── ...

    Producto
    ├── empresa
    └── ...

    Venta
    ├── empresa
    └── ...

Las consultas deben respetar siempre el contexto de empresa.

No utilizar consultas globales como:

    Cliente.objects.all()

cuando exista riesgo de exponer información de otros tenants.

Preferir:

    Cliente.objects.filter(
        empresa=request.user.empresa
    )

La empresa debe ser considerada parte fundamental del contexto de seguridad.

---

# 8. NIVELES DE ADMINISTRACIÓN

Existen dos niveles principales de administración.

## 8.1 Administrador del sistema

Administra la plataforma completa.

Responsabilidades:

- Crear empresas.
- Consultar empresas.
- Editar empresas.
- Activar empresas.
- Desactivar empresas.
- Asignar administrador inicial de empresa.
- Consultar información general.
- Consultar métricas globales.
- Administrar aspectos globales de la plataforma.

Este usuario pertenece al nivel global del sistema.

No debe confundirse con el administrador de una empresa.

---

# 9. ADMINISTRACIÓN DE EMPRESA

Cada empresa debe tener uno o más usuarios con capacidad administrativa.

El rol principal será:

> SUPER_ADMIN_EMPRESA

Este usuario administra la configuración y operación interna de su empresa.

Puede:

- Gestionar usuarios.
- Crear roles.
- Editar roles.
- Asignar permisos.
- Asignar roles a usuarios.
- Gestionar empresa.
- Gestionar productos.
- Cambiar precios.
- Gestionar clientes.
- Gestionar inventario.
- Gestionar ventas.
- Configurar facturación.
- Consultar reportes.

El SUPER_ADMIN_EMPRESA no puede administrar otra empresa.

---

# 10. ROLES Y PERMISOS

El sistema NO debe depender exclusivamente de roles rígidos.

Se utilizará:

> RBAC (Role-Based Access Control)

con roles y permisos granulares.

Modelo conceptual:

    Usuario
       ↓
    UsuarioRol
       ↓
    Rol
       ↓
    RolPermiso
       ↓
    Permiso

Un usuario puede tener uno o varios roles.

Los permisos deben representar acciones específicas.

Ejemplos:

    empresa.ver
    empresa.editar

    usuarios.ver
    usuarios.crear
    usuarios.editar
    usuarios.desactivar

    roles.ver
    roles.crear
    roles.editar
    roles.asignar_permisos

    clientes.ver
    clientes.crear
    clientes.editar

    productos.ver
    productos.crear
    productos.editar
    productos.cambiar_precio
    productos.activar
    productos.desactivar

    inventario.ver
    inventario.entrada
    inventario.salida
    inventario.ajuste

    ventas.ver
    ventas.crear
    ventas.editar
    ventas.anular

    facturacion.ver
    facturacion.preparar
    facturacion.emitir
    facturacion.descargar
    facturacion.enviar_correo

    reportes.ver

Los permisos son acciones.

Los roles agrupan permisos.

---

# 11. ROLES BASE

El sistema tendrá inicialmente dos roles globales conceptuales:

    SUPER_ADMIN_SISTEMA
    SUPER_ADMIN_EMPRESA

Además, cada empresa podrá utilizar roles operativos.

Ejemplos:

    Administrador
    Operador
    Vendedor
    Auditor
    Inventario

Los roles operativos deben poder configurarse según los permisos permitidos.

---

# 12. EJEMPLO DE PERMISOS

## SUPER_ADMIN_EMPRESA

Puede tener:

    usuarios.*
    roles.*
    empresa.*
    clientes.*
    productos.*
    inventario.*
    ventas.*
    facturacion.*
    reportes.*

## VENDEDOR

Puede tener:

    clientes.ver
    clientes.crear

    productos.ver

    ventas.ver
    ventas.crear

    facturacion.ver
    facturacion.preparar

No puede:

    productos.cambiar_precio
    productos.editar
    inventario.ajuste
    usuarios.crear
    roles.editar

## AUDITOR

Principalmente permisos de consulta:

    empresa.ver
    clientes.ver
    productos.ver
    inventario.ver
    ventas.ver
    facturacion.ver
    reportes.ver

---

# 13. REGLAS DE SEGURIDAD DE ROLES

El SUPER_ADMIN_EMPRESA debe estar protegido.

El sistema debe evitar:

- Que el último administrador de una empresa sea eliminado.
- Que el último administrador pierda todos sus permisos críticos.
- Que un usuario sin autorización cree un rol superior al suyo.
- Que un administrador de Empresa A modifique roles de Empresa B.
- Que un usuario modifique permisos fuera de su empresa.

Ocultar un botón en la interfaz NO es suficiente.

Los permisos deben validarse en el backend.

---

# 14. PATRÓN SERVICE LAYER

La lógica de negocio debe estar principalmente en servicios.

Evitar views con grandes cantidades de lógica.

Incorrecto:

    View
      ├── validar cliente
      ├── calcular inventario
      ├── crear venta
      ├── actualizar stock
      └── enviar factura

Preferido:

    View
      ↓
    Service
      ↓
    Models / ORM

Ejemplo conceptual:

    VentaView
       ↓
    VentaService.crear_venta()
       ↓
    Cliente
    Producto
    Inventario
    Venta
    DetalleVenta

Los Services representan casos de uso.

---

# 15. REPOSITORY PATTERN

No implementar Repository Pattern indiscriminadamente.

Django ORM ya proporciona una capa de acceso a datos suficientemente robusta para este proyecto.

Preferir:

    Service
       ↓
    Django ORM
       ↓
    PostgreSQL

Crear repositorios únicamente si aparece una necesidad real.

No crear clases Repository únicamente por seguir un patrón.

---

# 16. STRATEGY PATTERN

Se utilizará para proveedores de facturación.

Conceptualmente:

    FacturacionService
          ↓
    FacturacionProvider
          │
          ├── MockFacturacionProvider
          │
          └── FactusFacturacionProvider

Esto permitirá cambiar el proveedor sin modificar la lógica principal.

---

# 17. ADAPTER PATTERN

Factus tendrá un Adapter/Provider que traduzca las estructuras externas a modelos internos.

La aplicación NO debe propagar objetos o estructuras específicas de Factus por todo el sistema.

Ejemplo conceptual:

    FactusResponse
          ↓
    FactusAdapter
          ↓
    InvoiceResponse interno

El dominio interno debe utilizar sus propios modelos y estados.

---

# 18. DEPENDENCY INVERSION

La lógica de facturación debe depender de una abstracción:

    FacturacionProvider

y no directamente de:

    Factus API

La implementación concreta puede ser:

    MockFacturacionProvider

o:

    FactusFacturacionProvider

Esto permite desarrollar y probar la plataforma sin depender de la API externa.

---

# 19. FACTURACIÓN: FASE MOCK

Durante la primera etapa NO consumir Factus.

El flujo será:

    Venta
       ↓
    Preparar factura
       ↓
    FacturacionService
       ↓
    MockFacturacionProvider
       ↓
    Respuesta simulada
       ↓
    Actualizar factura

El Mock debe permitir probar al menos:

- Factura aceptada.
- Factura rechazada.
- Error de comunicación.
- Reintento.

La lógica de la aplicación debe comportarse como si existiera un proveedor real.

---

# 20. FACTURACIÓN: FASE REAL

Posteriormente:

    Venta
       ↓
    Factura
       ↓
    FacturacionService
       ↓
    FactusFacturacionProvider
       ↓
    Factus API
       ↓
    Respuesta
       ↓
    Adapter
       ↓
    Modelo interno
       ↓
    PostgreSQL

La integración real debe estar completamente aislada.

---

# 21. SEPARACIÓN ENTRE VENTA Y FACTURA

Una venta NO es una factura.

Venta:

> Representa una operación comercial.

Factura:

> Representa el documento de facturación asociado a una venta.

Relación conceptual:

    Venta
    ├── Cliente
    ├── Detalles
    ├── MedioPago
    ├── Subtotal
    ├── Impuestos
    └── Total
          │
          ↓
       Factura
       ├── Número
       ├── Estado
       ├── Referencia externa
       ├── PDF
       └── XML

Esta separación es obligatoria para mantener un dominio limpio.

---

# 22. MODELOS PRINCIPALES

## Empresa

Debe almacenar información básica y de configuración del negocio.

Ejemplos:

- razón social
- tipo de documento
- número de documento
- dirección
- municipio
- teléfono
- email
- estado
- configuración de facturación

## Usuario

- empresa
- nombre
- email
- estado
- roles

## Rol

- empresa
- nombre
- descripción
- estado

## Permiso

Catálogo de permisos disponibles.

Ejemplo:

    productos.cambiar_precio

## Cliente

- empresa
- identificación
- nombre
- email
- teléfono
- dirección

## Producto

- empresa
- código
- nombre
- descripción
- precio
- unidad
- impuestos
- estado

## Inventario

Representa existencia actual.

## MovimientoInventario

Debe mantener trazabilidad.

Campos conceptuales:

- producto
- tipo
- cantidad
- cantidad anterior
- cantidad nueva
- usuario
- fecha
- motivo

Tipos:

    INICIAL
    ENTRADA
    SALIDA
    AJUSTE

## Venta

- empresa
- cliente
- usuario
- estado
- subtotal
- impuestos
- descuento
- total
- fecha

## DetalleVenta

- venta
- producto
- cantidad
- precio
- impuesto
- subtotal

## MedioPago

Representa el medio utilizado en la venta.

## Factura

- empresa
- venta
- número
- estado
- referencia externa
- fecha
- información del proveedor
- documentos asociados

## NotaCredito

Debe relacionarse con la factura original.

---

# 23. ESTADOS

No utilizar strings arbitrarios para estados.

Utilizar Choices/Enums.

Ejemplo:

## Venta

    BORRADOR
    CONFIRMADA
    FACTURADA
    ANULADA

## Factura

    PENDIENTE
    ENVIADA
    VALIDADA
    RECHAZADA

## Usuario

    ACTIVO
    INACTIVO

## Empresa

    ACTIVA
    INACTIVA

Los estados deben tener transiciones controladas.

---

# 24. INVENTARIO

No modificar únicamente el stock sin trazabilidad.

Evitar:

    producto.stock -= cantidad

como única operación.

Debe existir un registro de movimiento.

Ejemplo:

    Stock anterior: 20
    Movimiento: SALIDA
    Cantidad: 3
    Stock nuevo: 17
    Usuario: operador
    Fecha: fecha/hora
    Motivo: venta

Las operaciones de inventario deben ser transaccionales.

---

# 25. TRANSACCIONES

Utilizar:

    transaction.atomic()

en operaciones que modifiquen múltiples entidades y deban mantenerse consistentes.

Ejemplo:

Crear venta:

    Crear venta
    +
    Crear detalles
    +
    Actualizar inventario

Si alguna operación falla:

    ROLLBACK

No permitir estados parciales.

---

# 26. VALIDACIONES

Existirán múltiples niveles de validación.

## Frontend

Validaciones de experiencia de usuario.

## Django Forms

Validación de entrada.

## Modelos / Base de datos

Restricciones:

- unique
- foreign keys
- null
- constraints

## Services

Reglas de negocio.

Ejemplos:

- No vender producto inactivo.
- No vender más stock disponible.
- No crear cliente duplicado.
- No crear producto con código duplicado.
- No emitir factura de una venta inválida.
- No permitir operaciones fuera de la empresa.

La validación importante SIEMPRE debe existir en backend.

---

# 27. MULTI-TENANT Y SEGURIDAD

Toda operación debe considerar:

    Usuario autenticado
        ↓
    Empresa
        ↓
    Permisos
        ↓
    Operación

El sistema debe validar:

1. El usuario está autenticado.
2. El usuario pertenece a la empresa.
3. El recurso pertenece a la empresa.
4. El usuario tiene el permiso necesario.
5. La operación es válida según las reglas de negocio.

Nunca confiar únicamente en IDs proporcionados por el navegador.

---

# 28. AUTENTICACIÓN

Utilizar inicialmente el sistema de autenticación de Django.

Debe existir:

- Login.
- Logout.
- Sesiones.
- Recuperación de acceso cuando sea necesario.
- Control de usuario activo/inactivo.

La autorización se manejará mediante el sistema propio de roles y permisos del proyecto.

No depender únicamente del Django Admin para la autorización de la aplicación.

---

# 29. INTERFAZ

La aplicación utilizará Django Templates.

Debe existir un layout común:

    base.html

Con:

- navegación
- menú lateral
- usuario actual
- empresa actual
- mensajes
- contenido

Los módulos deben reutilizar componentes visuales.

Los permisos también deben controlar la visualización de opciones.

Ejemplo:

Si el usuario no tiene:

    productos.cambiar_precio

no debe aparecer la opción de cambiar precio.

Pero además el backend debe bloquear la operación.

---

# 30. DASHBOARDS

Existirán dos niveles.

## Dashboard global

Para SUPER_ADMIN_SISTEMA.

Puede mostrar:

- cantidad de empresas
- empresas activas
- empresas inactivas
- cantidad de usuarios
- ventas globales
- facturas
- otros indicadores globales

## Dashboard de empresa

Para usuarios autorizados.

Puede mostrar:

- ventas del período
- cantidad de ventas
- productos
- clientes
- inventario
- facturas
- notas crédito
- alertas

Los indicadores deben respetar el tenant.

---

# 31. SEGURIDAD DE INFORMACIÓN

Nunca almacenar:

- contraseñas en texto plano.
- tokens de API sin protección.
- secretos en Git.
- credenciales en código fuente.

Utilizar variables de entorno.

Ejemplo:

    SECRET_KEY
    DATABASE_URL
    DB_PASSWORD

Posteriormente:

    FACTUS_CLIENT_ID
    FACTUS_CLIENT_SECRET
    FACTUS_TOKEN

Los logs nunca deben contener credenciales, contraseñas o tokens.

---

# 32. CONFIGURACIÓN

Utilizar `.env` para configuración sensible o dependiente del entorno.

El archivo `.env` NO debe ser versionado.

Debe existir:

    .env.example

con nombres de variables sin valores sensibles.

---

# 33. GIT

Utilizar control de versiones desde el inicio.

Ramas principales:

    main
    develop

Features:

    feature/hu-001-registrar-empresa
    feature/hu-008-registrar-cliente
    feature/hu-011-registrar-producto

Los cambios deben ser pequeños y trazables.

---

# 34. TESTING

El proyecto debe incluir pruebas progresivamente.

Prioridad:

1. Reglas críticas de negocio.
2. Services.
3. Permisos.
4. Aislamiento multiempresa.
5. Inventario.
6. Ventas.
7. Facturación.
8. Integración externa.

Especialmente probar:

- Usuario de Empresa A no puede acceder a Empresa B.
- Usuario sin permiso no puede ejecutar una operación.
- No se puede vender más stock del disponible.
- No se puede modificar precio sin permiso.
- No se puede eliminar el último administrador.
- Facturación rechazada actualiza correctamente el estado.
- Facturación simulada funciona sin API externa.

---

# 35. OBSERVABILIDAD Y LOGGING

Registrar eventos importantes:

- login
- creación de empresa
- creación de usuario
- cambio de permisos
- creación de producto
- cambio de precio
- movimientos de inventario
- creación de venta
- generación de factura
- respuesta del proveedor
- errores relevantes

No registrar información sensible.

---

# 36. ORDEN DE IMPLEMENTACIÓN

El desarrollo debe seguir este orden general.

## FASE 1 — Arquitectura base

- Crear proyecto Django.
- Configurar PostgreSQL.
- Configurar variables de entorno.
- Configurar estructura modular.
- Configurar autenticación.
- Configurar usuario.
- Configurar empresa.
- Configurar multiempresa.

## FASE 2 — Autorización

- Roles.
- Permisos.
- Usuario-Rol.
- Rol-Permiso.
- SUPER_ADMIN_SISTEMA.
- SUPER_ADMIN_EMPRESA.
- Aislamiento de permisos por empresa.

Esta fase es prioritaria antes de desarrollar módulos comerciales.

## FASE 3 — Empresa

- Registrar empresa.
- Consultar empresa.
- Actualizar empresa.
- Activar/desactivar empresa.
- Administración global de empresas.

## FASE 4 — Clientes

- Registrar.
- Consultar.
- Actualizar.

## FASE 5 — Productos

- Registrar.
- Consultar.
- Actualizar.
- Activar/desactivar.
- Controlar permisos de modificación de precio.

## FASE 6 — Inventario

- Inventario inicial.
- Consulta.
- Entradas.
- Salidas.
- Ajustes.
- Trazabilidad.

## FASE 7 — Ventas

- Crear venta.
- Detalles.
- Medio de pago.
- Descuentos.
- Estados.
- Actualización de inventario.

## FASE 8 — Facturación simulada

- Modelo de factura.
- FacturacionService.
- MockFacturacionProvider.
- Estados.
- Respuestas simuladas.
- PDF/XML simulados.
- Errores y reintentos.

## FASE 9 — Integración Factus

Solo después de estabilizar el flujo interno:

- Autenticación.
- Configuración.
- Cliente Factus.
- Adapter.
- Envío.
- Respuesta.
- Estados.
- PDF.
- XML.
- Correo.
- Notas crédito.

## FASE 10 — Dashboard y mejoras

- Indicadores.
- Reportes.
- Alertas.
- Mejoras de UX.
- Auditoría.

---

# 37. REGLA DE DESARROLLO PRINCIPAL

Cada funcionalidad debe corresponder a una User Story del Product Backlog.

Antes de implementar una funcionalidad:

1. Identificar la User Story.
2. Revisar criterios de aceptación.
3. Revisar dependencias.
4. Revisar permisos necesarios.
5. Revisar impacto multiempresa.
6. Diseñar modelo si es necesario.
7. Implementar Service.
8. Implementar View/Form.
9. Implementar interfaz.
10. Crear pruebas.
11. Validar Definition of Done.

No desarrollar funcionalidades que no estén justificadas por el alcance del proyecto sin solicitar confirmación.

---

# 38. PRINCIPIOS DE DISEÑO

Priorizar:

- Simplicidad.
- Separación de responsabilidades.
- Bajo acoplamiento.
- Alta cohesión.
- Seguridad.
- Trazabilidad.
- Testabilidad.
- Reutilización razonable.
- Código mantenible.

Evitar:

- Sobreingeniería.
- Microservicios innecesarios.
- Patrones implementados solo por cumplir una lista.
- Lógica de negocio en templates.
- Lógica de negocio excesiva en views.
- Dependencia directa de Factus desde módulos internos.
- Consultas sin aislamiento por empresa.
- Permisos únicamente en frontend.
- Datos sensibles en Git.

---

# 39. FLUJO GLOBAL DEL SISTEMA

El flujo principal esperado es:

    ADMINISTRADOR DEL SISTEMA
             ↓
       Crear empresa
             ↓
    Asignar administrador
             ↓
    SUPER_ADMIN_EMPRESA
             ↓
       Configurar empresa
             ↓
       Crear usuarios
             ↓
       Crear roles/permisos
             ↓
    ┌────────┴──────────┐
    ↓                   ↓
 Clientes            Productos
    │                   │
    └────────┬──────────┘
             ↓
         Inventario
             ↓
           Venta
             ↓
       Medio de pago
             ↓
     Preparar factura
             ↓
     FacturacionService
             ↓
    ┌────────┴──────────┐
    ↓                   ↓
   MOCK              FACTUS
    │                   │
    └────────┬──────────┘
             ↓
        Respuesta
             ↓
      Estado de factura
             ↓
       PDF / XML / correo
             ↓
         Dashboard

---

# 40. ESTADO ACTUAL DEL PROYECTO

Actualmente el proyecto se encuentra en fase de planificación y diseño.

Todavía NO se debe implementar la integración real con Factus.

La prioridad inmediata es construir correctamente:

1. Arquitectura base.
2. Multiempresa.
3. Autenticación.
4. Roles.
5. Permisos.
6. Administración global.
7. Administración de empresa.
8. Clientes.
9. Productos.
10. Inventario.
11. Ventas.
12. Facturación simulada.

La integración real con Factus será una etapa posterior.

---

# 41. REGLA PARA CLAUDE

Antes de realizar cualquier modificación importante:

- Revisar este documento.
- Revisar el Product Backlog.
- Revisar las User Stories.
- Revisar las dependencias.
- Mantener la arquitectura definida.
- No introducir tecnologías innecesarias.
- No cambiar decisiones existentes sin autorización.
- No implementar Factus antes de que la plataforma interna esté preparada.
- No crear funcionalidades fuera del alcance sin indicarlo.

Cuando exista una decisión técnica que pueda afectar la arquitectura, seguridad, modelo de datos, multiempresa, permisos o integración externa, detenerse y solicitar confirmación antes de modificar el diseño.

Este documento representa el contexto técnico base del proyecto.