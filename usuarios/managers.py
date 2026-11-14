"""Manager del modelo de usuario personalizado (login por email)."""

from django.contrib.auth.base_user import BaseUserManager


class UsuarioManager(BaseUserManager):
    """Crea usuarios usando el email como identificador único."""

    use_in_migrations = True

    def _normalizar_email(self, email):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        return self.normalize_email(email).lower()

    def create_user(self, email, password=None, **extra_fields):
        email = self._normalizar_email(email)
        extra_fields.setdefault("rol", "Cliente")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("rol", "Admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
