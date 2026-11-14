"""Formularios del catálogo con validaciones personalizadas."""

from django import forms

from .models import Categoria, Producto

MAX_IMAGEN_MB = 2
EXTENSIONES_IMAGEN = {"jpg", "jpeg", "png", "webp"}


class BootstrapFormMixin:
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


class CategoriaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "slug"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "slug": forms.TextInput(attrs={"placeholder": "Se genera automáticamente si se deja vacío"}),
        }
        help_texts = {"slug": "Identificador para la URL. Dejalo vacío para generarlo solo."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self._aplicar_estilos()

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        qs = Categoria.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre.")
        return nombre


class ProductoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "categoria", "precio", "stock", "imagen", "activo"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "stock": forms.NumberInput(attrs={"min": "0", "step": "1"}),
        }
        help_texts = {
            "imagen": "JPG, PNG o WEBP de hasta 2 MB. Si se deja vacío se usa una imagen genérica.",
            "activo": "Los productos inactivos no se muestran en la tienda.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()
        self.fields["activo"].widget.attrs.pop("required", None)

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio <= 0:
            raise forms.ValidationError("El precio debe ser mayor a cero.")
        return precio

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("El stock no puede ser negativo.")
        return stock

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if not imagen or not hasattr(imagen, "size"):
            return imagen
        if imagen.size > MAX_IMAGEN_MB * 1024 * 1024:
            raise forms.ValidationError(f"La imagen no puede superar los {MAX_IMAGEN_MB} MB.")
        extension = imagen.name.rsplit(".", 1)[-1].lower() if "." in imagen.name else ""
        if extension not in EXTENSIONES_IMAGEN:
            raise forms.ValidationError("Formato no permitido. Usá JPG, PNG o WEBP.")
        return imagen
