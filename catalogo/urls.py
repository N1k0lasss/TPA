"""Rutas de la app catálogo."""

from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.ProductoListView.as_view(), name="producto_list"),
    path("producto/<int:pk>/", views.ProductoDetailView.as_view(), name="producto_detail"),
    # Gestión interna
    path("gestion/", views.GestionProductoListView.as_view(), name="gestion_productos"),
    path("gestion/nuevo/", views.ProductoCreateView.as_view(), name="producto_create"),
    path("gestion/<int:pk>/editar/", views.ProductoUpdateView.as_view(), name="producto_update"),
    path("gestion/<int:pk>/eliminar/", views.ProductoDeleteView.as_view(), name="producto_delete"),
    path("categorias/", views.GestionCategoriaListView.as_view(), name="gestion_categorias"),
    path("categorias/nueva/", views.CategoriaCreateView.as_view(), name="categoria_create"),
    path("categorias/<int:pk>/editar/", views.CategoriaUpdateView.as_view(), name="categoria_update"),
    path("categorias/<int:pk>/eliminar/", views.CategoriaDeleteView.as_view(), name="categoria_delete"),
]
