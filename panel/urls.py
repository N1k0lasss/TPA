"""Rutas del panel de gestión."""

from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("pedidos.csv", views.exportar_pedidos_csv, name="exportar_pedidos"),
]
