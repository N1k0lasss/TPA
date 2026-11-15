"""Rutas principales del proyecto InvenShop."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="catalogo:producto_list", permanent=False), name="inicio"),
    path("cuenta/", include("usuarios.urls")),
    path("catalogo/", include("catalogo.urls")),
    path("carrito/", include("pedidos.urls_carrito")),
    path("pedidos/", include("pedidos.urls")),
    path("panel/", include("panel.urls")),
]

# En desarrollo Django sirve los archivos subidos por los usuarios.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Personalización del encabezado del admin
admin.site.site_header = "InvenShop · Administración"
admin.site.site_title = "InvenShop"
admin.site.index_title = "Gestión de inventario y ventas"

handler403 = "panel.views.error_403"
handler404 = "panel.views.error_404"
handler500 = "panel.views.error_500"
