"""Modelos de pedidos: Pedido y DetallePedido."""

from decimal import Decimal

from django.conf import settings
from django.db import models

from catalogo.models import Producto


class Pedido(models.Model):
    """Pedido realizado por un cliente.

    Se almacena una *copia* de los datos de envío y del precio unitario de cada
    producto para conservar el histórico aunque el catálogo cambie.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "Pendiente", "Pendiente"
        PAGADO = "Pagado", "Pagado"
        ENVIADO = "Enviado", "Enviado"
        CANCELADO = "Cancelado", "Cancelado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="cliente",
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        db_index=True,
    )
    total = models.DecimalField("total", max_digits=12, decimal_places=2, default=Decimal("0.00"))

    # Datos de envío (snapshot del checkout)
    direccion = models.CharField("dirección", max_length=200)
    ciudad = models.CharField("ciudad", max_length=100)
    codigo_postal = models.CharField("código postal", max_length=10)
    telefono_contacto = models.CharField("teléfono de contacto", max_length=30)
    notas = models.TextField("notas de envío", blank=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["usuario", "-fecha_creacion"], name="pedido_usuario_fecha_idx"),
            models.Index(fields=["estado"], name="pedido_estado_idx"),
        ]

    def __str__(self):
        return f"Pedido #{self.pk:06d} · {self.usuario.nombre_completo}"

    @property
    def numero(self):
        return f"#{self.pk:06d}"

    @property
    def cantidad_items(self):
        return sum(detalle.cantidad for detalle in self.detalles.all())

    @property
    def puede_cancelarse(self):
        return self.estado in {self.Estado.PENDIENTE, self.Estado.PAGADO}

    @property
    def esta_finalizado(self):
        return self.estado in {self.Estado.ENVIADO, self.Estado.CANCELADO}

    def calcular_total(self):
        total = sum((d.subtotal for d in self.detalles.all()), Decimal("0.00"))
        self.total = total
        return total


class DetallePedido(models.Model):
    """Línea de un pedido: producto, cantidad y precio al momento de la compra."""

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="pedido",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_pedido",
        verbose_name="producto",
    )
    cantidad = models.PositiveIntegerField("cantidad")
    precio_unitario = models.DecimalField("precio unitario", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "detalle de pedido"
        verbose_name_plural = "detalles de pedido"
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(fields=["pedido", "producto"], name="detalle_unico_por_pedido"),
        ]

    def __str__(self):
        return f"{self.cantidad} × {self.producto.nombre}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad
