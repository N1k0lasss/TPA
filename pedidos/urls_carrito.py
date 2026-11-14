"""Rutas del carrito."""

from django.urls import path

from . import views

app_name = "carrito"

urlpatterns = [
    path("", views.CarritoDetalleView.as_view(), name="detalle"),
    path("agregar/<int:pk>/", views.AgregarAlCarritoView.as_view(), name="agregar"),
    path("actualizar/<int:pk>/", views.ActualizarCarritoView.as_view(), name="actualizar"),
    path("quitar/<int:pk>/", views.QuitarDelCarritoView.as_view(), name="quitar"),
    path("vaciar/", views.VaciarCarritoView.as_view(), name="vaciar"),
]
