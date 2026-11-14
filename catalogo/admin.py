"""Django Admin del catálogo: búsqueda, filtros y edición rápida de stock."""

from django.contrib import admin
from django.db.models import Count

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "cantidad_productos", "descripcion_corta")
    search_fields = ("nombre", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}
    ordering = ("nombre",)
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total_productos=Count("productos"))

    @admin.display(description="Productos", ordering="total_productos")
    def cantidad_productos(self, obj):
        return obj.total_productos

    @admin.display(description="Descripción")
    def descripcion_corta(self, obj):
        return (obj.descripcion[:60] + "…") if len(obj.descripcion) > 60 else obj.descripcion


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "categoria",
        "precio",
        "stock",
        "activo",
        "fecha_actualizacion",
    )
    list_editable = ("stock", "activo")
    list_filter = ("categoria", "activo", "fecha_creacion")
    search_fields = ("nombre", "descripcion", "categoria__nombre")
    list_select_related = ("categoria",)
    list_per_page = 25
    date_hierarchy = "fecha_creacion"
    ordering = ("nombre",)
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    fieldsets = (
        ("Producto", {"fields": ("nombre", "descripcion", "categoria", "imagen")}),
        ("Precio e inventario", {"fields": ("precio", "stock", "activo")}),
        ("Auditoría", {"fields": ("fecha_creacion", "fecha_actualizacion")}),
    )
