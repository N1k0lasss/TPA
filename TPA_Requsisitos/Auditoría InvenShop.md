# Auditoría Crítica y Matriz de Trazabilidad del TPA: InvenShop

Se presenta una auditoría técnica y académica exhaustiva sobre el análisis y la planificación del Trabajo Práctico Anual (**InvenShop**), contrastando cada decisión arquitectónica y funcional contra la totalidad de las fuentes del cuaderno 1-5.

## 1\. Matriz de Trazabilidad Requisitos vs. Fuentes

La siguiente matriz mapea cada especificación del proyecto con su fuente oficial, obligatoriedad, implementación prevista en Django, método de verificación y estado de auditoría:  
ID,Requisito,Fuente,Categoría,Obligatoriedad,Implementación Prevista,Método de Verificación,Estado  
REQ-01,Arquitectura Monolítica MVT,TPA.pdf (Secc. 3\) 6   Clase 6 1,Arquitectura,Obligatorio,"Proyecto monolítico en Django dividiendo Modelos, Vistas y Plantillas DTL con herencia base 1, 6.",Inspección de la estructura de carpetas y funcionamiento sin servidores API externos.,Validado  
REQ-02,"Modularización en 3 Apps (usuarios, catalogo, pedidos)","TPA.pdf (Secc. 4\) 7   Clase 6/7 8, 9",Arquitectura,Obligatorio,Tres aplicaciones aisladas mediante startapp y desacopladas en el urls.py principal con include() 7-9.,"Verificación de existencia de las tres carpetas de app y sus urls.py correspondientes 8, 9.",Validado  
REQ-03,Custom User Model (Login por Email),"TPA.pdf (Secc. 4, 5.1) 7, 10   Clase 12 11, 12",Seguridad / Datos,Obligatorio,"Modelo Usuario(AbstractUser) en usuarios con email como USERNAME\_FIELD único y campo rol 7, 11, 12.","Ejecución de createsuperuser e inicio de sesión en /admin/ utilizando correo en vez de usuario 10, 13.",Validado  
REQ-04,Matriz de Permisos y Control de Acceso por Roles,"TPA.pdf (Secc. 5.1) 10, 14   Clase 10/12 15-17",Seguridad,Obligatorio,"Matriz para Admin, Empleado y Cliente mediante Group, @permission\_required y PermissionRequiredMixin 10, 14, 16, 17.",Intento de acceso directo por URL a vistas de gestión estando autenticado como Cliente (debe dar HTTP 403\) 10.,Validado  
REQ-05,"Catálogo Paginado (12 p/pág), Filtros y Búsqueda","TPA.pdf (Secc. 5.2) 14   Clase 7/9 18, 19",Funcional,Obligatorio,"ProductoListView(ListView) con paginate\_by=12, filtrado por categoría y búsqueda combinada con objetos Q 14, 18, 19.","Navegación del catálogo probando paginación, filtros laterales y caja de búsqueda en vivo 14.",Validado  
REQ-06,Control de Stock y Exclusión de Inactivos,"TPA.pdf (Secc. 5.2) 14   Clase 9 20, 21",Funcional / Negocio,Obligatorio,"Filtro activo=True en queryset, distintivo ""Agotado"" en plantilla y bloqueo de adición al carrito si stock \<= 0 14.","Comprobación visual del badge ""Agotado"" e intento de envío POST con cantidad mayor al stock 14.",Validado  
REQ-07,Carrito en Sesión HTTP,TPA.pdf (Secc. 5.2) 14   Clase 12 11,Funcional / Lógica,Obligatorio,"Gestión mediante request.session\['carrito'\] sin persistencia en base de datos preliminar 11, 14.",Navegación entre páginas verificando la persistencia de productos en la sesión y ausencia de registros en BD 14.,Validado  
REQ-08,Checkout y Procesamiento Atómico,"TPA.pdf (Secc. 5.3) 22   Clase 9/11 20, 23",Funcional / Técnico,Obligatorio,"Formulario de envío validado (CheckoutForm), generación de Pedido / DetallePedido en transaction.atomic() 22, 23.",Registro de pedido con descuento simultáneo en la tabla Producto.stock 22.,Validado  
REQ-09,Transición de Estados y Reposición de Stock,TPA.pdf (Secc. 5.3) 22   Clase 9 19,Lógica de Negocio,Obligatorio,Vistas de actualización de estado para Empleados/Admins con restitución automática de stock si cambia a 'Cancelado' 22.,Transición de pedido a 'Cancelado' comprobando en la BD que las unidades se reincorporan a Producto.stock 22.,Validado  
REQ-10,Optimización ORM (Prevención N+1),TPA.pdf (Criterios) 4   Clase 9 24-27,Técnico,Obligatorio,"Uso obligatorio de select\_related() (relaciones ForeignKey) y prefetch\_related() (relaciones inversas/M2M) 4, 26, 27.",Conteo de consultas SQL ejecutadas en el renderizado de listas mediante Django Debug Toolbar o logs de SQL 24-27.,Validado  
REQ-11,Configuración Personalizada del Admin,TPA.pdf (Secc. 5.4) 28   Clase 10 13,Funcional / Técnico,Obligatorio,"Implementación de search\_fields, list\_filter, list\_editable e inlines para DetallePedido dentro de Pedido 28.",Acceso a /admin/ comprobando la edición rápida de stock y la gestión alineada de los detalles del pedido 28.,Validado  
REQ-12,Variables de Entorno y Seguridad Nativa,"TPA.pdf (Criterios) 4   Clase 6/11 1, 29",Seguridad,Obligatorio,"Aislamiento de SECRET\_KEY y BD en .env (vía python-dotenv), tokens {% csrf\_token %} en formularios POST 1, 4, 29.","Inspección del código en repositorio (ausencia de claves explícitas) y verificación de rechazo POST sin CSRF 1, 4.",Validado  
REQ-13,Formularios Estilizados y CBVs,"TPA.pdf (Secc. 2, 5.1) 10, 30   Clase 7/11 18, 31",Presentación,Obligatorio,"Uso de ListView, DetailView, CreateView, UpdateView e inyección de clases Bootstrap (form-control) 18, 30, 31.","Inspección visual de la UI responsive y revisión de vistas en el IDE adhiriendo a herencia de clases 18, 31.",Validado  
REQ-14,Opción de Django REST Framework (DRF),TPA.pdf (Criterios) 4,Arquitectura,Complementario,Posibilidad de exponer serializadores y vistas API en lugar de plantillas DTL monolíticas 4.,Exposición de endpoints JSON y prueba de serializadores.,Requiere Confirmación  
REQ-15,Exención de Práctica Profesionalizante,TPA.pdf (Pág. 1\) 3   audio\_02 32,Normativa,Excepción,"Presentación y defensa del proyecto desarrollado en Práctica Profesionalizante en lugar de InvenShop 3, 32.","Acreditación previa del proyecto en la materia correspondiente antes de la fecha de entrega 3, 32.",Pendiente  
REQ-16,Evaluación e Exposición Oral (Parcial 2),"Guía Defensa 2, 33   audio\_02 32, 33",Evaluación,Obligatorio,"Defensa oral de 15 a 30 min en 5 bloques. Nota individual equivalente a la calificación del Examen Parcial 2 2, 32, 33.","Exposición técnica sin lectura de código y demostración funcional con datos de prueba realistas 32, 34, 35.",Pendiente

