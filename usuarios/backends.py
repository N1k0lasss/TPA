"""Backend de autenticación que traduce los roles a permisos de Django.

Las vistas basadas en clases usan `PermissionRequiredMixin` y el propio
Django Admin consulta `has_perm()`. Este backend concede los permisos
personalizados definidos en `Usuario.Meta` según el rol, sin necesidad de
asignar grupos o permisos manualmente a cada cuenta.

El `ModelBackend` tradicional queda como segundo backend, de modo que los
permisos estándar (grupos, permisos por modelo y superusuario) sigan
funcionando.
"""

from django.contrib.auth.backends import ModelBackend

PERMISOS_EMPLEADO = {
    "usuarios.gestionar_tienda",
    # Catálogo y stock
    "catalogo.view_categoria",
    "catalogo.add_categoria",
    "catalogo.change_categoria",
    "catalogo.delete_categoria",
    "catalogo.view_producto",
    "catalogo.add_producto",
    "catalogo.change_producto",
    "catalogo.delete_producto",
    # Pedidos y sus líneas históricas
    "pedidos.view_pedido",
    "pedidos.change_pedido",
    "pedidos.view_detallepedido",
}

PERMISOS_ADMIN = PERMISOS_EMPLEADO | {
    "usuarios.gestionar_usuarios",
    "usuarios.view_usuario",
    "usuarios.add_usuario",
    "usuarios.change_usuario",
    "usuarios.delete_usuario",
    "auth.view_group",
    "auth.add_group",
    "auth.change_group",
    "auth.delete_group",
    "auth.view_permission",
}

PERMISOS_POR_ROL = {
    "Admin": PERMISOS_ADMIN,
    "Empleado": PERMISOS_EMPLEADO,
    "Cliente": set(),
}

APPS_POR_ROL = {
    "Admin": {"usuarios", "catalogo", "pedidos", "auth"},
    "Empleado": {"catalogo", "pedidos"},
    "Cliente": set(),
}


class PermisosPorRolBackend(ModelBackend):
    """Concede permisos de InvenShop y del admin según `Usuario.rol`."""

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        if user_obj.is_superuser:
            return True
        return perm in PERMISOS_POR_ROL.get(getattr(user_obj, "rol", None), set())

    def has_module_perms(self, user_obj, app_label):
        if not user_obj.is_active:
            return False
        if user_obj.is_superuser:
            return True
        return app_label in APPS_POR_ROL.get(getattr(user_obj, "rol", None), set())
