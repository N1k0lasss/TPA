"""Modelo de usuario personalizado de InvenShop.

Se define antes de la primera migración para evitar problemas posteriores.
El login se realiza con el correo electrónico (no existe `username`).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UsuarioManager


class Usuario(AbstractUser):
    """Usuario del sistema con roles Administrador, Empleado y Cliente."""

    class Rol(models.TextChoices):
        ADMIN = "Admin", "Administrador"
        EMPLEADO = "Empleado", "Empleado"
        CLIENTE = "Cliente", "Cliente"

    username = None
    email = models.EmailField("correo electrónico", unique=True)
    nombre = models.CharField("nombre", max_length=100)
    apellido = models.CharField("apellido", max_length=100)
    rol = models.CharField(
        "rol",
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
        db_index=True,
    )
    telefono = models.CharField("teléfono", max_length=30, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["apellido", "nombre"]
        permissions = [
            ("gestionar_tienda", "Puede gestionar catálogo y pedidos"),
            ("gestionar_usuarios", "Puede gestionar usuarios y roles"),
        ]

    def __str__(self):
        return f"{self.nombre_completo} ({self.email})"

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        # Mantiene is_staff coherente con el rol para poder usar Django Admin.
        self.is_staff = bool(self.is_superuser or self.rol in {self.Rol.ADMIN, self.Rol.EMPLEADO})
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.nombre_completo

    def get_short_name(self):
        return self.nombre

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}".strip()

    @property
    def iniciales(self):
        return f"{self.nombre[:1]}{self.apellido[:1]}".upper()

    @property
    def es_admin(self):
        return self.is_superuser or self.rol == self.Rol.ADMIN

    @property
    def es_gestor(self):
        """Empleados y administradores pueden gestionar catálogo y pedidos."""
        return self.is_superuser or self.rol in {self.Rol.ADMIN, self.Rol.EMPLEADO}

    @property
    def es_cliente(self):
        return self.rol == self.Rol.CLIENTE and not self.es_gestor