## 2\. Auditoría Crítica de la Planificación Previa

Al revisar la planificación previa contra las fuentes originales, se identifican las siguientes inconsistencias y omisiones que deben ser corregidas antes de iniciar la programación:

### A. Errores Encontrados

* **Superficialidad en la Configuración del Panel de Administración (admin.py)**:  
* *Diagnóstico*: En el borrador de planificación se asumió la registración por defecto de los modelos en el Admin (admin.site.register).  
* *Impacto Académico*: La **Sección 5.4 del TPA** exige explícitamente una personalización avanzada mediante clases ModelAdmin 28:  
* Búsqueda con search\_fields (por nombre de producto, email de usuario y número de pedido) 28\.  
* Filtros laterales con list\_filter (categoría, estado de pedido, activo, fechas) 28\.  
* Edición directa en tabla mediante list\_editable para los campos stock y activo 28\.  
* Edición en línea mediante inlines (TabularInline o StackedInline) de DetallePedido dentro de la vista de Pedido 28\.  
* **Ausencia de Transaccionalidad Atómica Explícita en el Checkout**:  
* *Diagnóstico*: El plan anterior mencionaba la creación de Pedido y DetallePedido, pero no enfatizaba la obligatoriedad del bloque atómico a nivel de ORM.  
* *Impacto Técnico*: Si la actualización de stock o la inserción de un ítem falla a mitad de proceso, la base de datos quedaría en un estado inconsistente (pedido registrado sin stock descontado o viceversa). Debe aplicarse imperativamente with transaction.atomic(): en la vista de checkout.

