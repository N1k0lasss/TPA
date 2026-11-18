# Bitácora técnica de InvenShop

> **Fecha de generación:** 2026-11-18  
> **Repositorio:** `C:\Users\niko\Desktop\TPA` (rama `main`)  
> **Commit más reciente:** `823892a` — *Agrega grupos de Django sincronizados con el rol de usuario*  
> **Estado:** funcionalmente completo; documentación y pruebas al día.

Este documento describe **lo que realmente hace el proyecto**, cómo está organizado en carpetas, qué responsabilidad tiene cada archivo, cómo se recorren los flujos principales y cuál es el estado actual frente a la consigna. Se basa en el código fuente, en el historial de Git y en los documentos de requisitos de `TPA_Requsisitos/`. No incluye texto copiado de esos documentos: solo los cita.

---

## Índice

1. [Ficha del proyecto](#1-ficha-del-proyecto)
2. [Bitácora de desarrollo](#2-bitácora-de-desarrollo)
3. [Mapa de carpetas](#3-mapa-de-carpetas)
4. [Arquitectura y ciclo de una petición](#4-arquitectura-y-ciclo-de-una-petición)
5. [Modelo de datos](#5-modelo-de-datos)
6. [Detalle por aplicación](#6-detalle-por-aplicación)
7. [Mapa de rutas](#7-mapa-de-rutas)
8. [Flujos funcionales](#8-flujos-funcionales)
9. [Seguridad y autorización](#9-seguridad-y-autorización)
10. [Datos y entorno](#10-datos-y-entorno)
11. [Pruebas automatizadas](#11-pruebas-automatizadas)
12. [Estado actual y pendientes](#12-estado-actual-y-pendientes)
13. [Comandos útiles](#13-comandos-útiles)
14. [Referencias](#14-referencias)

---

## 1. Ficha del proyecto

| Campo | Valor |
|---|---|
| Nombre oficial | **InvenShop – Sistema de Gestión e Inventario con Comercio Electrónico** |
| Materia | Programación IV (ITSE 2026), Tecnicatura Superior en Desarrollo de Software |
| Tipo | Aplicación web monolítica Django, patrón **MVT** |
| Objetivo | Administrar productos e inventario, procesar pedidos y ofrecer un catálogo público |
| Backend | Python 3.13, Django 5.2.19 LTS |
| Frontend | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, JavaScript, Django Template Language |
| Base de datos | SQLite por defecto; PostgreSQL opcional vía `DB_ENGINE=postgres` |
| Dependencias | `python-dotenv`, `Pillow`, `psycopg[binary]` |
| Apps propias | `usuarios`, `catalogo`, `pedidos`, `panel` |
| Migraciones | 6 archivos de migración (3 iniciales, 2 de ajuste y 1 de datos) |
| Pruebas | **83 tests OK** |
| Entorno | `venv/` (ignorado por Git), `.env` (ignorado) |

---

## 2. Bitácora de desarrollo

Historial real de commits, de más antiguo a más reciente:

| Fecha | Hash | Hito |
|---|---|---|
| 2026-11-13 21:21 | `e482608` | `v0.1` — primera versión funcional. |
| 2026-11-15 18:22 | `525e2ef` | Corrige paginación, histórico del admin y agrega documentación con capturas. |
| 2026-11-15 18:39 | `94880e7` | Cierra brechas de la consigna: permisos por rol y búsqueda por número de pedido. |
| 2026-11-15 19:20 | `28141e9` | Cumple el requisito de decoradores y agrega reporte CSV de pedidos. |
| 2026-11-18 13:49 | `2be60ef` | Documentación actualizada (`README.md`, `docs/EVALUACION.md`). |
| 2026-11-18 14:11 | `823892a` | Agrega grupos de Django sincronizados con el rol de usuario. |

### Qué aportó el último commit

- Migración `usuarios/0003_grupos_iniciales.py`: crea `Administradores`, `Empleados` y `Clientes` y asocia a los usuarios existentes según su `rol`.
- `usuarios/senales.py`: señal `post_migrate` que puebla los permisos de cada grupo y señal `post_save` que mantiene el grupo alineado cuando cambia el rol.
- `usuarios/backends.py`: constantes de grupos y `PERMISOS_POR_GRUPO`, reutilizando los permisos del backend de roles.
- `usuarios/admin.py`: `groups` y `user_permissions` pasan a ser de solo lectura en el formulario de usuario.
- `usuarios/tests.py`: nueva clase `GruposTests` con 4 pruebas. El total pasó de 79 a 83.
- Documentación actualizada en `README.md` y `docs/EVALUACION.md`.

**Detalle técnico resuelto:** Django crea los permisos de una sola app por cada señal `post_migrate`. Cuando dispara `usuarios`, todavía no existen los permisos de `catalogo` ni `pedidos`. La señal llama explícitamente a `create_permissions()` para todas las apps antes de poblar los grupos.

---

## 3. Mapa de carpetas

### 3.1 Árbol general

```text
TPA/
├── manage.py                       # Punto de entrada: runserver, migrate, test, seed_demo
├── requirements.txt                # Dependencias con versiones fijadas
├── .env                            # Variables locales (IGNORADO por Git)
├── .env.example                    # Plantilla de variables de entorno
├── .gitignore                      # Excluye venv, .env, db.sqlite3, media/, etc.
├── db.sqlite3                      # Base local (IGNORADA por Git)
├── README.md                       # Documentación principal de uso
│
├── config/                         # Configuración global del proyecto Django
│   ├── settings.py                 # Seguridad, apps, BD, auth, templates, i18n, media
│   ├── urls.py                     # Enrutador raíz con include() y handlers de error
│   ├── wsgi.py / asgi.py           # Puntos de entrada para servidores
│   └── __init__.py
│
├── usuarios/                       # Usuario personalizado, login, roles y permisos
│   ├── models.py                   # Usuario(AbstractUser), Rol, USERNAME_FIELD=email
│   ├── managers.py                 # UsuarioManager (create_user / create_superuser)
│   ├── backends.py                 # PermisosPorRolBackend + constantes de Group
│   ├── mixins.py                   # RolRequeridoMixin, GestorMixin, AdminMixin
│   ├── senales.py                  # Sincronización rol <-> Group (post_migrate/post_save)
│   ├── forms.py                    # Registro, login por email, perfil, gestión, password
│   ├── views.py                    # Registro, login, logout, perfil, gestión de usuarios
│   ├── admin.py                    # UsuarioAdmin personalizado
│   ├── urls.py                     # Namespace "usuarios"
│   ├── migrations/
│   │   ├── 0001_initial.py         # Crea Usuario
│   │   ├── 0002_alter_usuario_options.py  # Permisos personalizados
│   │   └── 0003_grupos_iniciales.py       # Datos: crea los 3 grupos
│   └── tests.py                    # 18 pruebas
│
├── catalogo/                       # Categorías, productos, catálogo y gestión
│   ├── models.py                   # Categoria, Producto
│   ├── forms.py                    # CategoriaForm, ProductoForm (validan imagen/precio/stock)
│   ├── views.py                    # Listado público, detalle y CRUD de gestión
│   ├── admin.py                    # CategoriaAdmin, ProductoAdmin (edición rápida)
│   ├── urls.py                     # Namespace "catalogo"
│   ├── templatetags/invenshop.py   # Filtros: pesos, estado_badge, rol_badge, querystring
│   ├── migrations/0001_initial.py
│   └── tests.py                    # 13 pruebas
│
├── pedidos/                        # Carrito, checkout, pedidos y estados
│   ├── carrito.py                  # Clase Carrito sobre request.session["carrito"]
│   ├── services.py                 # crear_pedido() y cambiar_estado() (transacciones)
│   ├── consultas.py                # filtrar_pedidos(): alcance por rol y filtros
│   ├── context_processors.py       # Contador de ítems del carrito para el navbar
│   ├── models.py                   # Pedido, DetallePedido
│   ├── forms.py                    # CheckoutForm, EstadoPedidoForm
│   ├── views.py                    # Vistas de carrito, checkout e historial
│   ├── admin.py                    # PedidoAdmin, inline de solo lectura, acciones masivas
│   ├── urls.py                     # Namespace "pedidos"
│   ├── urls_carrito.py             # Namespace "carrito"
│   ├── migrations/0001_initial.py, 0002_initial.py
│   └── tests.py                    # 29 pruebas
│
├── panel/                          # Dashboard, reportes, seed y páginas de error
│   ├── views.py                    # DashboardView, exportar_pedidos_csv, handlers 403/404/500
│   ├── urls.py                     # Namespace "panel"
│   ├── management/commands/seed_demo.py  # Carga de datos de demostración
│   └── tests.py                    # 19 pruebas
│
├── templates/                      # 29 plantillas DTL con herencia desde base.html
│   ├── base.html                   # Plantilla maestra: navbar, messages, bloques
│   ├── partials/                   # campo.html, paginacion.html, producto_card.html
│   ├── catalogo/                   # Listado, detalle, formularios y confirmaciones
│   ├── pedidos/                    # Carrito, checkout, confirmación, listado, detalle, estado
│   ├── usuarios/                   # Login, registro, perfil, password, gestión
│   ├── panel/                      # dashboard.html
│   └── errores/                    # 403.html, 404.html, 500.html
│
├── static/                         # Archivos estáticos globales
│   ├── css/estilos.css
│   ├── js/app.js
│   └── img/placeholder.svg
│
├── media/productos/seed/           # 26 imágenes PNG generadas por seed_demo (IGNORADO)
│
├── docs/
│   ├── BITACORA.md                 # Este documento
│   ├── EVALUACION.md               # Checklist de rúbrica y guion de demostración
│   └── capturas/                   # 14 capturas PNG (01 a 14)
│
└── TPA_Requsisitos/                # Fuentes de la consigna (no se modifican)
    ├── Sistema InvenShop.md
    ├── InvenShop Django.md
    ├── Auditoría InvenShop.md
    ├── extracted.txt
    └── TPA - programacionIV - 2026.docx.pdf
```

### 3.2 Responsabilidad de los archivos de la raíz

| Archivo | Responsabilidad |
|---|---|
| `manage.py` | Ejecuta comandos de gestión (`runserver`, `migrate`, `test`, `seed_demo`). |
| `requirements.txt` | Fija Django 5.2.19, Pillow 13.0.0, python-dotenv 1.2.4, psycopg 3.3.9 y transitivas. |
| `.env.example` | Documenta `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL` y `DB_*`. |
| `.env` | Valores locales reales. Nunca se versiona. |
| `.gitignore` | Excluye `venv/`, `.env`, `db.sqlite3`, `media/`, `staticfiles/`, cachés e IDEs. |
| `README.md` | Instalación, credenciales, rutas, decisiones de diseño y correspondencia con la consigna. |

---

## 4. Arquitectura y ciclo de una petición

```text
Navegador
   │  HttpRequest
   ▼
config/urls.py  ──include()──▶  usuarios/urls.py
                               catalogo/urls.py
                               pedidos/urls.py + urls_carrito.py
                               panel/urls.py
   ▼
Vistas (CBV mayoritariamente; 1 FBV para el CSV)
   │  Mixins / decoradores → autorización por rol
   ▼
Modelos + ORM  (services.py contiene las reglas de negocio)
   │  select_related / prefetch_related / transacciones
   ▼
Base de datos (SQLite / PostgreSQL)
   ▼
Contexto → Plantillas DTL (base.html + bloques + partials)
   ▼
HttpResponse (HTML o CSV)
```

**Separación de responsabilidades**

- `models.py` define datos y propiedades de presentación simples (`disponible`, `numero`, `subtotal`).
- `services.py` concentra la lógica de negocio delicada: crear pedidos y cambiar estados.
- `views.py` orquesta request/response y mensajes al usuario.
- Las plantillas solo presentan: no consultan la BD ni resuelven reglas de negocio. Los filtros de `templatetags/invenshop.py` son de formato (`pesos`, badges, query strings).

---

## 5. Modelo de datos

```text
Usuario (email = login, rol) ──1:N──▶ Pedido ──1:N──▶ DetallePedido ◀──N:1── Producto
                                                              │
Categoria ──1:N──▶ Producto ───────────────────────────────────┘
```

### Usuario (`usuarios/models.py`)

| Campo | Tipo / detalle |
|---|---|
| `email` | `EmailField(unique=True)`, `USERNAME_FIELD`. No existe `username`. |
| `nombre`, `apellido` | `CharField(100)`, obligatorios (`REQUIRED_FIELDS`). |
| `rol` | `TextChoices`: `Admin`, `Empleado`, `Cliente` (default). |
| `telefono` | `CharField(30)`, opcional. |
| `groups`, `user_permissions` | Heredados de `AbstractUser`; el grupo se sincroniza con el rol. |

`save()` normaliza el email a minúsculas y mantiene `is_staff` coherente con roles `Admin`/`Empleado` para habilitar el Django Admin.

### Categoria y Producto (`catalogo/models.py`)

| Modelo | Campos principales |
|---|---|
| `Categoria` | `nombre` (único), `descripcion`, `slug` (único, autogenerado si falta). |
| `Producto` | `nombre`, `descripcion`, `precio` (`Decimal`, > 0), `stock` ( positivo, default 0), `categoria` (FK `PROTECT`), `imagen`, `activo`, `fecha_creacion`, `fecha_actualizacion`. |

`Producto` expone `disponible` (`activo and stock > 0`), `stock_bajo` (≤ 5) y `etiqueta_stock` (`Agotado`, `¡Últimas N unidades!`, `Disponible`). Tiene índices por `(activo, categoria)` y `nombre`.

### Pedido y DetallePedido (`pedidos/models.py`)

| Modelo | Campos principales |
|---|---|
| `Pedido` | `usuario` (FK `PROTECT`), `fecha_creacion`, `estado`, `total`, `direccion`, `ciudad`, `codigo_postal`, `telefono_contacto`, `notas`. |
| `DetallePedido` | `pedido` (FK `CASCADE`), `producto` (FK `PROTECT`), `cantidad`, `precio_unitario`. Restricción de unicidad por `(pedido, producto)`. |

Los datos de envío y el precio unitario se **copian** al pedido para que el histórico no cambie si se edita el catálogo. El número visible es `#000001` (propiedad `numero`).

### Políticas de eliminación

- `PROTECT` en `Pedido.usuario`, `Producto.categoria` y `DetallePedido.producto`: impide borrar registros con histórico asociado.
- `CASCADE` solo en `DetallePedido.pedido`: al borrar un pedido se borran sus líneas.

---

## 6. Detalle por aplicación

### 6.1 `config/`

| Archivo | Responsabilidad |
|---|---|
| `settings.py` | Lee `.env` con `python-dotenv`; configura seguridad (CSRF, HSTS, cookies cuando `DEBUG=False`), `INSTALLED_APPS`, middleware, `AUTH_USER_MODEL = "usuarios.Usuario"`, `AUTHENTICATION_BACKENDS`, validadores de contraseña, idioma `es-ar`, zona `America/Argentina/Buenos_Aires`, media y mensajes mapeados a Bootstrap. |
| `urls.py` | Incluye los 5 namespaces, redirige `/` al catálogo y define `handler403/404/500`. Personaliza el título del admin. |
| `asgi.py` / `wsgi.py` | Entradas para servidores ASGI/WSGI. |

### 6.2 `usuarios/`

| Archivo | Responsabilidad |
|---|---|
| `models.py` | `Usuario`, roles y propiedades `es_admin`, `es_gestor`, `es_cliente`. |
| `managers.py` | Creación de usuarios y superusuarios con email. |
| `backends.py` | `PermisosPorRolBackend`: traduce el rol a permisos de Django; define `GRUPOS_POR_ROL` y `PERMISOS_POR_GRUPO`. |
| `senales.py` | `post_migrate` crea/actualiza grupos y sincroniza usuarios; `post_save` asigna el grupo según el rol. |
| `mixins.py` | `RolRequeridoMixin` (403 para autenticados sin permiso), `GestorMixin`, `AdminMixin`. |
| `forms.py` | Registro con validación de unicidad y fortaleza; login por email; perfil; cambio de contraseña; gestión de roles con regla "no podés quitarte tu propio rol". |
| `views.py` | `RegistroView`, `IniciarSesionView` (redirección por rol), `CerrarSesionView`, `PerfilView`, `CambiarPasswordView`, `UsuarioListView`, `UsuarioUpdateView`. |
| `admin.py` | `UsuarioAdmin` sin `username`, con grupos y permisos de solo lectura. |

### 6.3 `catalogo/`

| Archivo | Responsabilidad |
|---|---|
| `models.py` | `Categoria`, `Producto`, índices y etiquetas de stock. |
| `forms.py` | Validan nombre de categoría único, precio > 0, stock ≥ 0 e imágenes JPG/PNG/WEBP de hasta 2 MB. |
| `views.py` | `ProductoListView` (12 por página, `Q` objects, filtro por slug, orden), `ProductoDetailView`, CRUD de productos y categorías para staff. |
| `admin.py` | `list_editable` para `stock`/`activo`, filtros, búsqueda, `date_hierarchy`, conteo anotado de productos por categoría. |
| `templatetags/invenshop.py` | Filtros de plantilla para precios, badges y conservación de query strings. |

### 6.4 `pedidos/`

| Archivo | Responsabilidad |
|---|---|
| `carrito.py` | `Carrito`: agregar, actualizar, quitar, vaciar, iterar con producto fresco desde la BD y detección de stock insuficiente. Solo sesión. |
| `services.py` | `crear_pedido()` (atómico, `select_for_update`, descuento con `F()` y vaciado del carrito) y `cambiar_estado()` (transiciones válidas y reposición de stock). |
| `consultas.py` | `filtrar_pedidos()`: clientes solo los suyos; staff ve todos y puede buscar por número, nombre o email. La usa también el CSV. |
| `context_processors.py` | Expone `carrito_cantidad` al navbar. |
| `models.py` | `Pedido`, `DetallePedido`, estados y snapshot histórico. |
| `forms.py` | `CheckoutForm` con `clean_direccion`, `clean_ciudad`, `clean_codigo_postal` y `clean_telefono_contacto`; `EstadoPedidoForm` solo con transiciones posibles. |
| `views.py` | 5 vistas de carrito, `CheckoutView`, confirmación, historial, detalle y cambio de estado. |
| `admin.py` | Pedidos con inline de solo lectura, acciones masivas y reposición de stock al cancelar desde el admin. |

### 6.5 `panel/`

| Archivo | Responsabilidad |
|---|---|
| `views.py` | `DashboardView` (ventas, ticket promedio, inventario, stock bajo, últimos pedidos), `exportar_pedidos_csv` (FBV con decoradores) y handlers de error 403/404/500. |
| `management/commands/seed_demo.py` | Genera datos realistas e imágenes con Pillow; idempotente. |
| `urls.py` | `/panel/` y `/panel/pedidos.csv`. |

### 6.6 Plantillas, estáticos y documentación

| Ubicación | Contenido |
|---|---|
| `templates/base.html` | Estructura HTML5, Bootstrap 5, navbar por roles, bloques `titulo`, `contenido`, `css_extra`, `js_extra`. |
| `templates/partials/` | `producto_card.html`, `paginacion.html`, `campo.html`. |
| `static/css/estilos.css` | Estilos propios y clases de badges de estado/rol. |
| `static/js/app.js` | Comportamiento de interfaz (sin lógica de negocio). |
| `media/productos/seed/` | 26 PNG generados por `seed_demo` (no versionados). |
| `docs/capturas/` | 14 capturas numeradas que respaldan la demo. |
| `docs/EVALUACION.md` | Guion de demostración, checklist de rúbrica y puntos técnicos para la defensa. |

---

## 7. Mapa de rutas

| Namespace | Ruta | Vista | Protección |
|---|---|---|---|
| `catalogo` | `/catalogo/` | `ProductoListView` | Pública |
| `catalogo` | `/catalogo/producto/<pk>/` | `ProductoDetailView` | Pública (solo activos) |
| `catalogo` | `/catalogo/gestion/`, `/nuevo/`, `/<pk>/editar/`, `/<pk>/eliminar/` | CRUD de productos | `GestorMixin` |
| `catalogo` | `/catalogo/categorias/...` | CRUD de categorías | `GestorMixin` |
| `carrito` | `/carrito/` | `CarritoDetalleView` | Pública |
| `carrito` | `/carrito/agregar/<pk>/` | `AgregarAlCarritoView` | Pública (POST) |
| `carrito` | `/carrito/actualizar/<pk>/`, `/quitar/<pk>/`, `/vaciar/` | Vistas del carrito | Pública (POST) |
| `pedidos` | `/pedidos/checkout/` | `CheckoutView` | `LoginRequiredMixin` |
| `pedidos` | `/pedidos/` | `PedidoListView` | `LoginRequiredMixin` + filtro por rol |
| `pedidos` | `/pedidos/<pk>/` | `PedidoDetailView` | `LoginRequiredMixin` + 404 si es ajeno |
| `pedidos` | `/pedidos/<pk>/confirmacion/` | `PedidoConfirmacionView` | `LoginRequiredMixin` |
| `pedidos` | `/pedidos/<pk>/estado/` | `PedidoEstadoUpdateView` | `GestorMixin` |
| `panel` | `/panel/` | `DashboardView` | `GestorMixin` |
| `panel` | `/panel/pedidos.csv` | `exportar_pedidos_csv` | `@login_required` + `@permission_required` |
| `usuarios` | `/cuenta/registro/`, `/login/`, `/logout/` | Registro y auth | Públicas / logout autenticado |
| `usuarios` | `/cuenta/perfil/`, `/password/` | Perfil y contraseña | `LoginRequiredMixin` |
| `usuarios` | `/cuenta/gestion/...` | Gestión de usuarios | `AdminMixin` |
| `admin` | `/admin/` | Django Admin personalizado | Según rol y superusuario |

`/` redirige al catálogo. Las páginas 403, 404 y 500 tienen plantillas propias.

---

## 8. Flujos funcionales

### 8.1 Registro y acceso

1. `RegistroForm` valida email único (case-insensitive), coincidencia de contraseñas y `validate_password()`.
2. `RegistroView.form_valid()` fuerza `rol=Cliente`, guarda y autentica al usuario.
3. `EmailAuthenticationForm` llama a `authenticate(username=email, ...)`.
4. `IniciarSesionView.get_success_url()` envía a `panel:dashboard` si `es_gestor`, si no a `catalogo:producto_list`.
5. La señal `post_save` asigna el grupo `Clientes`, `Empleados` o `Administradores`.

### 8.2 Catálogo

1. `Producto.objects.filter(activo=True).select_related("categoria")`.
2. Búsqueda combinada `Q(nombre__icontains=q) | Q(descripcion__icontains=q)`.
3. Filtro por `categoria__slug` y orden por nombre, precio o fecha.
4. Paginación de 12. La tarjeta muestra `Agotado` cuando `stock == 0` y oculta el botón de compra.

### 8.3 Carrito

1. `Carrito(request)` lee/escribe `request.session["carrito"]`: `{id_producto: {"cantidad": n}}`.
2. `agregar()` valida que el producto esté activo y que `cantidad <= stock`.
3. `actualizar()` reemplaza la cantidad; `quitar()` y `vaciar()` limpian entradas.
4. `__iter__()` consulta los productos activos en una sola consulta, descarta los que ya no existen y calcula subtotales.
5. Ninguna operación persiste en la BD hasta el checkout.

### 8.4 Checkout y descuento de stock

1. `CheckoutView` exige login, carrito no vacío y `CheckoutForm` válido.
2. `crear_pedido()` abre `transaction.atomic()`, bloquea los productos con `select_for_update()` y valida stock nuevamente.
3. Crea `Pedido` y `DetallePedido` con el precio actual, descuenta con `F("stock") - cantidad`, guarda el total y vacía el carrito.
4. Redirige a la pantalla de confirmación.

### 8.5 Estados y cancelación

- Transiciones: `Pendiente → Pagado | Cancelado`; `Pagado → Enviado | Cancelado`; `Enviado` y `Cancelado` son finales.
- `cambiar_estado()` bloquea el pedido, valida la transición y, si el destino es `Cancelado`, repone `F("stock") + cantidad` por cada detalle.
- Si el estado destino es igual al actual, no hace nada (evita doble reposición).
- El admin usa las mismas reglas en `PedidoAdminForm.clean()`, en `save_model()` y en las acciones masivas.

### 8.6 Panel y reporte CSV

1. `DashboardView` calcula métricas con agregados y consultas optimizadas.
2. `exportar_pedidos_csv` reutiliza `filtrar_pedidos()` para respetar los mismos filtros del listado.
3. Protege contra fórmulas de Excel prefijando con `'` los valores que empiezan con `=`, `+`, `-` o `@`, y escribe BOM UTF-8.

---

## 9. Seguridad y autorización

### Matriz de roles

| Recurso | Anónimo | Cliente | Empleado | Admin |
|---|---|---|---|---|
| Catálogo y detalle | ✅ | ✅ | ✅ | ✅ |
| Carrito | ✅ | ✅ | ✅ | ✅ |
| Checkout e historial propio | ❌ | ✅ | ✅ | ✅ |
| Perfil y contraseña | ❌ | ✅ | ✅ | ✅ |
| Panel y CSV | ❌ | ❌ | ✅ | ✅ |
| CRUD de productos/categorías | ❌ | ❌ | ✅ | ✅ |
| Cambio de estado de pedidos | ❌ | ❌ | ✅ | ✅ |
| Gestión de usuarios y roles | ❌ | ❌ | ❌ | ✅ |
| Django Admin | ❌ | ❌ | Catálogo y Pedidos | Todo |

### Mecanismos

- **CBVs:** `LoginRequiredMixin`, `PermissionRequiredMixin`, `GestorMixin` y `AdminMixin`. Un autenticado sin permiso recibe 403; un anónimo es redirigido al login.
- **FBV:** `@login_required` y `@permission_required("usuarios.gestionar_tienda", raise_exception=True)` en el CSV.
- **Grupos:** el backend de roles concede los permisos de la tienda y los `Group` de Django reflejan el rol para el admin. `post_migrate` y `post_save` mantienen la sincronía.
- **Clientes sin permisos de modelo:** a propósito. Darles `view_pedido` les abriría el Django Admin; su privacidad se resuelve filtrando el queryset por usuario.
- **Login por email**, validadores de contraseña de Django (mínimo 8, similarity, common, numeric).
- **CSRF** en todos los formularios POST. Escape automático de variables en DTL; no se usa `safe` con datos de usuario.
- **Redirecciones seguras** en el carrito mediante `url_has_allowed_host_and_scheme`.
- **Secretos** en `.env` vía `python-dotenv`; `.env` y `db.sqlite3` están fuera de Git.
- **Endurecimiento** cuando `DEBUG=False`: SSL redirect, cookies seguras, HSTS y headers de referrer/frame.

---

## 10. Datos y entorno

### Comando `seed_demo`

`python manage.py seed_demo` carga, de forma idempotente:

- 6 categorías: Tecnología, Hogar, Indumentaria, Deportes, Librería, Belleza.
- 26 productos con descripción realista; 2 sin stock (*Webcam Full HD* y *Mochila urbana*).
- 4 usuarios de demostración con roles Admin, Empleado y dos Clientes.
- 5 pedidos en estados Pendiente, Pagado, Enviado y Cancelado.
- 26 imágenes PNG generadas con Pillow en `media/productos/seed/` (se puede omitir con `--sin-imagenes`).

### Credenciales de demostración

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@invenshop.com` | `Admin1234!` |
| Empleado | `empleado@invenshop.com` | `Empleado1234!` |
| Cliente | `cliente@invenshop.com` | `Cliente1234!` |
| Cliente | `lucia@invenshop.com` | `Cliente1234!` |

### Migraciones

| App | Migraciones |
|---|---|
| `catalogo` | `0001_initial.py` |
| `pedidos` | `0001_initial.py`, `0002_initial.py` |
| `usuarios` | `0001_initial.py`, `0002_alter_usuario_options.py`, `0003_grupos_iniciales.py` |

`makemigrations --check --dry-run` informa **No changes detected**.

### Variables de entorno principales

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SECURE_SSL_REDIRECT`, `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

---

## 11. Pruebas automatizadas

`python manage.py test` → **83 tests OK**.

| App | Pruebas | Temas cubiertos |
|---|---:|---|
| `usuarios` | 18 | Registro, login por email, redirección por rol, permisos, perfil, cambio de contraseña, grupos y backend. |
| `catalogo` | 13 | Búsqueda, filtros, orden, paginación, productos inactivos, CRUD y validación de imágenes. |
| `pedidos` | 29 | Carrito, stock, checkout atómico, precios congelados, estados, reposición, seguridad de objeto, admin y CSV. |
| `panel` | 19 | Métricas, dashboard, reporte CSV, páginas de error, admin por rol y `seed_demo`. |

También se cubren la búsqueda por número visible `#000001`, el acceso al admin según rol y la idempotencia del comando de datos demo.

---

## 12. Estado actual y pendientes

### Completo a nivel funcional

- Los 16 requisitos de la matriz de auditoría están resueltos o tienen una decisión tomada: MVT, 3 apps (+ `panel`), usuario personalizado, roles y grupos, catálogo paginado, carrito en sesión, checkout atómico, estados y reposición, ORM optimizado, admin personalizado, `.env`/CSRF, CBVs y formularios.
- 83 pruebas en verde, migraciones limpias, documentación y capturas actualizadas.
- Commit `823892a` aplicado; `git status` limpio.

### Pendientes que no son de código

| Ítem | Naturaleza |
|---|---|
| **Defensa oral** de 15 a 30 min en 5 bloques | Humana. Guion listo en `docs/EVALUACION.md`. |
| **Exención por Práctica Profesionalizante** | Normativa. Solo aplica si el grupo ya aprobó otro proyecto Django en esa materia. |
| **Django REST Framework** | Decisión: no se implementa. Es opcional en la rúbrica y el plan recomienda MVT/DTL. |
| **Producción real** (`DEBUG=False`, clave propia, HTTPS, PostgreSQL) | Mejora documentada, no exigida para la entrega académica. |

### Observación sobre la base local

La SQLite no versionada contiene un usuario extra `correo@prueba.com` (nombre "niko", sin pedidos) que no proviene de `seed_demo`. Conviene no mostrarlo en la demo o eliminarlo antes de la exposición, porque la consigna prohíbe datos de relleno. No se tocó al generar esta bitácora.

---

## 13. Comandos útiles

```powershell
# Entorno
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Base y datos de demostración
python manage.py migrate
python manage.py seed_demo
python manage.py seed_demo --sin-imagenes

# Servidor y pruebas
python manage.py runserver
python manage.py test
python manage.py test pedidos

# Verificación de migraciones
python manage.py makemigrations --check --dry-run

# Superusuario adicional
python manage.py createsuperuser
```

---

## 14. Referencias

| Documento | Contenido |
|---|---|
| `README.md` | Instalación, funcionalidades, rutas, decisiones de diseño y correspondencia con la consigna. |
| `docs/EVALUACION.md` | Checklist de rúbrica, guion de demostración y respuestas técnicas para la defensa. |
| `TPA_Requsisitos/Sistema InvenShop.md` | Análisis académico y técnico del TPA. |
| `TPA_Requsisitos/InvenShop Django.md` | Planificación técnica y etapas de implementación. |
| `TPA_Requsisitos/Auditoría InvenShop.md` | Matriz REQ-01…REQ-16, correcciones y checklist previo al desarrollo. |
| `TPA_Requsisitos/TPA - programacionIV - 2026.docx.pdf` | Consigna original. |

---

*Fin de la bitácora.*
