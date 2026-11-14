"""Reglas de negocio de pedidos: creación, stock y cambios de estado."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from catalogo.models import Producto

from .models import DetallePedido, Pedido

# Transiciones válidas del flujo de estados
TRANSICIONES = {
    Pedido.Estado.PENDIENTE: {Pedido.Estado.PAGADO, Pedido.Estado.CANCELADO},
    Pedido.Estado.PAGADO: {Pedido.Estado.ENVIADO, Pedido.Estado.CANCELADO},
    Pedido.Estado.ENVIADO: set(),
    Pedido.Estado.CANCELADO: set(),
}


def estados_permitidos(estado_actual):
    """Estados a los que puede pasar un pedido."""
    return [estado for estado in Pedido.Estado.values if estado in TRANSICIONES.get(estado_actual, set())]


@transaction.atomic
def crear_pedido(usuario, carrito, datos_envio):
    """Registra el pedido, sus detalles y descuenta stock de forma atómica.

    `datos_envio` debe contener direccion, ciudad, codigo_postal,
    telefono_contacto y (opcionalmente) notas.
    """
    items = list(carrito)
    if not items:
        raise ValidationError("El carrito está vacío.")

    ids = [item["producto"].pk for item in items]
    # select_for_update evita condiciones de carrera al descontar stock.
    productos = {
        producto.pk: producto
        for producto in Producto.objects.select_for_update().filter(pk__in=ids, activo=True)
    }

    problemas = []
    for item in items:
        producto = productos.get(item["producto"].pk)
        if not producto:
            problemas.append(f'"{item["producto"].nombre}" ya no está disponible.')
        elif item["cantidad"] > producto.stock:
            problemas.append(
                f'"{producto.nombre}": pediste {item["cantidad"]} y quedan {producto.stock}.'
            )
    if problemas:
        raise ValidationError(problemas)

    pedido = Pedido.objects.create(
        usuario=usuario,
        total=Decimal("0.00"),
        direccion=datos_envio["direccion"],
        ciudad=datos_envio["ciudad"],
        codigo_postal=datos_envio["codigo_postal"],
        telefono_contacto=datos_envio["telefono_contacto"],
        notas=datos_envio.get("notas", ""),
    )

    total = Decimal("0.00")
    for item in items:
        producto = productos[item["producto"].pk]
        cantidad = item["cantidad"]
        DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio,
        )
        Producto.objects.filter(pk=producto.pk).update(stock=F("stock") - cantidad)
        total += producto.precio * cantidad

    pedido.total = total
    pedido.save(update_fields=["total"])
    carrito.vaciar()
    return pedido


@transaction.atomic
def cambiar_estado(pedido, nuevo_estado):
    """Valida la transición, actualiza el pedido y repone stock si se cancela."""
    if nuevo_estado not in Pedido.Estado.values:
        raise ValidationError("Estado de pedido inválido.")

    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)

    if nuevo_estado == pedido.estado:
        return pedido

    if nuevo_estado not in TRANSICIONES.get(pedido.estado, set()):
        raise ValidationError(
            f"No se puede pasar de «{pedido.estado}» a «{nuevo_estado}»."
        )

    if nuevo_estado == Pedido.Estado.CANCELADO:
        # Al cancelar se repone el stock que había sido descontado.
        for detalle in pedido.detalles.all().only("producto_id", "cantidad"):
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") + detalle.cantidad)

    pedido.estado = nuevo_estado
    pedido.save(update_fields=["estado"])
    return pedido
