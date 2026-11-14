"""Vistas del catálogo: tienda pública y gestión para staff."""

from django.contrib import messages
from django.db.models import Count, ProtectedError, Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from usuarios.mixins import GestorMixin

from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto

ORDENAMIENTOS = {
    "nombre": ("nombre",),
    "-nombre": ("-nombre",),
    "precio": ("precio", "nombre"),
    "-precio": ("-precio", "nombre"),
    "recientes": ("-fecha_creacion",),
}


class ProductoListView(ListView):
    """Catálogo público con búsqueda, filtro, orden y paginación."""

    model = Producto
    template_name = "catalogo/producto_list.html"
    context_object_name = "productos"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Producto.objects.filter(activo=True)
            .select_related("categoria")
            .order_by(*ORDENAMIENTOS.get(self.request.GET.get("orden", "nombre"), ("nombre",)))
        )

        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
            )

        categoria_slug = self.request.GET.get("categoria", "").strip()
        if categoria_slug:
            queryset = queryset.filter(categoria__slug=categoria_slug)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        categoria_slug = self.request.GET.get("categoria", "").strip()
        contexto["categorias"] = Categoria.objects.annotate(
            total_productos=Count("productos", filter=Q(productos__activo=True))
        )
        contexto["categoria_actual"] = Categoria.objects.filter(slug=categoria_slug).first()
        contexto["q"] = self.request.GET.get("q", "").strip()
        contexto["orden"] = self.request.GET.get("orden", "nombre")
        contexto["total_resultados"] = self.get_queryset().count()
        return contexto


class ProductoDetailView(DetailView):
    """Ficha individual de un producto activo."""

    model = Producto
    template_name = "catalogo/producto_detail.html"
    context_object_name = "producto"

    def get_queryset(self):
        return Producto.objects.filter(activo=True).select_related("categoria")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["relacionados"] = (
            Producto.objects.filter(activo=True, categoria=self.object.categoria)
            .exclude(pk=self.object.pk)
            .select_related("categoria")[:4]
        )
        carrito = self.request.session.get("carrito", {})
        contexto["en_carrito"] = int(carrito.get(str(self.object.pk), {}).get("cantidad", 0))
        return contexto


# ---------------------------------------------------------------------------
# Gestión de productos (Administrador y Empleado)
# ---------------------------------------------------------------------------
class GestionProductoListView(GestorMixin, ListView):
    model = Producto
    template_name = "catalogo/gestion_producto_list.html"
    context_object_name = "productos"
    paginate_by = 15

    def get_queryset(self):
        queryset = Producto.objects.select_related("categoria").order_by("nombre")
        busqueda = self.request.GET.get("q", "").strip()
        categoria = self.request.GET.get("categoria", "").strip()
        estado = self.request.GET.get("estado", "").strip()

        if busqueda:
            queryset = queryset.filter(Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda))
        if categoria:
            queryset = queryset.filter(categoria__slug=categoria)
        if estado == "bajo":
            queryset = queryset.filter(activo=True, stock__lte=Producto.UMBRAL_STOCK_BAJO)
        elif estado == "inactivos":
            queryset = queryset.filter(activo=False)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["categorias"] = Categoria.objects.all()
        contexto["q"] = self.request.GET.get("q", "")
        contexto["categoria_actual"] = self.request.GET.get("categoria", "")
        contexto["estado_actual"] = self.request.GET.get("estado", "")
        contexto["umbral_stock"] = Producto.UMBRAL_STOCK_BAJO
        return contexto


class ProductoCreateView(GestorMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = "catalogo/producto_form.html"
    success_url = reverse_lazy("catalogo:gestion_productos")

    def form_valid(self, form):
        messages.success(self.request, f'El producto "{form.instance.nombre}" fue creado correctamente.')
        return super().form_valid(form)


class ProductoUpdateView(GestorMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = "catalogo/producto_form.html"

    def get_success_url(self):
        return reverse("catalogo:gestion_productos")

    def form_valid(self, form):
        messages.success(self.request, f'El producto "{form.instance.nombre}" fue actualizado.')
        return super().form_valid(form)


class ProductoDeleteView(GestorMixin, DeleteView):
    model = Producto
    template_name = "catalogo/producto_confirm_delete.html"
    success_url = reverse_lazy("catalogo:gestion_productos")
    context_object_name = "producto"

    def form_valid(self, form):
        nombre = self.object.nombre
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f'No se puede eliminar "{nombre}" porque figura en pedidos registrados. '
                "Podés desactivarlo para ocultarlo del catálogo.",
            )
            return HttpResponseRedirect(self.success_url)
        messages.success(self.request, f'El producto "{nombre}" fue eliminado.')
        return respuesta


# ---------------------------------------------------------------------------
# Gestión de categorías (Administrador y Empleado)
# ---------------------------------------------------------------------------
class GestionCategoriaListView(GestorMixin, ListView):
    model = Categoria
    template_name = "catalogo/categoria_list.html"
    context_object_name = "categorias"

    def get_queryset(self):
        return Categoria.objects.annotate(total_productos=Count("productos")).order_by("nombre")


class CategoriaCreateView(GestorMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "catalogo/categoria_form.html"
    success_url = reverse_lazy("catalogo:gestion_categorias")

    def form_valid(self, form):
        messages.success(self.request, f'La categoría "{form.instance.nombre}" fue creada.')
        return super().form_valid(form)


class CategoriaUpdateView(GestorMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "catalogo/categoria_form.html"
    success_url = reverse_lazy("catalogo:gestion_categorias")

    def form_valid(self, form):
        messages.success(self.request, f'La categoría "{form.instance.nombre}" fue actualizada.')
        return super().form_valid(form)


class CategoriaDeleteView(GestorMixin, DeleteView):
    model = Categoria
    template_name = "catalogo/categoria_confirm_delete.html"
    success_url = reverse_lazy("catalogo:gestion_categorias")
    context_object_name = "categoria"

    def form_valid(self, form):
        nombre = self.object.nombre
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f'No se puede eliminar "{nombre}" porque tiene productos asociados. '
                "Reasigná o eliminá esos productos primero.",
            )
            return HttpResponseRedirect(self.success_url)
        messages.success(self.request, f'La categoría "{nombre}" fue eliminada.')
        return respuesta
