from django.contrib.auth.management import create_permissions
from django.db import migrations

from hubflow.permissions.catalog import ROLES


def create_roles(apps, schema_editor):
    """Papéis padrão com as permissões do catálogo (as Permission são criadas antes, explicitamente)."""
    app_config = apps.get_app_config('permissions')
    app_config.models_module = True
    create_permissions(app_config, verbosity=0)
    app_config.models_module = None
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    for name, codenames in ROLES.items():
        group, _ = Group.objects.get_or_create(name=name)
        group.permissions.set(Permission.objects.filter(content_type__app_label='permissions', codename__in=codenames))


def drop_roles(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):
    dependencies = [('permissions', '0001_initial'), ('auth', '0012_alter_user_first_name_max_length')]

    operations = [migrations.RunPython(create_roles, drop_roles)]
