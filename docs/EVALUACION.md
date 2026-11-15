# Guía de evaluación y demostración

Documento de apoyo para presentar InvenShop y verificar el cumplimiento de la consigna de Programación IV 2026.

---

## 1. Preparación de la demo

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Comprobar que la base tenga datos:

- 6 categorías.
- 26 productos (dos sin stock: Webcam Full HD y Mochila urbana).
- 4 usuarios de demostración.
- 5 pedidos en estados Pendiente, Pagado, Enviado y Cancelado.

Credenciales:

| Rol | Email | Contraseña |
| --- | --- | --- |
| Admin | `admin@invenshop.com` | `Admin1234!` |
| Empleado | `empleado@invenshop.com` | `Empleado1234!` |
| Cliente | `cliente@invenshop.com` | `Cliente1234!` |

---

## 2. Guion sugerido de demostración (10–15 minutos)

### 2.1 Catálogo público
1. Abrir <http://127.0.0.1:8000/catalogo/>.
2. Buscar `auriculares` y comprobar que filtra por nombre/descripción.
3. Elegir la categoría **Tecnología** y ordenar por **Menor precio**.
4. Navegar a la página 2 o 3 y verificar la paginación de 12 productos.
5. Abrir un producto con stock y mostrar el selector de cantidad.
6. Abrir **Webcam Full HD** y mostrar que está **Agotado** y no permite agregar al carrito.

### 2.2 Carrito sin sesión
1. Agregar un producto como visitante.
2. Abrir `/carrito/` y comprobar que se conserva.
3. Mostrar que para finalizar la compra se solicita iniciar sesión.

### 2.3 Cliente
1. Iniciar sesión con `cliente@invenshop.com`.
2. Verificar la redirección al catálogo.
3. Agregar productos, actualizar cantidades y quitar uno.
4. Intentar superar el stock y mostrar el mensaje de validación.
5. Finalizar la compra completando dirección, ciudad, código postal y teléfono.
6. Mostrar la pantalla de confirmación, el pedido en **Mis pedidos** y el carrito vacío.
7. Verificar que el stock del producto disminuyó.
8. Intentar abrir un pedido de otro cliente (`/pedidos/5/` con el cliente demo) y mostrar el 404.

### 2.4 Empleado
1. Cerrar sesión e ingresar con `empleado@invenshop.com`.
2. Verificar la redirección al panel `/panel/`.
3. Mostrar métricas: ventas, pedidos pendientes, ticket promedio, valor del inventario y stock bajo.
4. Abrir **Productos y stock** y editar stock/precio de un producto.
5. Abrir un pedido, cambiarlo de **Pendiente** a **Pagado** y luego a **Enviado**.
6. Crear un pedido nuevo y cancelarlo para mostrar la reposición automática de stock.
7. Intentar abrir `/cuenta/gestion/` y mostrar el 403 (el empleado no administra usuarios).

### 2.5 Administrador
1. Cerrar sesión e ingresar con `admin@invenshop.com`.
2. Abrir `/cuenta/gestion/` y cambiar el rol de un cliente a Empleado (o desactivar una cuenta).
3. Mostrar que el Administrador no puede quitarse su propio rol.
4. Abrir `/admin/` y recorrer:
   - Productos: búsqueda, filtros, edición rápida de `stock` y `activo`.
   - Pedidos: inline de detalle en solo lectura, sin alta ni borrado.
   - Usuarios: formulario personalizado sin `username`.
5. Ejecutar una acción masiva sobre pedidos y verificar el mensaje de resultado.

### 2.6 Pruebas y cierre
1. Ejecutar `python manage.py test` y mostrar **68 pruebas OK**.
2. Mostrar las páginas de error 403 y 404 personalizadas.
3. Recordar que las credenciales y `DEBUG=True` son solo para la entrega académica.

---

## 3. Checklist de rúbrica

