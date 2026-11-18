# Guion de defensa oral de InvenShop

## Datos generales

- **Proyecto:** InvenShop - Sistema de Gestión de Inventario y Comercio Electrónico
- **Materia:** Programación IV (2026)
- **Duración:** 15 minutos
- **Modalidad:** 5 bloques obligatorios
- **Objetivo:** explicar la arquitectura, demostrar el funcionamiento y justificar las decisiones técnicas

Antes de comenzar, activar el entorno virtual, ejecutar las migraciones, cargar los datos de demostración e iniciar el servidor:

```powershell
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/catalogo/` y tener los siguientes usuarios disponibles:

| Rol | Email | Contraseña |
| --- | --- | --- |
| Administrador | `admin@invenshop.com` | `Admin1234!` |
| Empleado | `empleado@invenshop.com` | `Empleado1234!` |
| Cliente | `cliente@invenshop.com` | `Cliente1234!` |

---

## BLOQUE 1: Introducción y planteo del problema

**Duración:** 2 minutos

**Objetivo:** presentar al equipo, describir la problemática de la PyME y explicar los perfiles de usuario del sistema.

**Acción en pantalla:** mostrar la portada o el catálogo público con el servidor `runserver` iniciado.

### Exposición oral

> “Buenas tardes, profesora. Mi nombre es [Nombre] y junto a mi compañero/a [Nombre] vamos a defender nuestro Trabajo Práctico Anual: **InvenShop - Sistema de Gestión de Inventario y Comercio Electrónico**.
>
> El proyecto surge para resolver la ineficiencia operativa de PyMEs que gestionan sus ventas e inventarios mediante planillas manuales. Ese sistema provoca inconsistencias de stock y demoras en la atención al cliente.
>
> Diseñamos una solución monolítica en Django que incorpora tres perfiles principales. El **Cliente** puede navegar el catálogo y realizar compras; el **Empleado** administra el catálogo, el stock y los pedidos; y el **Administrador** tiene control sobre usuarios, permisos y todo el sistema.”

### Ideas principales

- Presentar el equipo y el nombre del proyecto.
- Definir la problemática.
- Explicar el objetivo general.
- Diferenciar los tres roles.

---

## BLOQUE 2: Arquitectura y modelo de datos

**Duración:** 3 minutos

**Objetivo:** explicar el patrón MVT, la modularización, las relaciones principales y la integridad de los datos.

**Acción en pantalla:** mostrar el esquema de carpetas del proyecto o un diagrama entidad-relación.

### Exposición oral

> “Estructuramos el sistema bajo el patrón **MVT**, que significa Modelo-Vista-Plantilla. La petición HTTP entra por el enrutador, se dirige a una vista, esta utiliza los modelos y el ORM para consultar o modificar la base de datos y finalmente devuelve una respuesta mediante una plantilla DTL.
>
> El proyecto está modularizado en las aplicaciones obligatorias `usuarios`, `catalogo` y `pedidos`. Además, agregamos `panel` para el dashboard de gestión y el reporte CSV.
>
> En `usuarios` reemplazamos el modelo predeterminado de Django por un **Custom User Model**. El correo electrónico es el identificador único y el campo `rol` define si el usuario es Cliente, Empleado o Administrador.
>
> En `catalogo` modelamos `Categoria` y `Producto`. La relación utiliza `ForeignKey` y una política de eliminación `PROTECT`, que impide borrar una categoría con productos asociados o un producto que ya tenga registros históricos.
>
> En `pedidos` modelamos `Pedido` y `DetallePedido`. El detalle guarda una copia del precio unitario y el pedido conserva los datos de envío, de manera que las modificaciones posteriores del catálogo o del perfil no cambien el histórico de una venta.”

### Flujo HTTP breve

```text
Navegador
  -> config/urls.py
  -> vista
  -> modelo / ORM
  -> base de datos
  -> plantilla DTL
  -> HttpResponse
```

---

## BLOQUE 3: Demostración funcional en vivo

**Duración:** 5 minutos

**Objetivo:** realizar el flujo principal de compra, controlar stock y demostrar la gestión de permisos mediante datos reales precargados.

### Paso 1: navegación pública y carrito en sesión

**Acción en pantalla:** abrir `http://127.0.0.1:8000/catalogo/` como usuario anónimo.

**Exposición oral:**

> “Comenzamos como visitante anónimo. El catálogo muestra 12 productos por página y permite buscar por nombre o descripción, filtrar por categoría y ordenar por nombre o precio.
>
> Si abrimos el producto **Webcam Full HD**, vemos que está marcado como **Agotado** y el sistema no permite agregarlo al carrito. También podemos agregar un producto disponible.
>
> El carrito se almacena en `request.session['carrito']`. De esta manera, un usuario puede comprar sin iniciar sesión. El carrito guarda las cantidades y los importes se calculan leyendo el producto actualizado desde la base de datos.
>
> Además, el stock se valida cuando se agrega o actualiza un producto y vuelve a validarse al confirmar el pedido.”

