"""Rutas de la app usuarios."""

from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("registro/", views.RegistroView.as_view(), name="registro"),
    path("login/", views.IniciarSesionView.as_view(), name="login"),
    path("logout/", views.CerrarSesionView.as_view(), name="logout"),
    path("perfil/", views.PerfilView.as_view(), name="perfil"),
    path("password/", views.CambiarPasswordView.as_view(), name="password_change"),
    path("gestion/", views.UsuarioListView.as_view(), name="usuario_list"),
    path("gestion/<int:pk>/", views.UsuarioUpdateView.as_view(), name="usuario_update"),
]
