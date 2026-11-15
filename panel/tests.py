"""Pruebas del panel: permisos, métricas, admin y páginas de error."""

from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Producto
from pedidos.models import DetallePedido, Pedido
from usuarios.models import Usuario


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(
            email="admin@example.com",
            password="ClaveSegura123!",
            nombre="Ana",
            apellido="Gómez",
            rol=Usuario.Rol.ADMIN,
        )
        cls.cliente = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
        )
        categoria = Categoria.objects.create(nombre="Pruebas")
        cls.producto = Producto.objects.create(
            nombre="Producto",
            descripcion="Para métricas",
            precio=Decimal("10000.00"),
            stock=5,
            categoria=categoria,
        )
        pedido = Pedido.objects.create(
            usuario=cls.cliente,
            total=Decimal("20000.00"),
            direccion="Calle 123",
            ciudad="Rosario",
            codigo_postal="2000",
            telefono_contacto="3415550000",
        )
        DetallePedido.objects.create(
            pedido=pedido,
            producto=cls.producto,
            cantidad=2,
            precio_unitario=cls.producto.precio,
        )

    def test_dashboard_requiere_login(self):
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_cliente_no_accede_al_panel(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_ve_metricas(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("panel:dashboard"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["ventas_totales"], Decimal("20000.00"))
        self.assertEqual(respuesta.context["pedidos_totales"], 1)
        self.assertEqual(respuesta.context["pedidos_pendientes"], 1)
        self.assertEqual(respuesta.context["valor_inventario"], Decimal("50000.00"))

    def test_pedido_cancelado_no_suma_a_ventas(self):
        Pedido.objects.update(estado=Pedido.Estado.CANCELADO)
        self.client.force_login(self.admin)

        respuesta = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(respuesta.context["ventas_totales"], Decimal("0.00"))
        self.assertEqual(respuesta.context["pedidos_cancelados"], 1)


class AdminSmokeTests(TestCase):
    """Verifica que las pantallas personalizadas del Django Admin rendericen."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_superuser(
            email="super@example.com",
            password="ClaveSegura123!",
            nombre="Súper",
            apellido="Admin",
        )
        consultora = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
            telefono="3415550000",
        )
        cls.categoria = Categoria.objects.create(nombre="Tecnología")
        cls.producto = Producto.objects.create(
            nombre="Mouse",
            descripcion="Inalámbrico",
            precio=Decimal("30000.00"),
            stock=4,
            categoria=cls.categoria,
        )
        cls.pedido = Pedido.objects.create(
            usuario=consultora,
            total=Decimal("30000.00"),
            direccion="Calle 123",
            ciudad="Rosario",
            codigo_postal="2000",
            telefono_contacto="3415550000",
        )
        DetallePedido.objects.create(
            pedido=cls.pedido,
            producto=cls.producto,
            cantidad=1,
            precio_unitario=cls.producto.precio,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_index_del_admin(self):
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_pantallas_de_usuarios(self):
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_add")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("admin:usuarios_usuario_change", args=[self.admin.pk])).status_code,
            200,
        )

    def test_pantallas_de_catalogo(self):
        self.assertEqual(self.client.get(reverse("admin:catalogo_categoria_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:catalogo_categoria_add")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:catalogo_producto_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:catalogo_producto_add")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("admin:catalogo_producto_change", args=[self.producto.pk])).status_code,
            200,
        )

    def test_pantalla_de_pedido_con_inline_historico(self):
        respuesta = self.client.get(reverse("admin:pedidos_pedido_change", args=[self.pedido.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "histórico de solo lectura")

    def test_busqueda_de_pedido_por_numero_visible(self):
        respuesta = self.client.get(
            reverse("admin:pedidos_pedido_changelist"),
            {"q": self.pedido.numero},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["cl"].result_count, 1)

    def test_admin_no_permite_agregar_pedidos_manualmente(self):
        respuesta = self.client.get(reverse("admin:pedidos_pedido_add"))
        self.assertEqual(respuesta.status_code, 403)


class AdminPermisosPorRolTests(TestCase):
    """El backend de roles también controla el acceso al Django Admin."""

    @classmethod
    def setUpTestData(cls):
        cls.empleado = Usuario.objects.create_user(
            email="empleado@example.com",
            password="ClaveSegura123!",
            nombre="Bruno",
            apellido="Fernández",
            rol=Usuario.Rol.EMPLEADO,
        )
        cls.admin = Usuario.objects.create_user(
            email="admin@example.com",
            password="ClaveSegura123!",
            nombre="Ana",
            apellido="Gómez",
            rol=Usuario.Rol.ADMIN,
        )

    def test_empleado_accede_al_admin_de_catalogo_y_pedidos(self):
        self.client.force_login(self.empleado)

        self.assertEqual(
            self.client.get(reverse("admin:catalogo_producto_changelist")).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(reverse("admin:pedidos_pedido_changelist")).status_code,
            200,
        )

    def test_empleado_no_accede_al_admin_de_usuarios(self):
        self.client.force_login(self.empleado)
        respuesta = self.client.get(reverse("admin:usuarios_usuario_changelist"))
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_no_superusuario_accede_al_admin_de_usuarios(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("admin:usuarios_usuario_changelist"))
        self.assertEqual(respuesta.status_code, 200)


class PaginasDeErrorTests(TestCase):
    def test_404_personalizado(self):
        respuesta = self.client.get("/esta-ruta-no-existe/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertTemplateUsed(respuesta, "errores/404.html")


class SeedDemoTests(TestCase):
    def test_comando_es_idempotente_sin_generar_imagenes(self):
        salida = StringIO()
        call_command("seed_demo", "--sin-imagenes", stdout=salida)
        call_command("seed_demo", "--sin-imagenes", stdout=salida)

        self.assertEqual(Categoria.objects.count(), 6)
        self.assertEqual(Producto.objects.count(), 26)
        self.assertEqual(Usuario.objects.filter(email="admin@invenshop.com").count(), 1)
        self.assertEqual(Pedido.objects.count(), 5)
