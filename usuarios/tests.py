"""Pruebas de la app usuarios: registro, login por email y roles."""

from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class RegistroTests(TestCase):
    def test_registro_publico_crea_cliente_y_autentica(self):
        respuesta = self.client.post(
            reverse("usuarios:registro"),
            {
                "nombre": "Marta",
                "apellido": "Sosa",
                "email": "marta@example.com",
                "telefono": "3415550000",
                "password1": "ClaveSegura123!",
                "password2": "ClaveSegura123!",
            },
        )

        self.assertRedirects(respuesta, reverse("catalogo:producto_list"))
        usuario = Usuario.objects.get(email="marta@example.com")
        self.assertEqual(usuario.rol, Usuario.Rol.CLIENTE)
        self.assertTrue(usuario.check_password("ClaveSegura123!"))
        self.assertFalse(usuario.is_staff)
        self.assertEqual(int(self.client.session["_auth_user_id"]), usuario.pk)

    def test_registro_rechaza_email_duplicado(self):
        Usuario.objects.create_user(
            email="repetido@example.com",
            password="ClaveSegura123!",
            nombre="Ana",
            apellido="Paz",
        )

        respuesta = self.client.post(
            reverse("usuarios:registro"),
            {
                "nombre": "Otra",
                "apellido": "Persona",
                "email": "REPETIDO@example.com",
                "telefono": "3415550001",
                "password1": "ClaveSegura123!",
                "password2": "ClaveSegura123!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ya existe una cuenta")
        self.assertEqual(Usuario.objects.filter(email__iexact="repetido@example.com").count(), 1)

    def test_registro_rechaza_contrasenas_distintas(self):
        respuesta = self.client.post(
            reverse("usuarios:registro"),
            {
                "nombre": "Marta",
                "apellido": "Sosa",
                "email": "marta2@example.com",
                "telefono": "3415550000",
                "password1": "ClaveSegura123!",
                "password2": "OtraClave123!",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Las contraseñas no coinciden")
        self.assertFalse(Usuario.objects.filter(email="marta2@example.com").exists())


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        cls.admin = Usuario.objects.create_user(
            email="admin@example.com",
            password="ClaveSegura123!",
            nombre="Ana",
            apellido="Gómez",
            rol=Usuario.Rol.ADMIN,
        )

    def test_login_cliente_redirige_al_catalogo(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"email": "cliente@example.com", "password": "ClaveSegura123!"},
            follow=True,
        )
        self.assertRedirects(respuesta, reverse("catalogo:producto_list"))
        self.assertTrue(respuesta.context["user"].is_authenticated)

    def test_login_empleado_redirige_al_panel(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"email": "empleado@example.com", "password": "ClaveSegura123!"},
        )
        self.assertRedirects(respuesta, reverse("panel:dashboard"))

    def test_login_admin_redirige_al_panel(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"email": "admin@example.com", "password": "ClaveSegura123!"},
        )
        self.assertRedirects(respuesta, reverse("panel:dashboard"))

    def test_login_acepta_email_con_mayusculas(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"email": "CLIENTE@EXAMPLE.COM", "password": "ClaveSegura123!"},
        )
        self.assertRedirects(respuesta, reverse("catalogo:producto_list"))

    def test_login_invalido_muestra_error(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"email": "cliente@example.com", "password": "incorrecta"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no son correctos")

    def test_cuenta_inactiva_no_puede_ingresar(self):
        self.cliente.is_active = False
        self.cliente.save()

        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"email": "cliente@example.com", "password": "ClaveSegura123!"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "deshabilitada")

    def test_rol_staff_mantiene_is_staff(self):
        self.assertTrue(self.empleado.is_staff)
        self.assertTrue(self.admin.is_staff)
        self.assertFalse(self.cliente.is_staff)


class PerfilYPermisosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Usuario.objects.create_user(
            email="cliente@example.com",
            password="ClaveSegura123!",
            nombre="Carla",
            apellido="Ríos",
            telefono="3415550000",
        )
        cls.otro = Usuario.objects.create_user(
            email="otro@example.com",
            password="ClaveSegura123!",
            nombre="Otro",
            apellido="Cliente",
        )
        cls.admin = Usuario.objects.create_user(
            email="admin@example.com",
            password="ClaveSegura123!",
            nombre="Ana",
            apellido="Gómez",
            rol=Usuario.Rol.ADMIN,
        )

    def test_perfil_requiere_login(self):
        respuesta = self.client.get(reverse("usuarios:perfil"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_cliente_edita_su_propio_perfil(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(
            reverse("usuarios:perfil"),
            {"nombre": "Carla", "apellido": "Ríos", "telefono": "3415559999"},
        )
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.telefono, "3415559999")

    def test_cliente_no_puede_gestionar_usuarios(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("usuarios:usuario_list"))
        self.assertEqual(respuesta.status_code, 403)

    def test_empleado_no_puede_gestionar_usuarios(self):
        empleado = Usuario.objects.create_user(
            email="empleado@example.com",
            password="ClaveSegura123!",
            nombre="Bruno",
            apellido="Fernández",
            rol=Usuario.Rol.EMPLEADO,
        )
        self.client.force_login(empleado)
        respuesta = self.client.get(reverse("usuarios:usuario_list"))
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_puede_cambiar_rol_de_un_cliente(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("usuarios:usuario_update", args=[self.otro.pk]),
            {
                "nombre": "Otro",
                "apellido": "Cliente",
                "email": "otro@example.com",
                "telefono": "3415550002",
                "rol": Usuario.Rol.EMPLEADO,
                "is_active": "on",
            },
        )
        self.assertRedirects(respuesta, reverse("usuarios:usuario_list"))
        self.otro.refresh_from_db()
        self.assertEqual(self.otro.rol, Usuario.Rol.EMPLEADO)
        self.assertTrue(self.otro.is_staff)

    def test_admin_no_puede_quitarse_su_propio_rol(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            reverse("usuarios:usuario_update", args=[self.admin.pk]),
            {
                "nombre": "Ana",
                "apellido": "Gómez",
                "email": "admin@example.com",
                "telefono": "3415550003",
                "rol": Usuario.Rol.CLIENTE,
                "is_active": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "No podés quitarte")
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.rol, Usuario.Rol.ADMIN)

    def test_listado_de_usuarios_busca_por_nombre(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("usuarios:usuario_list"), {"q": "Carla"})
        self.assertContains(respuesta, "Carla")
        self.assertNotContains(respuesta, "Otro Cliente")
