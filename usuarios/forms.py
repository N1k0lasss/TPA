"""Formularios de la app usuarios (registro, login, perfil y gestión)."""

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordChangeForm as PasswordChangeFormBase
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

Usuario = get_user_model()


class BootstrapFormMixin:
    """Agrega las clases de Bootstrap y atributos accesibles a los widgets."""

    def _aplicar_estilos(self):
        for nombre, campo in self.fields.items():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if campo.required:
                widget.attrs.setdefault("required", True)
            if "placeholder" not in widget.attrs:
                widget.attrs["placeholder"] = campo.label or nombre.replace("_", " ").capitalize()


class RegistroForm(BootstrapFormMixin, forms.ModelForm):
    """Alta de clientes. El rol se asigna siempre como Cliente."""

    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Mínimo 8 caracteres"}),
        help_text="Debe tener al menos 8 caracteres y no ser demasiado común.",
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ["nombre", "apellido", "email", "telefono"]
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefono": forms.TextInput(attrs={"autocomplete": "tel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefono"].required = True
        self.fields["email"].label = "Correo electrónico"
        self._aplicar_estilos()
        self.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Mínimo 8 caracteres"})
        self.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Repetí la contraseña"})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta registrada con este correo electrónico.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")

        if password1:
            usuario_temporal = Usuario(
                email=cleaned_data.get("email", ""),
                nombre=cleaned_data.get("nombre", ""),
                apellido=cleaned_data.get("apellido", ""),
            )
            try:
                validate_password(password1, usuario_temporal)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CLIENTE
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
        return usuario


class EmailAuthenticationForm(BootstrapFormMixin, forms.Form):
    """Login con email y contraseña (sin username)."""

    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": "El correo o la contraseña no son correctos. Verificá los datos e intentá nuevamente.",
        "inactive": "Esta cuenta se encuentra deshabilitada. Contactá al administrador.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()
        self.fields["email"].widget.attrs["placeholder"] = "tu@correo.com"
        self.fields["password"].widget.attrs["placeholder"] = "Tu contraseña"

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, username=email.lower(), password=password)
            if self.user_cache is None:
                # ModelBackend devuelve None para cuentas inactivas: se distingue
                # el mensaje para que el usuario sepa que debe contactar al admin.
                inactivo = Usuario.objects.filter(email__iexact=email, is_active=False).exists()
                if inactivo:
                    raise ValidationError(self.error_messages["inactive"], code="inactive")
                raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            if not self.user_cache.is_active:
                raise ValidationError(self.error_messages["inactive"], code="inactive")
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class PerfilForm(BootstrapFormMixin, forms.ModelForm):
    """Datos personales que el propio usuario puede editar."""

    class Meta:
        model = Usuario
        fields = ["nombre", "apellido", "telefono"]
        widgets = {
            "telefono": forms.TextInput(attrs={"autocomplete": "tel"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefono"].required = True
        self._aplicar_estilos()


class UsuarioGestionForm(BootstrapFormMixin, forms.ModelForm):
    """Formulario del administrador para cambiar rol y estado de una cuenta."""

    class Meta:
        model = Usuario
        fields = ["nombre", "apellido", "email", "telefono", "rol", "is_active"]
        widgets = {
            "email": forms.EmailInput(),
        }
        labels = {"is_active": "Cuenta activa"}

    def __init__(self, *args, **kwargs):
        self.administrador = kwargs.pop("administrador", None)
        super().__init__(*args, **kwargs)
        self.fields["email"].disabled = True  # el email es el identificador de la cuenta
        self._aplicar_estilos()

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        activo = cleaned_data.get("is_active")

        if self.administrador and self.instance.pk == self.administrador.pk:
            if rol != Usuario.Rol.ADMIN:
                self.add_error("rol", "No podés quitarte a vos mismo el rol Administrador.")
            if not activo:
                self.add_error("is_active", "No podés desactivar tu propia cuenta.")
        return cleaned_data


class PasswordChangeForm(BootstrapFormMixin, PasswordChangeFormBase):
    """Cambio de contraseña con estilos de Bootstrap."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()
        self.fields["old_password"].widget.attrs["placeholder"] = "Contraseña actual"
        self.fields["new_password1"].widget.attrs["placeholder"] = "Nueva contraseña"
        self.fields["new_password2"].widget.attrs["placeholder"] = "Repetir nueva contraseña"
