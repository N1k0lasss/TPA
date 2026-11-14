"""Rutas de pedidos."""

from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.PedidoListView.as_view(), name="lista"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("<int:pk>/", views.PedidoDetailView.as_view(), name="detalle"),
    path("<int:pk>/confirmacion/", views.PedidoConfirmacionView.as_view(), name="confirmacion"),
    path("<int:pk>/estado/", views.PedidoEstadoUpdateView.as_view(), name="cambiar_estado"),
]
