"""Pruebas del carrito, checkout, seguridad de pedidos y cambios de estado."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Producto
from usuarios.models import Usuario

from .models import DetallePedido, Pedido
from .services import cambiar_estado


def crear_producto(nombre="Producto de prueba", precio="10000.00", stock=10, activo=True):
    categoria, _ = Categoria.objects.get_or_create(nombre="Pruebas")
    return Producto.objects.create(
        nombre=nombre,
        descripcion="Producto generado para pruebas automatizadas.",
        precio=Decimal(precio),
        stock=stock,
        categoria=categoria,
        activo=activo,
    )


def crear_pedido(usuario, producto, cantidad=1, estado=Pedido.Estado.PENDIENTE):
    pedido = Pedido.objects.create(
        usuario=usuario,
        estado=estado,
        total=producto.precio * cantidad,
        direccion="Av. Siempre Viva 742",
        ciudad="Rosario",
        codigo_postal="2000",
        telefono_contacto="341 555-0000",
    )
    DetallePedido.objects.create(
        pedido=pedido,
        producto=producto,
        cantidad=cantidad,
        precio_unitario=producto.precio,
    )
    return pedido


class CarritoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.producto = crear_producto(stock=5)
        cls.agotado = crear_producto(nombre="Agotado", stock=0)

    def _agregar(self, producto, cantidad):
        return self.client.post(
            reverse("carrito:agregar", args=[producto.pk]),
            {"cantidad": cantidad, "next": producto.get_absolute_url()},
        )

    def test_agregar_producto_guarda_cantidad_en_la_sesion(self):
        respuesta = self._agregar(self.producto, 2)
        self.assertRedirects(respuesta, self.producto.get_absolute_url())
        self.assertEqual(self.client.session["carrito"][str(self.producto.pk)]["cantidad"], 2)

    def test_no_se_puede_agregar_mas_que_el_stock(self):
        respuesta = self._agregar(self.producto, 99)

        self.assertRedirects(respuesta, self.producto.get_absolute_url())
        self.assertNotIn(str(self.producto.pk), self.client.session.get("carrito", {}))

    def test_no_se_puede_agregar_producto_agotado(self):
        self._agregar(self.agotado, 1)
        self.assertNotIn(str(self.agotado.pk), self.client.session.get("carrito", {}))

    def test_actualizar_cantidad(self):
        self._agregar(self.producto, 1)
        respuesta = self.client.post(
            reverse("carrito:actualizar", args=[self.producto.pk]),
            {"cantidad": 4},
        )
        self.assertRedirects(respuesta, reverse("carrito:detalle"))
        self.assertEqual(self.client.session["carrito"][str(self.producto.pk)]["cantidad"], 4)

    def test_actualizar_por_encima_del_stock_no_modifica(self):
        self._agregar(self.producto, 1)
        respuesta = self.client.post(
            reverse("carrito:actualizar", args=[self.producto.pk]),
            {"cantidad": 50},
            follow=True,
        )
        self.assertContains(respuesta, "Solo hay 5 unidad")
        self.assertEqual(self.client.session["carrito"][str(self.producto.pk)]["cantidad"], 1)

    def test_quitar_y_vaciar(self):
        self._agregar(self.producto, 1)
        self.client.post(reverse("carrito:quitar", args=[self.producto.pk]))
        self.assertEqual(self.client.session["carrito"], {})

        self._agregar(self.producto, 2)
        self.client.post(reverse("carrito:vaciar"))
        self.assertEqual(self.client.session["carrito"], {})

    def test_carrito_muestra_subtotales_y_total(self):
        self._agregar(self.producto, 3)
        respuesta = self.client.get(reverse("carrito:detalle"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["total"], Decimal("30000.00"))
        self.assertContains(respuesta, "$ 30.000,00")

    def test_muestra_advertencia_si_el_stock_cambio(self):
        self._agregar(self.producto, 5)
        Producto.objects.filter(pk=self.producto.pk).update(stock=2)

        respuesta = self.client.get(reverse("carrito:detalle"))
        self.assertTrue(respuesta.context["hay_problemas_de_stock"])
        self.assertContains(respuesta, "Solo quedan 2 unidades")


class CheckoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.producto = crear_producto(stock=10, precio="25000.00")
        cls.cliente = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
            telefono="3415550000",
        )

    def setUp(self):
        self.client.force_login(self.cliente)

    def _preparar_carrito(self, cantidad=2):
        sesion = self.client.session
        sesion["carrito"] = {str(self.producto.pk): {"cantidad": cantidad}}
        sesion.save()

    def _datos_checkout(self, **extra):
        datos = {
            "direccion": "Av. Siempre Viva 742",
            "ciudad": "Rosario",
            "codigo_postal": "2000",
            "telefono_contacto": "341 555-0000",
            "notas": "Timbre 4B",
            "confirmar": "on",
        }
        datos.update(extra)
        return datos

    def test_checkout_requiere_autenticacion(self):
        self.client.logout()
        self._preparar_carrito()
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_checkout_sin_carrito_redirige_al_carrito(self):
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertRedirects(respuesta, reverse("carrito:detalle"))

    def test_checkout_crea_pedido_descuenta_stock_y_vacia_carrito(self):
        self._preparar_carrito(2)
        respuesta = self.client.post(reverse("pedidos:checkout"), self._datos_checkout())

        pedido = Pedido.objects.get(usuario=self.cliente)
        self.assertRedirects(respuesta, reverse("pedidos:confirmacion", args=[pedido.pk]))
        self.assertEqual(pedido.estado, Pedido.Estado.PENDIENTE)
        self.assertEqual(pedido.total, Decimal("50000.00"))
        self.assertEqual(pedido.direccion, "Av. Siempre Viva 742")
        self.assertEqual(pedido.detalles.count(), 1)
        self.assertEqual(pedido.detalles.first().precio_unitario, Decimal("25000.00"))

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)
        self.assertEqual(self.client.session["carrito"], {})

    def test_precio_queda_congelado_en_el_detalle(self):
        self._preparar_carrito(1)
        self.client.post(reverse("pedidos:checkout"), self._datos_checkout())

        self.producto.precio = Decimal("99999.00")
        self.producto.save()

        pedido = Pedido.objects.get(usuario=self.cliente)
        self.assertEqual(pedido.detalles.first().precio_unitario, Decimal("25000.00"))
        self.assertEqual(pedido.total, Decimal("25000.00"))

    def test_stock_insuficiente_no_crea_pedido(self):
        self._preparar_carrito(5)
        Producto.objects.filter(pk=self.producto.pk).update(stock=2)

        respuesta = self.client.post(
            reverse("pedidos:checkout"), self._datos_checkout(), follow=True
        )

        self.assertRedirects(respuesta, reverse("carrito:detalle"))
        self.assertContains(respuesta, "pediste 5 y quedan 2")
        self.assertFalse(Pedido.objects.filter(usuario=self.cliente).exists())
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 2)
        self.assertEqual(self.client.session["carrito"][str(self.producto.pk)]["cantidad"], 5)

    def test_validaciones_de_datos_de_envio(self):
        self._preparar_carrito()
        respuesta = self.client.post(
            reverse("pedidos:checkout"),
            self._datos_checkout(
                direccion="abc",
                codigo_postal="!!",
                telefono_contacto="12",
                confirmar="",
            ),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "dirección completa")
        self.assertContains(respuesta, "código postal")
        self.assertContains(respuesta, "teléfono válido")
        self.assertContains(respuesta, "Tenés que confirmar")
        self.assertFalse(Pedido.objects.filter(usuario=self.cliente).exists())

    def test_confirmacion_no_accesible_por_otro_cliente(self):
        self._preparar_carrito()
        self.client.post(reverse("pedidos:checkout"), self._datos_checkout())
        pedido = Pedido.objects.get(usuario=self.cliente)

        otro = Usuario.objects.create_user(
            email="otro@example.com",
            password="ClaveSegura123!",
            nombre="Otro",
            apellido="Cliente",
        )
        self.client.force_login(otro)
        respuesta = self.client.get(reverse("pedidos:confirmacion", args=[pedido.pk]))
        self.assertEqual(respuesta.status_code, 404)


class SeguridadPedidosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.producto = crear_producto()
        cls.cliente = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
        )
        cls.otro_cliente = Usuario.objects.create_user(
            email="otro@example.com",
            password="ClaveSegura123!",
            nombre="Otro",
            apellido="Cliente",
        )
        cls.empleado = Usuario.objects.create_user(
            email="empleado@example.com",
            password="ClaveSegura123!",
            nombre="Bruno",
            apellido="Fernández",
            rol=Usuario.Rol.EMPLEADO,
        )
        cls.pedido = crear_pedido(cls.cliente, cls.producto, cantidad=2)
        cls.pedido_ajeno = crear_pedido(cls.otro_cliente, cls.producto, cantidad=1)

    def test_cliente_solo_ve_sus_propios_pedidos(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("pedidos:lista"))

        self.assertContains(respuesta, self.pedido.numero)
        self.assertNotContains(respuesta, self.pedido_ajeno.numero)

    def test_cliente_no_puede_ver_pedido_ajeno(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("pedidos:detalle", args=[self.pedido_ajeno.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_empleado_ve_todos_los_pedidos(self):
        self.client.force_login(self.empleado)
        respuesta = self.client.get(reverse("pedidos:lista"))

        self.assertContains(respuesta, self.pedido.numero)
        self.assertContains(respuesta, self.pedido_ajeno.numero)

    def test_busqueda_por_numero_visible_con_almohadilla(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("pedidos:lista"), {"q": self.pedido.numero})

        encontrados = [pedido.pk for pedido in respuesta.context["pedidos"]]
        self.assertEqual(encontrados, [self.pedido.pk])

    def test_gestor_busca_pedido_por_numero_visible(self):
        self.client.force_login(self.empleado)
        respuesta = self.client.get(reverse("pedidos:lista"), {"q": self.pedido.numero})

        encontrados = [pedido.pk for pedido in respuesta.context["pedidos"]]
        self.assertEqual(encontrados, [self.pedido.pk])

    def test_filtro_por_estado(self):
        crear_pedido(self.cliente, self.producto, estado=Pedido.Estado.PAGADO)
        self.client.force_login(self.cliente)

        respuesta = self.client.get(reverse("pedidos:lista"), {"estado": Pedido.Estado.PAGADO})
        self.assertEqual(len(respuesta.context["pedidos"]), 1)
        self.assertEqual(respuesta.context["pedidos"][0].estado, Pedido.Estado.PAGADO)

    def test_pedidos_requieren_login(self):
        respuesta = self.client.get(reverse("pedidos:lista"))
        self.assertEqual(respuesta.status_code, 302)

    def test_cliente_no_puede_cambiar_estado(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(
            reverse("pedidos:cambiar_estado", args=[self.pedido.pk]),
            {"estado": Pedido.Estado.PAGADO},
        )
        self.assertEqual(respuesta.status_code, 403)
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, Pedido.Estado.PENDIENTE)


class CambioEstadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.producto = crear_producto(stock=10, precio="15000.00")
        cls.cliente = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
        )
        cls.empleado = Usuario.objects.create_user(
            email="empleado@example.com",
            password="ClaveSegura123!",
            nombre="Bruno",
            apellido="Fernández",
            rol=Usuario.Rol.EMPLEADO,
        )

    def test_empleado_cambia_pendiente_a_pagado(self):
        pedido = crear_pedido(self.cliente, self.producto)
        self.client.force_login(self.empleado)

        respuesta = self.client.post(
            reverse("pedidos:cambiar_estado", args=[pedido.pk]),
            {"estado": Pedido.Estado.PAGADO},
        )

        self.assertRedirects(respuesta, reverse("pedidos:detalle", args=[pedido.pk]))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.PAGADO)

    def test_no_se_puede_saltar_de_pendiente_a_enviado(self):
        pedido = crear_pedido(self.cliente, self.producto)
        self.client.force_login(self.empleado)

        respuesta = self.client.post(
            reverse("pedidos:cambiar_estado", args=[pedido.pk]),
            {"estado": Pedido.Estado.ENVIADO},
        )

        self.assertEqual(respuesta.status_code, 200)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.PENDIENTE)

    def test_cancelar_repone_stock(self):
        pedido = crear_pedido(self.cliente, self.producto, cantidad=3)
        Producto.objects.filter(pk=self.producto.pk).update(stock=7)

        cambiar_estado(pedido, Pedido.Estado.CANCELADO)

        pedido.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.CANCELADO)
        self.assertEqual(self.producto.stock, 10)

    def test_cancelar_dos_veces_no_duplica_el_stock(self):
        pedido = crear_pedido(self.cliente, self.producto, cantidad=2)
        Producto.objects.filter(pk=self.producto.pk).update(stock=8)

        cambiar_estado(pedido, Pedido.Estado.CANCELADO)
        # Cancelar de nuevo es una operación idempotente: no vuelve a reponer stock.
        cambiar_estado(pedido, Pedido.Estado.CANCELADO)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_pedido_enviado_es_estado_final(self):
        pedido = crear_pedido(self.cliente, self.producto, estado=Pedido.Estado.ENVIADO)
        with self.assertRaises(ValidationError):
            cambiar_estado(pedido, Pedido.Estado.PAGADO)

    def test_pagado_puede_pasar_a_enviado(self):
        pedido = crear_pedido(self.cliente, self.producto, estado=Pedido.Estado.PAGADO)
        cambiar_estado(pedido, Pedido.Estado.ENVIADO)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.Estado.ENVIADO)
