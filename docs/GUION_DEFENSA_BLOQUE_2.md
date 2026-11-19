# Guion de defensa oral — Bloque 2: Arquitectura y modelo de datos

> **Complemento** del Bloque 2 de [`GUIA_DEFENSA.md`](GUIA_DEFENSA.md).
> **Duración:** 3 minutos · **Extensión del texto:** ~390 palabras (ritmo de 130–140 ppm).
> **Objetivo:** explicar el patrón MVT, la modularización, las relaciones y la integridad de los datos.
> **Acción en pantalla:** esquema de carpetas del proyecto y/o diagrama entidad-relación.

---

## Antes de empezar (tener listo)

- Explorador de archivos con la raíz del proyecto abierta: `config/`, `usuarios/`, `catalogo/`, `pedidos/`, `panel/`.
- El diagrama ER de más abajo abierto en el visor de Markdown, o dibujado en el papel.
- Opcional: los tres `models.py` abiertos en pestañas, por si el jurado pide ver un campo puntual.
- **No** hace falta el navegador en este bloque; se usa recién en el Bloque 3.

---

## Guion literal (3 minutos)

### 1. Apertura: patrón MVT — 0:00 a 0:45

> “Bueno, pasamos al bloque de arquitectura. InvenShop es un **monolito Django** basado en el patrón **MVT**: Modelo, Vista y Plantilla. La petición del navegador entra por `config/urls.py`, que es el enrutador raíz y deriva a la app correspondiente. La **vista**  consulta los **modelos** a través del ORM, aplica las reglas de negocio y devuelve una **plantilla DTL** como respuesta HTTP. — pausa —
>
> Un detalle que queremos remarcar: las reglas de negocio no están dentro de la vista ni dentro del modelo, sino en módulos **`services.py`**. Así la vista queda por un lado y esa lógica se puede reutilizar y probar por separado.”

**👉 Mostrar:** el árbol de carpetas y, un segundo, `config/urls.py` con los `include()`.

---

### 2. Modularización en apps — 0:45 a 1:20

> “El sistema está modularizado en **cuatro aplicaciones**. Las tres obligatorias son **`usuarios`**, **`catalogo`** y **`pedidos`**; agregamos **`panel`** para el dashboard de gestión y el reporte CSV. Cada app es autocontenida: tiene sus propios `models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`, migraciones y tests. — pausa —
>
> En el `panel`,**no se definen modelos nuevos**: solo consulta los existentes para calcular métricas. Toda la configuración global —rutas, base de datos, autenticación, middleware— vive en la carpeta`config/`.”

**👉 Mostrar:** las carpetas de las cuatro apps y el `INSTALLED_APPS` de `config/settings.py`.

---

### 3. El usuario personalizado — 1:20 a 1:55

> “En el modelo de datos, el primer riesgo fue el usuario. Reemplazamos el usuario por defecto de Django **antes de la primera migración** con un **Custom User Model**, definido en `usuarios/models.py` y registrado con `AUTH_USER_MODEL` en `config/settings.py`.
>
> El identificador es el **email**, con `USERNAME_FIELD = 'email'`; directamente **no existe el campo `username`**. Y el campo **`rol`** —Cliente, Empleado o Administrador— es una de las decisiones centrales: define qué puede hacer cada persona y se mantiene sincronizado con los grupos de Django.”

**👉 Mostrar:** `usuarios/models.py` (USERNAME_FIELD y Rol) y la línea `AUTH_USER_MODEL`.

---

### 4. Catálogo: categorías y productos — 1:55 a 2:25

> “En `catalogo` tenemos dos modelos: **`Categoria`** y **`Producto`**. La relación es **uno a muchos**: una categoría tiene muchos productos, y cada producto apunta a su categoría con una `ForeignKey`.
>
> Acá elegimos **`on_delete=PROTECT`**: no se puede borrar una categoría mientras tenga productos asociados. Es una decisión de integridad, evita productos huérfanos en el catálogo. El producto además valida **precio mayor a cero** y **stock no negativo**, y tiene índices para acelerar la búsqueda y los filtros.”

**👉 Mostrar:** el diagrama ER, señalando la flecha Categoría → Producto.

---

### 5. Pedidos y snapshot histórico — 2:25 a 2:50

