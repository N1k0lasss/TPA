"""Crea los grupos de Django y los asocia a los usuarios según su rol.

Los permisos de cada grupo los completa la señal ``post_migrate`` definida en
``usuarios.senales``, que se ejecuta después de que Django haya creado los
objetos Permission.
"""

from django.db import migrations

GRUPOS = ("Administradores", "Empleados", "Clientes")
GRUPO_POR_ROL = {
    "Admin": "Administradores",
    "Empleado": "Empleados",
    "Cliente": "Clientes",
}


def crear_grupos(apps, schema_editor):
    db = schema_editor.connection.alias
    Group = apps.get_model("auth", "Group")
    Usuario = apps.get_model("usuarios", "Usuario")
    through = Usuario.groups.through

    for nombre in GRUPOS:
        Group.objects.using(db).get_or_create(name=nombre)

    grupos = {grupo.name: grupo for grupo in Group.objects.using(db).filter(name__in=GRUPOS)}
    for usuario in Usuario.objects.using(db).all().iterator():
        nombre = GRUPO_POR_ROL.get(usuario.rol)
        if nombre:
            through.objects.using(db).get_or_create(
                **{f"{Usuario._meta.model_name}_id": usuario.pk, "group_id": grupos[nombre].pk}
            )


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("usuarios", "0002_alter_usuario_options"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, migrations.RunPython.noop),
    ]
