"""Mixins de autorización reutilizables para las vistas basadas en clases."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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


class GestorMixin(RolRequeridoMixin):
    """Solo Administrador y Empleado."""

    roles_permitidos = ("Admin", "Empleado")


class AdminMixin(RolRequeridoMixin):
    """Solo Administrador."""

    roles_permitidos = ("Admin",)
