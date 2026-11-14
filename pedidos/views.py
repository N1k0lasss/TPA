"""Vistas del carrito, checkout e historial de pedidos."""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import DetailView, FormView, ListView, TemplateView

from catalogo.models import Producto
from usuarios.mixins import GestorMixin

from .carrito import Carrito
from .forms import CheckoutForm, EstadoPedidoForm
from .models import Pedido
from .services import cambiar_estado, crear_pedido, estados_permitidos


def _destino_seguro(request, por_defecto):
    """Evita redirecciones abiertas al volver a la página anterior."""
    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return por_defecto


# ---------------------------------------------------------------------------
# Carrito (sesión)
# ---------------------------------------------------------------------------
class CarritoDetalleView(TemplateView):
    template_name = "pedidos/carrito.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        items = list(Carrito(self.request))
        contexto["items"] = items
        contexto["total"] = sum((item["subtotal"] for item in items), start=Decimal("0.00"))
        contexto["hay_problemas_de_stock"] = any(item["stock_insuficiente"] for item in items)
        return contexto


class AgregarAlCarritoView(View):
    """Agrega un producto (POST). Funciona incluso sin iniciar sesión."""

    def post(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk, activo=True)
        try:
            cantidad = int(request.POST.get("cantidad", 1))
            Carrito(request).agregar(producto, cantidad)
        except (TypeError, ValueError):
            messages.error(request, "La cantidad ingresada no es válida.")
        except ValidationError as error:
            for mensaje in error.messages:
                messages.error(request, mensaje)
        else:
            messages.success(request, f'Agregaste "{producto.nombre}" al carrito.')
        return redirect(_destino_seguro(request, producto.get_absolute_url()))


class ActualizarCarritoView(View):
    def post(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk, activo=True)
        try:
            cantidad = int(request.POST.get("cantidad", 1))
            Carrito(request).actualizar(producto, cantidad)
        except (TypeError, ValueError):
            messages.error(request, "La cantidad ingresada no es válida.")
        except ValidationError as error:
            for mensaje in error.messages:
                messages.error(request, mensaje)
        else:
            messages.success(request, f'Actualizaste la cantidad de "{producto.nombre}".')
        return redirect("carrito:detalle")


class QuitarDelCarritoView(View):
    def post(self, request, pk):
        producto = Producto.objects.filter(pk=pk).first()
        Carrito(request).quitar(pk)
        if producto:
            messages.info(request, f'Quitaste "{producto.nombre}" del carrito.')
        else:
            messages.info(request, "El producto fue quitado del carrito.")
        return redirect("carrito:detalle")


class VaciarCarritoView(View):
    def post(self, request):
        Carrito(request).vaciar()
        messages.info(request, "Vaciaste el carrito.")
        return redirect("carrito:detalle")


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------
class CheckoutView(LoginRequiredMixin, FormView):
    """Solo usuarios autenticados. Resumen + datos de envío + confirmación."""

    template_name = "pedidos/checkout.html"
    form_class = CheckoutForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.carrito = Carrito(request)
        self.items = list(self.carrito)
        if not self.items:
            messages.info(request, "Tu carrito está vacío. Agregá productos para continuar.")
            return redirect("carrito:detalle")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        inicial = super().get_initial()
        inicial.setdefault("telefono_contacto", self.request.user.telefono)
        return inicial

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["items"] = self.items
        contexto["total"] = sum((item["subtotal"] for item in self.items), start=Decimal("0.00"))
        return contexto

    def form_valid(self, form):
        datos = {
            "direccion": form.cleaned_data["direccion"],
            "ciudad": form.cleaned_data["ciudad"],
            "codigo_postal": form.cleaned_data["codigo_postal"],
            "telefono_contacto": form.cleaned_data["telefono_contacto"],
            "notas": form.cleaned_data.get("notas", ""),
        }
        try:
            pedido = crear_pedido(self.request.user, Carrito(self.request), datos)
        except ValidationError as error:
            for mensaje in error.messages:
                messages.error(self.request, mensaje)
            return redirect("carrito:detalle")

        messages.success(
            self.request,
            f"¡Pedido {pedido.numero} confirmado! Ya estamos preparando tu compra.",
        )
        return redirect("pedidos:confirmacion", pk=pedido.pk)


