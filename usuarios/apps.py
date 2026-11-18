from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Usuarios'

    def ready(self):
        # Conecta la sincronización rol <-> Group. Se importa aquí para que el
        # registro de modelos ya esté completo cuando se registren las señales.
        from . import senales  # noqa: F401