| Criterio | Evidencia en el proyecto | Estado |
| --- | --- | --- |
| Proyecto Django con apps modulares | `usuarios`, `catalogo`, `pedidos`, `panel` | ✅ |
| Usuario personalizado y login por email | `usuarios/models.py`, `EmailAuthenticationForm` | ✅ |
| Roles y permisos | `Usuario.Rol`, `GestorMixin`, `AdminMixin`, vistas 403 | ✅ |
| Modelos y relaciones 1:N | `Categoria`, `Producto`, `Pedido`, `DetallePedido` | ✅ |
| Migraciones | `*/migrations/0001_initial.py`, `pedidos/0002_initial.py` | ✅ |
| Catálogo con 12 por página | `ProductoListView.paginate_by = 12` | ✅ |
| Búsqueda por nombre/descripción | `Q(nombre__icontains)` combinado con `Q(descripcion__icontains)` | ✅ |
| Filtro por categoría y orden | Parámetros `categoria` y `orden` | ✅ |
| Solo productos activos | `filter(activo=True)` en listado y detalle | ✅ |
| Producto agotado no se agrega | Validación en `Carrito.agregar` y UI sin botón | ✅ |
| Carrito en sesión | `pedidos/carrito.py` | ✅ |
| Actualizar, quitar y vaciar | Vistas POST con CSRF | ✅ |
| Validación de stock | Al agregar, actualizar y confirmar | ✅ |
| Checkout autenticado | `LoginRequiredMixin` en `CheckoutView` | ✅ |
| Datos de envío y validaciones | `CheckoutForm` + campos en `Pedido` | ✅ |
| Confirmación final | `PedidoConfirmacionView` y template | ✅ |
| Pedido atómico y descuento de stock | `crear_pedido` con `transaction.atomic` | ✅ |
| Carrito vaciado al confirmar | `carrito.vaciar()` dentro de la transacción | ✅ |
| Estados del pedido | Pendiente, Pagado, Enviado, Cancelado | ✅ |
| Solo staff cambia estados | `GestorMixin` en `PedidoEstadoUpdateView` | ✅ |
| Cancelación repone stock | `cambiar_estado` y `save_model` del admin | ✅ |
| Cliente solo ve sus pedidos | Filtro por usuario y 404 en detalle ajeno | ✅ |
| Admin con búsqueda y filtros | `search_fields`, `list_filter`, `date_hierarchy` | ✅ |
| Edición rápida de stock/activo | `list_editable` en `ProductoAdmin` | ✅ |
| Inline de pedido histórico | `DetallePedidoInline` de solo lectura | ✅ |
| Vistas basadas en clases | ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView | ✅ |
| ORM y optimización | `select_related`, `prefetch_related`, `annotate` | ✅ |
| Formularios con validaciones | `forms.py` de las cuatro apps | ✅ |
| CSRF / XSS | `{% csrf_token %}`, escape automático, sin `safe` con datos de usuario | ✅ |
| Herencia de templates | `base.html` + templates por app + partials | ✅ |
| Mensajes de feedback | Framework de mensajes con clases Bootstrap | ✅ |
| Pruebas automatizadas | 68 tests en las cuatro apps | ✅ |
| Datos de demostración | `seed_demo` idempotente con imágenes | ✅ |

---

## 4. Puntos técnicos para explicar durante la defensa

1. **¿Por qué el carrito está en la sesión?**
   Porque la consigna lo pide así y permite comprar sin registro. El carrito se valida contra la base al confirmar, donde se descuenta el stock de forma atómica.

2. **¿Cómo se evita que dos compras dejen stock negativo?**
   `crear_pedido` abre una transacción, bloquea los productos con `select_for_update`, valida el stock y recién entonces crea el pedido y descuenta.

3. **¿Por qué se guarda el precio en `DetallePedido`?**
   Para conservar el histórico: si el producto cambia de precio o se elimina, el pedido mantiene el valor original.

4. **¿Cómo se protege el acceso a pedidos ajenos?**
   El queryset se filtra por `usuario=request.user` para clientes y el detalle devuelve 404 si el pedido no pertenece al usuario.

5. **¿Por qué `PROTECT` en usuario y producto?**
   Para impedir que se borre un cliente con pedidos o un producto con ventas, preservando la integridad histórica.

6. **¿Cómo se evita el doble descuento/reposición de stock?**
   El cambio de estado valida la transición y, si el pedido ya está en el estado destino, no hace nada. La cancelación solo repone stock cuando pasa a Cancelado por primera vez.

7. **¿Qué consultas se optimizaron?**
   Catálogo (`select_related("categoria")`), pedidos (`select_related("usuario")`, `prefetch_related("detalles")`), dashboard y admin.

---

## 5. Limitaciones y mejoras posibles

- Pago simulado: no se integra una pasarela real; el estado **Pagado** lo marca el staff.
- El envío se coordina; no se calcula un costo automático.
- No se implementó recuperación de contraseña por email en la interfaz (Django Admin sí permite gestionarla).
- Para producción: `DEBUG=False`, `SECRET_KEY` propia, HTTPS, `ALLOWED_HOSTS` reales, PostgreSQL y un servidor WSGI/ASGI.
