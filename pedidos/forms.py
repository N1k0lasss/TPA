"""Formularios de checkout y de cambios de estado."""

import re

from django import forms

from .models import Pedido
from .services import estados_permitidos

PATRON_CODIGO_POSTAL = re.compile(r"^[A-Za-z0-9]{3,8}$")
PATRON_TELEFONO = re.compile(r"^[0-9+\-()\s]{6,25}$")


class BootstrapFormMixin:
    def _aplicar_estilos(self):
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if campo.required:
                widget.attrs.setdefault("required", True)


class CheckoutForm(BootstrapFormMixin, forms.ModelForm):
    """Datos de envío + confirmación final antes de registrar el pedido."""

    confirmar = forms.BooleanField(
        label="Confirmo que los datos de envío son correctos y quiero finalizar la compra.",
        error_messages={"required": "Tenés que confirmar los datos para finalizar el pedido."},
    )

    class Meta:
        model = Pedido
        fields = ["direccion", "ciudad", "codigo_postal", "telefono_contacto", "notas"]
        widgets = {
            "direccion": forms.TextInput(attrs={"placeholder": "Calle, número, piso/depto", "autocomplete": "street-address"}),
            "ciudad": forms.TextInput(attrs={"placeholder": "Ciudad", "autocomplete": "address-level2"}),
            "codigo_postal": forms.TextInput(attrs={"placeholder": "Ej.: 2000", "autocomplete": "postal-code"}),
            "telefono_contacto": forms.TextInput(attrs={"placeholder": "Ej.: 341 555-0123", "autocomplete": "tel"}),
            "notas": forms.Textarea(attrs={"rows": 2, "placeholder": "Timbre, horario de entrega u otra referencia (opcional)"}),
        }
        labels = {
            "direccion": "Dirección de envío",
            "ciudad": "Ciudad",
            "codigo_postal": "Código postal",
            "telefono_contacto": "Teléfono de contacto",
            "notas": "Notas para el envío",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["notas"].required = False
        self._aplicar_estilos()
        self.fields["confirmar"].widget.attrs.update({"class": "form-check-input"})

    def clean_direccion(self):
        direccion = self.cleaned_data["direccion"].strip()
        if len(direccion) < 5:
            raise forms.ValidationError("Ingresá una dirección completa (calle y número).")
        return direccion

    def clean_ciudad(self):
        ciudad = self.cleaned_data["ciudad"].strip()
        if len(ciudad) < 2:
            raise forms.ValidationError("Ingresá una ciudad válida.")
        return ciudad

    def clean_codigo_postal(self):
        codigo = self.cleaned_data["codigo_postal"].strip()
        if not PATRON_CODIGO_POSTAL.match(codigo):
            raise forms.ValidationError("El código postal debe tener entre 3 y 8 letras o números.")
        return codigo.upper()

    def clean_telefono_contacto(self):
        telefono = self.cleaned_data["telefono_contacto"].strip()
        if not PATRON_TELEFONO.match(telefono):
            raise forms.ValidationError("Ingresá un teléfono válido (entre 6 y 25 dígitos, puede incluir +, - y paréntesis).")
        return telefono


class EstadoPedidoForm(BootstrapFormMixin, forms.Form):
    """Permite elegir solo estados alcanzables desde el estado actual."""

    estado = forms.ChoiceField(label="Nuevo estado")

    def __init__(self, *args, pedido=None, **kwargs):
        self.pedido = pedido
        super().__init__(*args, **kwargs)
        opciones = [(estado, estado) for estado in estados_permitidos(pedido.estado)] if pedido else []
        self.fields["estado"].choices = opciones
        self._aplicar_estilos()
        self.fields["estado"].widget.attrs["class"] = "form-select"
