"""Administración de usuarios (Django Admin personalizado)."""

from django import forms
from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from .models import Usuario


class UsuarioAdminCreationForm(UserCreationForm):
    """Alta de usuarios desde el admin sin campo username."""

    class Meta:
        model = Usuario
        fields = ("email", "nombre", "apellido", "telefono", "rol")


class UsuarioAdminChangeForm(UserChangeForm):
    """Edición de usuarios desde el admin sin campo username."""

    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioAdminChangeForm
    add_form = UsuarioAdminCreationForm
    model = Usuario

    list_display = ("email", "nombre", "apellido", "rol", "telefono", "is_active", "cantidad_pedidos")
    list_filter = ("rol", "is_active", "is_staff")
    search_fields = ("email", "nombre", "apellido", "telefono")
    ordering = ("apellido", "nombre")
    list_per_page = 20
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Datos personales"), {"fields": ("nombre", "apellido", "telefono")}),
        (
            _("Rol y permisos"),
            {
                "fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "description": "El rol define el acceso a la tienda, al panel de gestión y al admin.",
            },
        ),
        (_("Fechas importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nombre", "apellido", "telefono", "rol", "password1", "password2"),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total_pedidos=Count("pedidos"))

    @admin.display(description="Pedidos", ordering="total_pedidos")
    def cantidad_pedidos(self, obj):
        return obj.total_pedidos

    def save_model(self, request, obj, form, change):
        # Mantiene la contraseña encriptada al crear desde el admin.
        if not change and form.cleaned_data.get("password1"):
            obj.set_password(form.cleaned_data["password1"])
        super().save_model(request, obj, form, change)
