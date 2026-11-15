"""Panel de gestión: tablero con métricas y reportes básicos."""

import csv
from decimal import Decimal

from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from catalogo.models import Producto
from pedidos.consultas import filtrar_pedidos
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
# Reportes (vista basada en función con decoradores de acceso)
# ---------------------------------------------------------------------------
def _celda(valor):
    """Evita que Excel interprete texto como fórmula (CSV injection)."""
    texto = "" if valor is None else str(valor)
    if texto.startswith(("=", "+", "-", "@")):
        return f"'{texto}"
    return texto


@login_required
@permission_required("usuarios.gestionar_tienda", raise_exception=True)
def exportar_pedidos_csv(request):
    """Descarga el historial de pedidos como CSV respetando los filtros.

    Es la única vista basada en función del proyecto y existe para cumplir
    el requisito de la consigna de usar `@login_required` y
    `@permission_required` además de los mixins de las CBV.

    - Anónimo -> redirección al login.
    - Cliente autenticado -> 403 (no tiene el permiso de gestión).
    - Empleado/Administrador -> descarga del reporte.
    """
    pedidos = filtrar_pedidos(
        Pedido.objects.select_related("usuario").prefetch_related("detalles"),
        usuario=request.user,
        busqueda=request.GET.get("q", ""),
        estado=request.GET.get("estado", ""),
    ).order_by("-fecha_creacion")

    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    nombre = f"pedidos_{timezone.localtime():%Y%m%d_%H%M}.csv"
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    # BOM para que Excel reconozca los acentos del archivo UTF-8.
    respuesta.write("\ufeff")

    escritor = csv.writer(respuesta, delimiter=";")
    escritor.writerow(
        [
            "Pedido",
            "Fecha",
            "Estado",
            "Cliente",
            "Email",
            "Teléfono",
            "Dirección",
            "Ciudad",
            "Código postal",
            "Ítems",
            "Total",
        ]
    )
    for pedido in pedidos:
        escritor.writerow(
            [
                pedido.numero,
                timezone.localtime(pedido.fecha_creacion).strftime("%d/%m/%Y %H:%M"),
                pedido.estado,
                _celda(pedido.usuario.nombre_completo),
                _celda(pedido.usuario.email),
                _celda(pedido.telefono_contacto),
                _celda(pedido.direccion),
                _celda(pedido.ciudad),
                _celda(pedido.codigo_postal),
                pedido.cantidad_items,
                f"{pedido.total:.2f}".replace(".", ","),
            ]
        )
    return respuesta


# ---------------------------------------------------------------------------
# Páginas de error personalizadas
# ---------------------------------------------------------------------------
def error_403(request, exception=None):
    return render(request, "errores/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "errores/404.html", status=404)


def error_500(request):
    return render(request, "errores/500.html", status=500)