> “En `pedidos` están **`Pedido`** y **`DetallePedido`**. El pedido apunta al usuario, también con **`PROTECT`**, así que no se puede borrar un cliente con historial; y tiene muchos detalles.
>
> Cada detalle guarda el producto, la cantidad y, algo clave, una **copia del precio unitario** al momento de la compra. Los datos de envío también se copian dentro del pedido. Es el concepto de **snapshot**: si mañana cambiamos el precio de un producto o el cliente se muda, el pedido antiguo sigue mostrando exactamente lo que se compró y pagó. — pausa —
>
> El detalle, en cambio, sí se borra en **cascada** junto con su pedido, porque una línea sin el pedido padre no tiene sentido.”

**👉 Mostrar:** la flecha Pedido → DetallePedido y el campo `precio_unitario`.

---

### 6. Cierre y puente al Bloque 3 — 2:50 a 3:00

> “En resumen: **cinco modelos propios**, relaciones uno a muchos, `PROTECT` donde hay histórico y `CASCADE` solamente adentro del pedido. Ahora les muestro cómo se usa todo esto en el flujo real de compra.”

---

## Diagrama entidad-relación para proyectar

```mermaid
erDiagram
    USUARIO ||--o{ PEDIDO : "realiza · PROTECT"
    PEDIDO  ||--|{ DETALLE_PEDIDO : "contiene · CASCADE"
    PRODUCTO ||--o{ DETALLE_PEDIDO : "aparece en · PROTECT"
    CATEGORIA ||--o{ PRODUCTO : "agrupa · PROTECT"

    USUARIO {
        Email email PK "USERNAME_FIELD"
        string nombre
        string apellido
        string rol "Admin / Empleado / Cliente"
        string telefono
    }
    CATEGORIA {
        string nombre UK
        string slug UK
    }
    PRODUCTO {
        decimal precio ">= 0.01"
        int stock ">= 0"
        bool activo
        FK categoria
    }
    PEDIDO {
        string estado "Pendiente / Pagado / Enviado / Cancelado"
        decimal total
        string direccion "snapshot de envío"
        string ciudad
        string codigo_postal
        string telefono_contacto
    }
    DETALLE_PEDIDO {
        int cantidad
        decimal precio_unitario "snapshot de precio"
    }
```

Versión simple, por si no hay proyector:

```text
Usuario (email = login, rol) ──1:N──▶ Pedido ──1:N──▶ DetallePedido ◀──N:1── Producto
                                                           ▲                    ▲
                                                           └──────── N:1 ────────┘
Categoria ──1:N──▶ Producto
```

**Frase para acompañar el diagrama:** “El pedido es el centro: une al cliente con los productos, pero guarda su propia copia del precio y del envío para que el histórico sea inmutable.”

---

## Mapa rápido: archivo → qué dice de este bloque

| Archivo | Punto que apoya |
| --- | --- |
| `config/settings.py` | `AUTH_USER_MODEL`, `ROOT_URLCONF`, apps instaladas, motores de BD (SQLite/PostgreSQL) por `.env` |
| `config/urls.py` | Enrutador raíz con `include()` hacia las cuatro apps |
| `usuarios/models.py` | Usuario personalizado, `USERNAME_FIELD`, `Rol`, permisos `gestionar_tienda` / `gestionar_usuarios` |
| `catalogo/models.py` | `Categoria` 1:N `Producto`, `PROTECT`, validadores, índices |
| `pedidos/models.py` | `Pedido` 1:N `DetallePedido`, `PROTECT`/`CASCADE`, snapshot, `UniqueConstraint(pedido, producto)` |
| `panel/models.py` | Sin modelos propios: confirma que `panel` solo consume datos |

---

## Preguntas probables del jurado sobre este bloque

**¿Por qué MVT y no una API REST con DRF?**
> “La consigna lo daba como opcional y la opción recomendada era MVT con DTL. Como no hay clientes externos ni integraciones, un monolito que sirve HTML directamente reduce capas y complejidad. Igual separamos la lógica en `services.py`, que es lo que después permitiría agregar una API sin reescribir las reglas.”