### B. Omisiones Detectadas

* **Validación Personalizada de Contraseñas y Formulario de Registro**:  
* *Fuente*: TPA.pdf (Sección 5.1) 10 y Clase 11 23\.  
* *Omisión*: No se detalló la inclusión explícita de las políticas de fortaleza de contraseñas de Django (AUTH\_PASSWORD\_VALIDATORS en settings.py) dentro del formulario CustomUserCreationForm, ni la validación de coincidencia entre password1 y password2 10\.  
* **Redirección Pos-Login Orientada a Roles**:  
* *Fuente*: TPA.pdf (Sección 5.1) 10\.  
* *Omisión*: El flujo de autenticación no debe redirigir a todos los usuarios a la misma página. Si el usuario autenticado tiene el rol 'Cliente', debe ser derivado a la raíz del catálogo público; si tiene rol 'Empleado' o 'Admin', debe ser redirigido directamente al panel de gestión de inventario y pedidos 10\.  
* **Validación de Datos de Envío en Checkout**:  
* *Fuente*: TPA.pdf (Sección 5.3) 22 y Clase 11 23\.  
* *Omisión*: Falta especificar la validación del formato del teléfono de contacto en CheckoutForm utilizando el método del formulario clean\_telefono\_contacto() 22, 23\.

### C. Correcciones Necesarias en la Arquitectura Planteada

1. **Alineación Completa de admin.py en la App catalogo y pedidos**:  
2. \# catalogo/admin.py  
3. @admin.register(Producto)  
4. class ProductoAdmin(admin.ModelAdmin):  
5.     list\_display \= ('nombre', 'precio', 'stock', 'categoria', 'activo')  
6.     list\_editable \= ('stock', 'activo')  
7.     list\_filter \= ('categoria', 'activo')  
8.     search\_fields \= ('nombre', 'descripcion')  
9.   
10. \# pedidos/admin.py  
11. class DetallePedidoInline(admin.TabularInline):  
12.     model \= DetallePedido  
13.     extra \= 0  
14.     readonly\_fields \= ('producto', 'cantidad', 'precio\_unitario')  
15.   
16. @admin.register(Pedido)  
17. class PedidoAdmin(admin.ModelAdmin):  
18.     list\_display \= ('id', 'usuario', 'fecha\_creacion', 'estado', 'total')  
19.     list\_filter \= ('estado', 'fecha\_creacion')  
20.     search\_fields \= ('usuario\_\_email', 'id')  
21.     inlines \= \[DetallePedidoInline\]  
22. **Enrutamiento y Control de Acceso Estricto en Vistas por Roles**:  
23. Asegurar que ProductoCreateView, ProductoUpdateView y PedidoEstadoUpdateView utilicen PermissionRequiredMixin con sus permisos específicos (catalogo.add\_producto, catalogo.change\_producto, pedidos.change\_pedido) 10, 17\.

## 3\. Dudas TÉCNICAS a Consultar al Docente

Antes de iniciar la codificación del proyecto, se deben enviar las siguientes tres consultas puntuales a la cátedra:

* **Incompatibilidad entre Rúbrica y Requisitos de Interfaz (DTL vs. DRF)**:  
* *Pregunta*: "En la rúbrica de evaluación se menciona la opción de usar Django REST Framework (DRF) con serializadores 4, mientras que el desarrollo funcional detalla plantillas DTL con herencia (base.html) y Bootstrap 6, 14\. ¿Es 100% aceptable presentar el proyecto como una aplicación monolítica tradicional MVT con plantillas HTML sin implementar endpoints REST en DRF?"  
* **Modalidad de Reposición de Stock en Cancelación de Pedidos**:  
* *Pregunta*: "El enunciado indica que al cancelar un pedido 'se recomienda reponer el stock descontado' 22\. ¿Prefieren que esta restitución de stock sea ejecutada automáticamente por el backend al cambiar el estado a 'Cancelado', o debe requerir un botón de confirmación manual por parte del empleado?"  
* **Presentación de Proyectos de Práctica Profesionalizante**:  
* *Pregunta*: "Para los grupos que hayan realizado un desarrollo web en Django en Práctica Profesionalizante 3, 32: ¿Se exige que el proyecto cumpla exactamente con la estructura de 3 apps (usuarios, catalogo, pedidos) de InvenShop, o se evalúa la arquitectura propia con la que fue aprobado en dicha asignatura 3, 32?"

## 4\. Lista Definitiva de Verificación Previa al Desarrollo (Checklist de Control)

Utiliza este checklist técnico como puerta de enlace final antes de escribir la primera línea de código:

### 🛠️ Entorno y Configuración Base

*  Entorno virtual aislado creado (env) y dependencias registradas en requirements.txt (Django, python-dotenv, Pillow) 36, 37\.  
*  Archivos .env y .env.example configurados sin credenciales ni SECRET\_KEY expuestas en el repositorio 4\.  
*  Archivo .gitignore verificado para excluir env/, .env, db.sqlite3 y la carpeta media/ 38\.

### 👤 Autenticación y Modelos de Usuario

*  Modelo Usuario heredando de AbstractUser con email como identificador único (USERNAME\_FIELD \= 'email') 7, 11, 12\.  
*  Ajuste de AUTH\_USER\_MODEL \= 'usuarios.Usuario' en settings.py realizado **antes de la primera migración** 39\.  
*  Definición de roles (Admin, Empleado, Cliente) en el modelo de usuario 7\.

### 📦 Catálogo e Inventario

*  Modelos Categoria y Producto creados con clave foránea ForeignKey(Categoria, on\_delete=models.PROTECT) 7, 20\.  
*  Búsqueda por palabras clave implementada mediante objetos Q (Q(nombre\_\_icontains=q) \| Q(descripcion\_\_icontains=q)) 14, 19\.  
*  Optimización ORM de la consulta de catálogo aplicando imperativamente .select\_related('categoria') 14, 26\.

### 🛒 Carrito, Pedidos y Transacciones

*  Carrito programado exclusivamente sobre request.session\['carrito'\] sin persistencia previa en base de datos 11, 14\.  
*  Validación estricta de disponibilidad de stock antes de agregar o modificar ítems en el carrito 14\.  
*  Checkout encapsulado en with transaction.atomic(): para garantizar el registro de orden y descuento de stock como una operación indivisible 22\.  
*  Lógica de restitución de unidades al inventario implementada para pedidos que pasen al estado 'Cancelado' 22\.

### 🔐 Seguridad y Panel Admin

*  Inyección de tokens {% csrf\_token %} en la totalidad de plantillas HTML con formularios POST 1, 4\.  
*  Configuración completa de ModelAdmin en admin.py con search\_fields, list\_filter, list\_editable e inlines para detalles de pedidos 28\.  
*  Protección de vistas según el rol mediante LoginRequiredMixin y PermissionRequiredMixin 10, 17\.  
*  Preparación de un set de datos de prueba realistas (sin registros o usuarios informales tipo *"asdf"* o *"admin123"*) para el día de la defensa oral 34\.

💡 *Con esta auditoría crítica y matriz de trazabilidad, el proyecto cuenta con el respaldo teórico y reglamentario para comenzar la fase de desarrollo sin riesgo de penalización en la evaluación final.*  