### Paso 2: autenticación de cliente y checkout

**Acción en pantalla:**

1. Abrir el carrito.
2. Hacer clic en finalizar la compra.
3. Iniciar sesión con `cliente@invenshop.com`.
4. Completar dirección, ciudad, código postal y teléfono.
5. Confirmar el pedido.

**Exposición oral:**

> “Al intentar finalizar la compra, el sistema solicita iniciar sesión porque el checkout está protegido por `LoginRequiredMixin`. Ingresamos con el usuario cliente precargado y completamos los datos de envío.
>
> Al confirmar, la creación del pedido se procesa dentro de una transacción. El backend vuelve a verificar el stock disponible, crea el pedido y sus detalles, descuenta las unidades del inventario y vacía el carrito. El pedido queda registrado inicialmente en estado **Pendiente**.
>
> Luego podemos volver al historial y comprobar que el cliente solo puede ver sus propios pedidos.”

### Paso 3: gestión de empleado

**Acción en pantalla:**

1. Cerrar la sesión del cliente.
2. Iniciar sesión con `empleado@invenshop.com`.
3. Abrir `/panel/`.
4. Abrir un pedido nuevo.
5. Cambiarlo de **Pendiente** a **Pagado** y luego a **Enviado**.
6. Cancelar otro pedido pendiente y mostrar la reposición de stock.
7. Intentar ingresar a `/cuenta/gestion/` para demostrar la restricción 403.

**Exposición oral:**

> “Ahora cambiamos al rol Empleado. Ingresamos al panel de gestión y vemos las métricas principales.
>
> Cambiamos un pedido de **Pendiente** a **Pagado** y luego a **Enviado**. El sistema valida que la transición sea permitida.
>
> Si cancelamos otro pedido que estaba Pendiente, el backend repone automáticamente las unidades al stock. La reposición ocurre una sola vez, ya que una cancelación posterior o el regreso a un estado de cancelado no vuelven a sumar stock.
>
> También probamos el control de permisos. Si el Empleado intenta administrar usuarios o el Cliente intenta acceder a una URL de gestión, el sistema responde con un error 403 Forbidden o redirige según la autenticación correspondiente.”

---

## BLOQUE 4: inmersión en el código en el IDE

**Duración:** 4 minutos

**Objetivo:** abrir el editor y justificar las decisiones técnicas sin leer el código línea por línea.

**Acción en pantalla:** abrir el VS Code con los archivos relacionados con modelos, vistas, reglas de negocio y seguridad.

### Exposición oral

> “En `usuarios/models.py` reemplazamos el identificador por `email` mediante `USERNAME_FIELD = 'email'`. No utilizamos el campo `username` y definimos nombre, apellido, teléfono y rol.
>
> Para evitar credenciales expuestas, la clave secreta y las opciones de base de datos se cargan desde variables de entorno mediante `python-dotenv`. Todas las acciones POST incluyen el token `{% csrf_token %}` y el motor de plantillas protege automáticamente frente a XSS.”

Abrir `catalogo/views.py`:

> “En `ProductoListView` utilizamos una vista basada en clases `ListView`, con paginación de 12 productos por página. En `get_queryset()` filtramos los productos activos y aplicamos objetos `Q` para combinar la búsqueda por nombre y descripción.
>
> También usamos `.select_related('categoria')`. Esto evita el problema N+1 porque carga la categoría dentro de la misma consulta SQL cuando existe una relación ForeignKey.”

Abrir `pedidos/services.py`:

> “Las reglas de negocio de pedidos están concentradas en `services.py`. `crear_pedido()` está decorada con `@transaction.atomic`, de modo que la creación del pedido, sus detalles y el descuento de stock forman una sola operación.
>
> Antes de crear el pedido, los productos se bloquean con `.select_for_update()` y se compara la cantidad solicitada con el stock disponible. Si dos usuarios intentan comprar simultáneamente, el segundo usuario espera al bloqueo y valida nuevamente el stock antes de confirmar.
>
> `cambiar_estado()` valida las transiciones permitidas. Desde Pendiente puede pasar a Pagado o Cancelado, desde Pagado puede pasar a Enviado o Cancelado, y Enviado o Cancelado no admiten nuevas transiciones.
>
> Para cancelar se utiliza `F('stock') + cantidad`, y para confirmar se utiliza `F('stock') - cantidad`. Estas operaciones se realizan directamente en la base de datos y dentro de la transacción.”

Abrir `usuarios/mixins.py` o `usuarios/backends.py`:

> “La autorización combina el campo `rol` con los grupos y permisos de Django. Los mixins protegen las vistas de gestión y el backend traduce el rol a permisos. Así el Cliente puede comprar y ver sus pedidos, el Empleado gestiona catálogo y pedidos, y el Administrador administra además usuarios y roles.”