class PedidoConfirmacionView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = "pedidos/confirmacion.html"
    context_object_name = "pedido"

    def get_queryset(self):
        queryset = Pedido.objects.select_related("usuario").prefetch_related("detalles__producto")
        if not self.request.user.es_gestor:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset


# ---------------------------------------------------------------------------
# Historial y detalle
# ---------------------------------------------------------------------------
class PedidoListView(LoginRequiredMixin, ListView):
    """Los clientes ven solo sus pedidos; el staff ve todos."""

    model = Pedido
    template_name = "pedidos/pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Pedido.objects.select_related("usuario")
            .prefetch_related("detalles")
            .order_by("-fecha_creacion")
        )
        if not self.request.user.es_gestor:
            queryset = queryset.filter(usuario=self.request.user)

        estado = self.request.GET.get("estado", "").strip()
        if estado in Pedido.Estado.values:
            queryset = queryset.filter(estado=estado)

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            filtro = Q()
            if self.request.user.es_gestor:
                filtro |= (
                    Q(usuario__email__icontains=busqueda)
                    | Q(usuario__nombre__icontains=busqueda)
                    | Q(usuario__apellido__icontains=busqueda)
                )
            if busqueda.isdigit():
                filtro |= Q(pk=int(busqueda))
            if filtro:
                queryset = queryset.filter(filtro)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["estados"] = Pedido.Estado.choices
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        contexto["q"] = self.request.GET.get("q", "")
        return contexto


class PedidoDetailView(LoginRequiredMixin, DetailView):
    """Detalle con control de acceso a nivel de objeto."""

    model = Pedido
    template_name = "pedidos/pedido_detail.html"
    context_object_name = "pedido"

    def get_queryset(self):
        queryset = Pedido.objects.select_related("usuario").prefetch_related(
            "detalles__producto__categoria"
        )
        if not self.request.user.es_gestor:
            queryset = queryset.filter(usuario=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["estados_permitidos"] = estados_permitidos(self.object.estado)
        contexto["linea_tiempo"] = [
            {
                "nombre": estado,
                "alcanzado": self._estado_alcanzado(estado),
                "actual": self.object.estado == estado,
            }
            for estado in [Pedido.Estado.PENDIENTE, Pedido.Estado.PAGADO, Pedido.Estado.ENVIADO]
        ]
        return contexto

    def _estado_alcanzado(self, estado):
        orden = [Pedido.Estado.PENDIENTE, Pedido.Estado.PAGADO, Pedido.Estado.ENVIADO]
        if self.object.estado == Pedido.Estado.CANCELADO:
            return False
        return orden.index(estado) <= orden.index(self.object.estado)


class PedidoEstadoUpdateView(GestorMixin, View):
    """Solo Administrador y Empleado pueden cambiar el estado de un pedido."""

    template_name = "pedidos/pedido_estado.html"

    def dispatch(self, request, *args, **kwargs):
        self.pedido = get_object_or_404(Pedido, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not estados_permitidos(self.pedido.estado):
            messages.info(request, "Este pedido ya está en un estado final y no se puede modificar.")
            return redirect("pedidos:detalle", pk=self.pedido.pk)
        return self._render(request, EstadoPedidoForm(pedido=self.pedido))

    def post(self, request, *args, **kwargs):
        form = EstadoPedidoForm(request.POST, pedido=self.pedido)
        if form.is_valid():
            try:
                cambiar_estado(self.pedido, form.cleaned_data["estado"])
            except ValidationError as error:
                for mensaje in error.messages:
                    messages.error(request, mensaje)
            else:
                messages.success(
                    request,
                    f"El pedido {self.pedido.numero} pasó a estado «{form.cleaned_data['estado']}».",
                )
                return redirect("pedidos:detalle", pk=self.pedido.pk)
        return self._render(request, form)

    def _render(self, request, form):
        return render(
            request,
            self.template_name,
            {
                "pedido": self.pedido,
                "form": form,
                "estados_permitidos": estados_permitidos(self.pedido.estado),
            },
        )
