"""Modelos del catálogo: categorías y productos."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Categoria(models.Model):
    """Agrupa productos del catálogo."""

    nombre = models.CharField("nombre", max_length=100, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    slug = models.SlugField("slug", max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._slug_unico(slugify(self.nombre))
        super().save(*args, **kwargs)

    def _slug_unico(self, base):
        slug = base or "categoria"
        numero = 2
        while Categoria.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{numero}"
            numero += 1
        return slug

    def get_absolute_url(self):
        return f"{reverse('catalogo:producto_list')}?categoria={self.slug}"


class Producto(models.Model):
    """Producto publicado en la tienda y controlado en inventario."""

    UMBRAL_STOCK_BAJO = 5

    nombre = models.CharField("nombre", max_length=150)
    descripcion = models.TextField("descripción")
    precio = models.DecimalField(
        "precio",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    stock = models.PositiveIntegerField("stock", default=0)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="categoría",
    )
    imagen = models.ImageField("imagen", upload_to="productos/%Y/%m/", blank=True)
    activo = models.BooleanField("activo", default=True)
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["activo", "categoria"], name="producto_activo_categoria_idx"),
            models.Index(fields=["nombre"], name="producto_nombre_idx"),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse("catalogo:producto_detail", args=[self.pk])

    @property
    def disponible(self):
        return self.activo and self.stock > 0

    @property
    def stock_bajo(self):
        return 0 < self.stock <= self.UMBRAL_STOCK_BAJO

    @property
    def etiqueta_stock(self):
        if self.stock == 0:
            return "Agotado"
        if self.stock_bajo:
            return f"¡Últimas {self.stock} unidades!"
        return "Disponible"
