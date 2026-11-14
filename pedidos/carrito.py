"""Carrito de compras almacenado en la sesión de Django.

No se guarda nada en la base de datos hasta que el cliente confirma el pedido.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError

from catalogo.models import Producto

CLAVE_SESION = "carrito"


class Carrito:
    """Operaciones sobre el carrito guardado en `request.session`."""

    def __init__(self, request):
        self.session = request.session
        datos = self.session.get(CLAVE_SESION)
        if not isinstance(datos, dict):
            datos = {}
            self.session[CLAVE_SESION] = datos
        self.carrito = datos

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------
    def agregar(self, producto, cantidad=1, reemplazar=False):
        if cantidad < 1:
            raise ValidationError("La cantidad debe ser un número entero mayor a cero.")
        if not producto.activo:
            raise ValidationError("Este producto ya no está disponible.")

        clave = str(producto.pk)
        cantidad_actual = int(self.carrito.get(clave, {}).get("cantidad", 0))
        nueva_cantidad = cantidad if reemplazar else cantidad_actual + cantidad

        if nueva_cantidad > producto.stock:
            if producto.stock == 0:
                raise ValidationError(f'"{producto.nombre}" está agotado.')
            raise ValidationError(
                f'No hay stock suficiente de "{producto.nombre}". '
                f"Disponible: {producto.stock} unidad(es)."
            )

        self.carrito[clave] = {"cantidad": nueva_cantidad}
        self.guardar()

    def actualizar(self, producto, cantidad):
        if cantidad < 1:
            raise ValidationError("La cantidad mínima es 1. Para quitar el producto usá el botón de eliminar.")
        if cantidad > producto.stock:
            raise ValidationError(f'Solo hay {producto.stock} unidad(es) de "{producto.nombre}".')
        self.agregar(producto, cantidad=cantidad, reemplazar=True)

    def quitar(self, producto_id):
        if str(producto_id) in self.carrito:
            del self.carrito[str(producto_id)]
            self.guardar()

    def vaciar(self):
        self.session[CLAVE_SESION] = {}
        self.carrito = self.session[CLAVE_SESION]
        self.session.modified = True

    def guardar(self):
        self.session.modified = True

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def __len__(self):
        return len(self.carrito)

    def __iter__(self):
        """Devuelve ítems con el producto actualizado desde la base de datos."""
        ids = [int(clave) for clave in self.carrito.keys() if str(clave).isdigit()]
        productos = Producto.objects.filter(pk__in=ids, activo=True).select_related("categoria")
        encontrados = {producto.pk: producto for producto in productos}

        # Limpia entradas de productos eliminados o despublicados.
        ids_invalidos = [str(pid) for pid in ids if pid not in encontrados]
        if ids_invalidos:
            for pid in ids_invalidos:
                self.carrito.pop(pid, None)
            self.guardar()

        for clave, item in list(self.carrito.items()):
            producto = encontrados.get(int(clave)) if str(clave).isdigit() else None
            if not producto:
                continue
            cantidad = int(item.get("cantidad", 0))
            if cantidad < 1:
                continue
            yield {
                "producto": producto,
                "cantidad": cantidad,
                "precio": producto.precio,
                "subtotal": producto.precio * cantidad,
                "stock_insuficiente": cantidad > producto.stock,
            }

    @property
    def vacio(self):
        return not self.carrito

    @property
    def cantidad_total(self):
        return sum(int(item.get("cantidad", 0)) for item in self.carrito.values())

    @property
    def total(self):
        return sum((item["subtotal"] for item in self), start=Decimal("0.00"))

    @property
    def hay_problemas_de_stock(self):
        return any(item["stock_insuficiente"] for item in self)
