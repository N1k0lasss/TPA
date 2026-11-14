"""Panel de gestión: tablero con métricas y reportes básicos."""

from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import render
from django.views.generic import TemplateView

from catalogo.models import Producto
from pedidos.models import Pedido
from usuarios.mixins import GestorMixin
from usuarios.models import Usuario


class DashboardView(GestorMixin, TemplateView):
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        pedidos = Pedido.objects.all()

        por_estado = {
            fila["estado"]: fila["total"]
            for fila in pedidos.values("estado").annotate(total=Count("id"))
        }
        pedidos_validos = pedidos.exclude(estado=Pedido.Estado.CANCELADO)
        ventas = pedidos_validos.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        cantidad_validos = pedidos_validos.count()

        contexto.update(
            {
                "ventas_totales": ventas,
                "pedidos_totales": pedidos.count(),
                "pedidos_validos": cantidad_validos,
                "ticket_promedio": (ventas / cantidad_validos) if cantidad_validos else Decimal("0.00"),
                "pedidos_pendientes": por_estado.get(Pedido.Estado.PENDIENTE, 0),
                "pedidos_pagados": por_estado.get(Pedido.Estado.PAGADO, 0),
                "pedidos_enviados": por_estado.get(Pedido.Estado.ENVIADO, 0),
                "pedidos_cancelados": por_estado.get(Pedido.Estado.CANCELADO, 0),
                "por_estado": [
                    {
                        "nombre": estado,
                        "cantidad": por_estado.get(estado, 0),
                    }
                    for estado in Pedido.Estado.values
                ],
                "productos_activos": Producto.objects.filter(activo=True).count(),
                "productos_sin_stock": Producto.objects.filter(activo=True, stock=0).count(),
                "stock_bajo": Producto.objects.filter(
                    activo=True, stock__lte=Producto.UMBRAL_STOCK_BAJO
                )
                .select_related("categoria")
                .order_by("stock", "nombre")[:6],
                "valor_inventario": Producto.objects.filter(activo=True).aggregate(
                    valor=Sum(
                        ExpressionWrapper(
                            F("precio") * F("stock"),
                            output_field=DecimalField(max_digits=14, decimal_places=2),
                        )
                    )
                )["valor"]
                or Decimal("0.00"),
                "ultimos_pedidos": Pedido.objects.select_related("usuario").prefetch_related("detalles")[:8],
                "total_usuarios": Usuario.objects.count(),
                "total_clientes": Usuario.objects.filter(rol=Usuario.Rol.CLIENTE).count(),
            }
        )
        return contexto


# ---------------------------------------------------------------------------
# Páginas de error personalizadas
# ---------------------------------------------------------------------------
def error_403(request, exception=None):
    return render(request, "errores/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errores/404.html", status=404)


def error_500(request):
    return render(request, "errores/500.html", status=500)
