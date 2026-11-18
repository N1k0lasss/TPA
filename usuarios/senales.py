"""Sincronización entre el rol de ``Usuario`` y los grupos de Django.

El rol es la fuente de verdad de la autorización de la tienda. Los grupos
existen para cumplir la recomendación de la cátedra de gestionar permisos en
bloque y para que el Django Admin también los tenga en cuenta. Este módulo
mantiene ambos en concordancia:

* al migrar, crea los tres grupos, les asigna sus permisos y actualiza a los
  usuarios ya existentes;
* al crear o cambiar el rol de un usuario, le asigna el grupo correspondiente.
"""

from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .backends import GRUPOS_POR_ROL, PERMISOS_POR_GRUPO
from .models import Usuario


def _permisos(codenames):
    """Devuelve los objetos Permission a partir de strings ``app.codename``."""
    if not codenames:
        return []
    filtro = Q()
    for permiso in codenames:
        app_label, codename = permiso.split(".", 1)
        filtro |= Q(content_type__app_label=app_label, codename=codename)
    return list(Permission.objects.filter(filtro))


def sincronizar_grupos(using="default"):
    """Crea/actualiza los tres grupos con los permisos definidos por rol."""
    for nombre, codenames in PERMISOS_POR_GRUPO.items():
        grupo, _creado = Group.objects.using(using).get_or_create(name=nombre)
        grupo.permissions.set(_permisos(codenames))


def sincronizar_usuario(usuario):
    """Ajusta el grupo de un usuario según su rol, conservando otros grupos."""
    nombre_grupo = GRUPOS_POR_ROL.get(usuario.rol)
    if nombre_grupo is None:
        return
    db = usuario._state.db or "default"
    grupo = Group.objects.using(db).filter(name=nombre_grupo).first()
    if grupo is None:
        return  # Los grupos se crean en post_migrate; se reintentará en el próximo alta.

    actuales = set(
        usuario.groups.filter(name__in=GRUPOS_POR_ROL.values()).values_list("name", flat=True)
    )
    deseados = {nombre_grupo}
    for nombre in actuales - deseados:
        usuario.groups.remove(Group.objects.using(db).get(name=nombre))
    if deseados - actuales:
        usuario.groups.add(grupo)


@receiver(post_migrate)
def inicializar_grupos(sender, using, **kwargs):
    """Se ejecuta después de migrar ``usuarios``.

    Django crea los permisos de una sola app por cada señal ``post_migrate``,
    así que primero nos aseguramos de que existan los de todas las apps antes
    de poblar los grupos.
    """
    if getattr(sender, "name", None) != "usuarios":
        return
    for app_config in global_apps.get_app_configs():
        create_permissions(app_config, verbosity=0, using=using, apps=global_apps)
    sincronizar_grupos(using=using)
    for usuario in Usuario.objects.using(using).all().iterator():
        sincronizar_usuario(usuario)


@receiver(post_save, sender=Usuario, dispatch_uid="invenshop.grupo_segun_rol")
def grupo_segun_rol(sender, instance, raw, **kwargs):
    """Mantiene el grupo alineado con el rol (alta, edición o cambio de rol)."""
    if not raw:
        sincronizar_usuario(instance)
