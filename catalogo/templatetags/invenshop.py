"""Filtros y etiquetas de plantilla de InvenShop."""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def pesos(valor):
    """Formatea un número como precio argentino: $ 12.345,00."""
    if valor in (None, ""):
        return "$ 0,00"
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return valor
    formato = f"{numero:,.2f}"
    formato = formato.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {formato}"


@register.filter
def estado_badge(estado):
    """Devuelve la clase CSS asociada al estado de un pedido."""
    mapa = {
        "Pendiente": "estado-pendiente",
        "Pagado": "estado-pagado",
        "Enviado": "estado-enviado",
        "Cancelado": "estado-cancelado",
    }
    return mapa.get(estado, "chip-neutral")


@register.filter
def rol_badge(rol):
    mapa = {
        "Admin": "chip",
        "Empleado": "chip chip-neutral",
        "Cliente": "chip",
    }
    return mapa.get(rol, "chip")


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Arma una query string conservando los filtros actuales.

    Ejemplo: {% querystring page=2 %} o {% querystring categoria=None %}
    """
    request = context.get("request")
    if request is None:
        return ""
    query = request.GET.copy()
    for clave, valor in kwargs.items():
        if valor is None or valor == "":
            query.pop(clave, None)
        else:
            query[clave] = valor
    return query.urlencode()