### Archivos sugeridos para mostrar

1. `usuarios/models.py`
2. `catalogo/views.py`
3. `pedidos/services.py`
4. `usuarios/mixins.py`
5. `usuarios/backends.py`

No leer el código línea por línea. Explicar la finalidad de cada decisión y cómo se relaciona con la demostración funcional.

---

## BLOQUE 5: preguntas técnicas y cierre

**Duración:** 1 minuto

**Objetivo:** responder con solidez una o varias preguntas técnicas y cerrar la presentación.

### Pregunta 1: carrito en sesión

**Pregunta:** ¿Por qué eligieron manejar el carrito en la sesión y no guardar cada ítem en la base de datos desde el principio?

**Respuesta preparada:**

> “Elegimos la sesión HTTP porque la consigna permite a los usuarios armar el carrito antes de estar autenticados. Guardarlo directamente en la base de datos generaría registros huérfanos o escrituras innecesarias para usuarios anónimos.
>
> El carrito no modifica el inventario mientras el usuario navega. Al confirmar el checkout, el backend valida nuevamente el stock y realiza la persistencia completa del pedido y sus detalles dentro de una transacción.”

### Pregunta 2: roles y grupos

**Pregunta:** ¿Por qué utilizan roles y grupos de Django al mismo tiempo?

**Respuesta preparada:**

> “El campo `rol` funciona como fuente de verdad para las vistas y las reglas de la aplicación. Los grupos permiten asignar permisos de Django en bloque.
>
> Las señales mantienen sincronizados el rol y los grupos cuando se crea o modifica un usuario. Esta combinación permite que el Empleado acceda al Django Admin de catálogo y pedidos sin darle permisos sobre usuarios.”

### Pregunta 3: protección de pedidos ajenos

**Pregunta:** ¿Cómo evitan que un cliente vea pedidos de otro usuario?

**Respuesta preparada:**

> “Para las vistas de clientes filtramos el queryset por `usuario=request.user`. Por eso un usuario no puede obtener el detalle de un pedido ajeno por su URL: el queryset no encuentra el objeto y Django devuelve 404.
>
> El Staff utiliza otro filtro, porque Empleado y Administrador sí pueden consultar todos los pedidos.”

### Pregunta 4: precio unitario conservado

**Pregunta:** ¿Por qué guardan el precio dentro de `DetallePedido`?

**Respuesta preparada:**

> “Guardamos el precio unitario en el detalle para conservar el histórico de ventas. Si el producto cambia de precio, se elimina o se modifica posteriormente, el pedido mantiene el importe original que el cliente pagó.”

### Cierre

**Exposición oral:**

> “En resumen, InvenShop integra catálogo, carrito, checkout, pedidos, control de estados, roles y administración de inventario dentro de una aplicación monolítica Django.
>
> Implementamos validaciones de stock, transacciones, control de acceso y una interfaz que permite distinguir claramente las tareas de Cliente, Empleado y Administrador.
>
> Muchas gracias por escuchar la exposición. Quedamos disponibles para responder preguntas.”

---

## Cronómetro de exposición

| Bloque | Contenido | Tiempo |
| --- | --- | --- |
| 1 | Introducción y problema | 2 minutos |
| 2 | Arquitectura y modelo de datos | 3 minutos |
| 3 | Demostración funcional | 5 minutos |
| 4 | Explicación del código | 4 minutos |
| 5 | Preguntas y cierre | 1 minuto |
| **Total** |  | **15 minutos** |

---

## Recomendaciones finales

1. Tener activado el entorno virtual antes de comenzar.
2. Tener `runserver` activo y el navegador abierto en el catálogo.
3. Tener abiertos en el IDE únicamente los archivos que se van a explicar.
4. Tener anotadas las credenciales de demostración.
5. Utilizar productos y usuarios reales precargados mediante `seed_demo`.
6. No presentar datos de prueba informales como `test`, `asdf` o `admin123`.
7. No leer el código línea por línea.
8. Explicar el motivo y la finalidad de cada decisión técnica.
9. Ensayar el cambio entre Cliente y Empleado para evitar perder tiempo.
10. Priorizar una ruta demostrativa clara antes que intentar mostrar todas las funciones del sistema.

---

## Ruta prioritaria para ensayar

1. Catálogo público.
2. Producto con stock.
3. Producto **Webcam Full HD** con stock 0.
4. Agregar un producto al carrito.
5. Login como cliente.
6. Checkout y confirmación.
7. Historial del cliente.
8. Login como empleado.
9. Cambio de estado Pendiente -> Pagado -> Enviado.
10. Cancelación de un pedido y reposición de stock.
11. Intento de acceso 403.
12. Explicación breve en el IDE.

