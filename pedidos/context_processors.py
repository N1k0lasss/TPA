"""Context processor: cantidad de ítems del carrito para el navbar."""

CLAVE_SESION = "carrito"


def carrito(request):
    datos = request.session.get(CLAVE_SESION, {})
    if not isinstance(datos, dict):
        datos = {}
    cantidad = sum(int(item.get("cantidad", 0)) for item in datos.values() if isinstance(item, dict))
    return {"carrito_cantidad": cantidad}
