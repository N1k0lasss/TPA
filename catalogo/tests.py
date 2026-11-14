"""Pruebas del catálogo: filtros, paginación, permisos y borrado protegido."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from pedidos.models import DetallePedido, Pedido
from usuarios.models import Usuario

from .models import Categoria, Producto


class CatalogoPublicoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nombre="Tecnología")
        cls.otra_categoria = Categoria.objects.create(nombre="Hogar")
        cls.producto = Producto.objects.create(
            nombre="Auriculares Bluetooth",
            descripcion="Cancelación de ruido y estuche de carga",
            precio=Decimal("89999.00"),
            stock=5,
            categoria=cls.categoria,
        )
        cls.producto_inactivo = Producto.objects.create(
            nombre="Producto oculto",
            descripcion="No debe verse en la tienda",
            precio=Decimal("1000.00"),
            stock=3,
            categoria=cls.categoria,
            activo=False,
        )
        Producto.objects.create(
            nombre="Lámpara LED",
            descripcion="Luz cálida regulable",
            precio=Decimal("25000.00"),
            stock=0,
            categoria=cls.otra_categoria,
        )

    def test_catalogo_muestra_solo_productos_activos(self):
        respuesta = self.client.get(reverse("catalogo:producto_list"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Auriculares Bluetooth")
        self.assertContains(respuesta, "Lámpara LED")
        self.assertNotContains(respuesta, "Producto oculto")

    def test_busqueda_por_nombre_y_descripcion(self):
        respuesta = self.client.get(reverse("catalogo:producto_list"), {"q": "ruido"})
        self.assertContains(respuesta, "Auriculares Bluetooth")
        self.assertNotContains(respuesta, "Lámpara LED")

    def test_filtro_por_categoria(self):
        respuesta = self.client.get(
            reverse("catalogo:producto_list"),
            {"categoria": self.otra_categoria.slug},
        )
        self.assertContains(respuesta, "Lámpara LED")
        self.assertNotContains(respuesta, "Auriculares Bluetooth")

    def test_orden_por_precio(self):
        respuesta = self.client.get(reverse("catalogo:producto_list"), {"orden": "precio"})
        nombres = [producto.nombre for producto in respuesta.context["productos"]]
        self.assertEqual(nombres[0], "Lámpara LED")
        self.assertEqual(nombres[-1], "Auriculares Bluetooth")

    def test_paginacion_de_12_productos(self):
        for numero in range(15):
            Producto.objects.create(
                nombre=f"Producto extra {numero:02d}",
                descripcion="Relleno para paginación",
                precio=Decimal("1000.00"),
                stock=1,
                categoria=self.categoria,
            )

        respuesta = self.client.get(reverse("catalogo:producto_list"))
        self.assertTrue(respuesta.context["is_paginated"])
        self.assertEqual(len(respuesta.context["productos"]), 12)
        self.assertEqual(respuesta.context["paginator"].count, 17)

    def test_detalle_de_producto_inactivo_devuelve_404(self):
        respuesta = self.client.get(
            reverse("catalogo:producto_detail", args=[self.producto_inactivo.pk])
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_detalle_muestra_precio_y_estado_de_stock(self):
        respuesta = self.client.get(
            reverse("catalogo:producto_detail", args=[self.producto.pk])
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "$ 89.999,00")
        self.assertContains(respuesta, "en stock")


class GestionCatalogoPermisosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nombre="Tecnología")
        cls.producto = Producto.objects.create(
            nombre="Mouse inalámbrico",
            descripcion="Sensor de precisión",
            precio=Decimal("35000.00"),
            stock=10,
            categoria=cls.categoria,
        )
        cls.empleado = Usuario.objects.create_user(
            email="empleado@example.com",
            password="ClaveSegura123!",
            nombre="Bruno",
            apellido="Fernández",
            rol=Usuario.Rol.EMPLEADO,
        )
        cls.cliente = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
        )
        cls.admin = Usuario.objects.create_user(
            email="admin@example.com",
            password="ClaveSegura123!",
            nombre="Ana",
            apellido="Gómez",
            rol=Usuario.Rol.ADMIN,
        )

    def test_cliente_no_accede_a_gestion_de_productos(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("catalogo:gestion_productos"))
        self.assertEqual(respuesta.status_code, 403)

    def test_empleado_crea_producto(self):
        self.client.force_login(self.empleado)
        respuesta = self.client.post(
            reverse("catalogo:producto_create"),
            {
                "nombre": "Teclado mecánico",
                "descripcion": "Switches táctiles",
                "categoria": self.categoria.pk,
                "precio": "72000.00",
                "stock": "8",
                "activo": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("catalogo:gestion_productos"))
        self.assertTrue(Producto.objects.filter(nombre="Teclado mecánico").exists())

    def test_formulario_rechaza_precio_cero(self):
        self.client.force_login(self.empleado)
        respuesta = self.client.post(
            reverse("catalogo:producto_create"),
            {
                "nombre": "Producto inválido",
                "descripcion": "Precio en cero",
                "categoria": self.categoria.pk,
                "precio": "0",
                "stock": "3",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "El precio debe ser mayor a cero")
        self.assertFalse(Producto.objects.filter(nombre="Producto inválido").exists())

    def test_no_se_elimina_producto_con_pedidos(self):
        cliente = Usuario.objects.create_user(
            email="comprador@example.com",
            password="ClaveSegura123!",
            nombre="Juan",
            apellido="Pérez",
        )
        pedido = Pedido.objects.create(
            usuario=cliente,
            direccion="Calle 123",
            ciudad="Rosario",
            codigo_postal="2000",
            telefono_contacto="3415550000",
            total=Decimal("35000.00"),
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=self.producto.precio,
        )

        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("catalogo:producto_delete", args=[self.producto.pk]),
            follow=True,
        )
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())
        self.assertContains(respuesta, "figura en pedidos registrados")

    def test_no_se_elimina_categoria_con_productos(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("catalogo:categoria_delete", args=[self.categoria.pk]),
            follow=True,
        )
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertContains(respuesta, "tiene productos asociados")

    def test_empleado_puede_actualizar_stock(self):
        self.client.force_login(self.empleado)
        respuesta = self.client.post(
            reverse("catalogo:producto_update", args=[self.producto.pk]),
            {
                "nombre": self.producto.nombre,
                "descripcion": self.producto.descripcion,
                "categoria": self.categoria.pk,
                "precio": "35000.00",
                "stock": "31",
                "activo": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("catalogo:gestion_productos"))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 31)
