"""Consultas reutilizables sobre pedidos (listado, admin y reportes)."""

from django.db.models import Q

from .models import Pedido


def filtrar_pedidos(queryset, *, usuario, busqueda="", estado=""):
    """Aplica el alcance por rol y los filtros del historial de pedidos.

    - Los clientes solo ven sus propios pedidos.
    - El staff puede filtrar por estado y buscar por número visible
      (`#000006`), nombre, apellido o email del cliente.

    Se usa tanto en la vista de listado como en el reporte CSV para que
    ambos muestren exactamente los mismos resultados.
    """
    if not usuario.es_gestor:
        queryset = queryset.filter(usuario=usuario)

    estado = (estado or "").strip()
    if estado in Pedido.Estado.values:
        queryset = queryset.filter(estado=estado)

    busqueda = (busqueda or "").strip()
    if busqueda:
        filtro = Q()
        if usuario.es_gestor:
            filtro |= (
                Q(usuario__email__icontains=busqueda)
                | Q(usuario__nombre__icontains=busqueda)
                | Q(usuario__apellido__icontains=busqueda)
            )
        numero = busqueda.lstrip("#")
        if numero.isdigit():
            filtro |= Q(pk=int(numero))
        if filtro:
            queryset = queryset.filter(filtro)

    return queryset
