"""Mixins de autorización reutilizables para las vistas basadas en clases."""

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe una CBV a los roles indicados en `roles_permitidos`.

    - Usuario anónimo -> redirección al login (con ?next=).
    - Usuario autenticado sin permiso -> error 403.
    """

    roles_permitidos = ()

    def test_func(self):
        usuario = self.request.user
        if not usuario.is_authenticated:
            return False
        return usuario.is_superuser or usuario.rol in self.roles_permitidos

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("No tenés permisos para acceder a esta sección.")


class GestorMixin(RolRequeridoMixin, PermissionRequiredMixin):
    """Solo Administrador y Empleado, con el permiso de gestión de tienda."""

    roles_permitidos = ("Admin", "Empleado")
    permission_required = "usuarios.gestionar_tienda"


class AdminMixin(RolRequeridoMixin, PermissionRequiredMixin):
    """Solo Administrador, con el permiso de gestión de usuarios."""

    roles_permitidos = ("Admin",)
    permission_required = "usuarios.gestionar_usuarios"