**¿Por qué un usuario personalizado y por qué antes de migrar?**
> “Porque el login es por email y el modelo por defecto de Django usa `username`. Cambiar `AUTH_USER_MODEL` a mitad de proyecto obligaría a recrear migraciones y tablas con datos; hacerlo desde el inicio evita ese problema.”

**¿Por qué `PROTECT` y no `CASCADE` en las relaciones con usuarios y productos?**
> “`CASCADE` borraría el histórico: si se elimina un cliente, se irían sus pedidos; si se elimina un producto, se irían las líneas vendidas. `PROTECT` obliga a desactivar el producto (`activo=False`) en lugar de borrarlo, y preserva las ventas. `CASCADE` solo tiene sentido de pedido hacia sus detalles, que viven y mueren juntos.”

**¿Qué pasa si cambia el precio de un producto que ya se vendió?**
> “Nada en el pedido: `DetallePedido.precio_unitario` guarda el valor original. Es la misma idea con dirección, ciudad, código postal y teléfono en `Pedido`. El histórico no se recalcula nunca desde el catálogo.”

**¿Cómo evitan duplicar el mismo producto dos veces en un pedido?**
> “Con `UniqueConstraint(fields=['pedido', 'producto'])` en `DetallePedido`. Y si el cliente vuelve a agregarlo, el carrito suma la cantidad en lugar de crear otra línea.”

**¿Dónde está el carrito dentro del modelo de datos?**
> “No está como modelo: vive en `request.session['carrito']`, porque la consigna permite armarlo sin iniciar sesión. Persiste en la tabla de sesiones de Django, pero no es una entidad del dominio; cuando se confirma la compra recién se materializa en `Pedido` y `DetallePedido`.”

**¿Por qué hay `rol` y también grupos de Django?**
> “El `rol` es la fuente de verdad para las reglas de la tienda; los grupos permiten gestionar permisos en bloque. La migración `usuarios.0003` los crea, las señales `post_migrate` y `post_save` los sincronizan con el rol, y el backend traduce el rol a permisos. El grupo `Clientes` no tiene permisos de modelo a propósito: eso le abriría el Django Admin, y su privacidad se resuelve filtrando el queryset.”

**¿Para qué sirven los índices que mencionaron?**
> “Para no recorrer toda la tabla en las consultas frecuentes: `activo + categoria` y `nombre` en productos, `usuario + fecha` y `estado` en pedidos, más `db_index` en `rol`. En listados grandes eso se nota, y además usamos `select_related`/`prefetch_related` para evitar el problema N+1.”

**¿Cómo se representa el número de pedido `#000001`?**
> “No es un campo guardado: es una propiedad que formatea la primary key con seis dígitos, `f'#{self.pk:06d}'`. Así no puede haber duplicados ni desfase con la base.”

**¿Qué pasa si mañana quieren PostgreSQL?**
> “No hay que tocar los modelos. `config/settings.py` elige el motor según `DB_ENGINE` del `.env`; con `postgres` y las variables `DB_*` completas, corremos las mismas migraciones.”

---

## Si se complica o sobra tiempo

- **Si te quedás corto:** agregá una frase sobre los permisos personalizados —“en `Usuario.Meta.permissions` definimos `gestionar_tienda` y `gestionar_usuarios`, que el backend concede según el rol”— y otra sobre el número de pedido.
- **Si te sobra tiempo:** mencioná que las seis migraciones (`usuarios` 0001–0003, `catalogo` 0001, `pedidos` 0001–0002) reflejan exactamente este modelo, y que `makemigrations --check --dry-run` no detecta cambios pendientes.
- **Si te preguntan algo de checkout o estados:** no te adelantes; respondé breve y decí “eso lo vemos en el bloque de demostración / de código”.

## Errores a evitar

- No leer `models.py` línea por línea: **mostrar el diagrama y explicar la finalidad**.
- No decir “MySQL” ni “microservicios”: es **SQLite/PostgreSQL** y es un **monolito**.
- No confundir `PROTECT` con “no se puede modificar”: solo **impide borrar**; el stock se edita normalmente.
- No decir que el cliente pertenece a un grupo con permisos: el grupo `Clientes` **no tiene permisos de modelo**.
- No mencionar el carrito como “la tabla carrito”: se llama **sesión**, no modelo.
