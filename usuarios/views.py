"""Vistas de autenticación, perfil y gestión de usuarios."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import (
    EmailAuthenticationForm,
    PasswordChangeForm,
    PerfilForm,
    RegistroForm,
    UsuarioGestionForm,
)
from .mixins import AdminMixin
from .models import Usuario


class RegistroView(CreateView):
    """Registro público. Todo usuario nuevo recibe el rol Cliente."""

    model = Usuario
    form_class = RegistroForm
    template_name = "usuarios/registro.html"
    success_url = reverse_lazy("catalogo:producto_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("catalogo:producto_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(
            self.request,
            f"¡Bienvenido/a a InvenShop, {self.object.nombre}! Tu cuenta fue creada correctamente.",
        )
        return respuesta


class IniciarSesionView(LoginView):
    """Login con email. Redirige según el rol del usuario."""

    authentication_form = EmailAuthenticationForm
    template_name = "usuarios/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        destino = self.get_redirect_url()
        if destino:
            return destino
        if self.request.user.es_gestor:
            return reverse("panel:dashboard")
        return reverse("catalogo:producto_list")

    def form_valid(self, form):
        messages.success(self.request, f"¡Hola de nuevo, {form.get_user().nombre}!")
        return super().form_valid(form)


class CerrarSesionView(LogoutView):
    next_page = reverse_lazy("catalogo:producto_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Cerraste sesión correctamente.")
        return super().dispatch(request, *args, **kwargs)


class PerfilView(LoginRequiredMixin, UpdateView):
    """Cada usuario ve y edita únicamente su propio perfil."""

    model = Usuario
    form_class = PerfilForm
    template_name = "usuarios/perfil.html"
    success_url = reverse_lazy("usuarios:perfil")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Tus datos personales se actualizaron correctamente.")
        return super().form_valid(form)


class CambiarPasswordView(LoginRequiredMixin, PasswordChangeView):
    form_class = PasswordChangeForm
    template_name = "usuarios/password_change.html"
    success_url = reverse_lazy("usuarios:perfil")

    def form_valid(self, form):
        messages.success(self.request, "Tu contraseña se cambió correctamente.")
        return super().form_valid(form)


class UsuarioListView(AdminMixin, ListView):
    """Listado de cuentas (solo Administrador)."""

    model = Usuario
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"
    paginate_by = 12

    def get_queryset(self):
        queryset = Usuario.objects.annotate(cantidad_pedidos=Count("pedidos")).order_by(
            "apellido", "nombre"
        )
        busqueda = self.request.GET.get("q", "").strip()
        rol = self.request.GET.get("rol", "").strip()
        if busqueda:
            queryset = queryset.filter(
                Q(email__icontains=busqueda)
                | Q(nombre__icontains=busqueda)
                | Q(apellido__icontains=busqueda)
            )
        if rol in Usuario.Rol.values:
            queryset = queryset.filter(rol=rol)
        return queryset

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["q"] = self.request.GET.get("q", "")
        contexto["rol_actual"] = self.request.GET.get("rol", "")
        contexto["roles"] = Usuario.Rol.choices
        return contexto


class UsuarioUpdateView(AdminMixin, UpdateView):
    """Edición de rol y estado de una cuenta (solo Administrador)."""

    model = Usuario
    form_class = UsuarioGestionForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:usuario_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["administrador"] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"La cuenta de {form.instance.nombre_completo} fue actualizada.")
        return super().form_valid(form)
