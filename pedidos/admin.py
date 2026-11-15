"""Django Admin de pedidos: estados, inlines y datos históricos de solo lectura."""

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils.html import format_html

from catalogo.models import Producto

from .models import DetallePedido, Pedido
from .services import TRANSICIONES, cambiar_estado


class PedidoAdminForm(forms.ModelForm):
    """Valida las transiciones de estado también desde el admin."""

    class Meta:
        model = Pedido
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        nuevo_estado = cleaned_data.get("estado")
        # En clean() la instancia todavía conserva el estado guardado en la BD.
        if self.instance.pk and nuevo_estado:
            anterior = self.instance.estado
            if nuevo_estado != anterior and nuevo_estado not in TRANSICIONES.get(anterior, set()):
                raise ValidationError(
                    {"estado": f"Transición inválida: de «{anterior}» no se puede pasar a «{nuevo_estado}»."}
                )
        return cleaned_data


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    can_delete = False
    fields = ("producto", "cantidad", "precio_unitario", "subtotal")
    readonly_fields = ("producto", "cantidad", "precio_unitario", "subtotal")
    verbose_name = "detalle del pedido"
    verbose_name_plural = "detalles del pedido (histórico de solo lectura)"

    def has_add_permission(self, request, obj=None):
        # El detalle se genera en el checkout y no debe modificarse desde el admin.
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        if not obj.pk:
            return "—"
        return format_html("$ {}", f"{obj.subtotal:,.2f}".replace(",", "."))


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    form = PedidoAdminForm
    inlines = [DetallePedidoInline]

    list_display = ("numero", "usuario", "fecha_creacion", "estado", "total", "cantidad_items")
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("id", "usuario__email", "usuario__nombre", "usuario__apellido")
    date_hierarchy = "fecha_creacion"
    list_select_related = ("usuario",)
    list_per_page = 20
    ordering = ("-fecha_creacion",)
    readonly_fields = (
        "usuario",
        "fecha_creacion",
        "total",
        "direccion",
        "ciudad",
        "codigo_postal",
        "telefono_contacto",
        "notas",
    )
    fieldsets = (
        ("Pedido", {"fields": ("usuario", "fecha_creacion", "estado", "total")}),
        (
            "Datos de envío (histórico)",
            {"fields": ("direccion", "ciudad", "codigo_postal", "telefono_contacto", "notas")},
        ),
    )
    actions = ("marcar_pagado", "marcar_enviado", "marcar_cancelado")

    def has_add_permission(self, request):
        # Los pedidos se generan desde el checkout; el admin solo los consulta y gestiona.
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("detalles")

    def get_search_results(self, request, queryset, search_term):
        """Permite buscar por el número visible (#000006) además del id."""
        resultados, use_distinct = super().get_search_results(request, queryset, search_term)
        numero = search_term.strip().lstrip("#")
        if numero.isdigit():
            resultados |= self.model.objects.filter(pk=int(numero))
        return resultados, use_distinct

    @admin.display(description="Pedido", ordering="-fecha_creacion")
    def numero(self, obj):
        return obj.numero

    @admin.display(description="Ítems")
    def cantidad_items(self, obj):
        return obj.cantidad_items

    def save_model(self, request, obj, form, change):
        anterior = None
        if change:
            anterior = Pedido.objects.filter(pk=obj.pk).values_list("estado", flat=True).first()
        super().save_model(request, obj, form, change)
        if anterior == Pedido.Estado.CANCELADO or obj.estado != Pedido.Estado.CANCELADO:
            return
        # Se canceló desde el admin: se repone el stock una sola vez.
        for detalle in obj.detalles.all():
            Producto.objects.filter(pk=detalle.producto_id).update(stock=F("stock") + detalle.cantidad)
        self.message_user(
            request,
            f"Pedido {obj.numero} cancelado: se repuso el stock de sus productos.",
            messages.WARNING,
        )

    # ------------------------------------------------------------------
    # Acciones masivas
    # ------------------------------------------------------------------
    @admin.action(description="Marcar pedidos seleccionados como Pagado")
    def marcar_pagado(self, request, queryset):
        self._aplicar_estado(request, queryset, Pedido.Estado.PAGADO)

    @admin.action(description="Marcar pedidos seleccionados como Enviado")
    def marcar_enviado(self, request, queryset):
        self._aplicar_estado(request, queryset, Pedido.Estado.ENVIADO)

    @admin.action(description="Cancelar pedidos seleccionados (repone stock)")
    def marcar_cancelado(self, request, queryset):
        self._aplicar_estado(request, queryset, Pedido.Estado.CANCELADO)

    def _aplicar_estado(self, request, queryset, nuevo_estado):
        actualizados, con_error = 0, 0
        for pedido in queryset:
            try:
                cambiar_estado(pedido, nuevo_estado)
            except ValidationError:
                con_error += 1
            else:
                actualizados += 1
        if actualizados:
            self.message_user(request, f"{actualizados} pedido(s) actualizados a «{nuevo_estado}».")
        if con_error:
            self.message_user(
                request,
                f"{con_error} pedido(s) no pudieron cambiarse por transiciones inválidas.",
                messages.ERROR,
            )
