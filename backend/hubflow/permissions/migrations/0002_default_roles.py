from django.contrib.auth.management import create_permissions
from django.db import migrations

from hubflow.permissions.catalog import ROLES


def create_roles(apps, schema_editor):
    """Papéis padrão com as permissões do catálogo (as Permission são criadas antes, explicitamente)."""
    app_config = apps.get_app_config('permissions')
    app_config.models_module = True
    create_permissions(app_config, verbosity=0)
    app_config.models_module = None
    # As permissões padrão (add/change/delete/view) dos outros apps também precisam existir já aqui.
    for label in ('accounts', 'clients', 'projects', 'boards', 'sprints', 'billing'):
        other = apps.get_app_config(label)
        other.models_module = True
        create_permissions(other, verbosity=0)
        other.models_module = None
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    for name, perms in ROLES.items():
        group, _ = Group.objects.get_or_create(name=name)
        wanted = [Permission.objects.get(content_type__app_label=app, codename=codename) for app, codename in (p.split('.') for p in perms)]
        group.permissions.set(wanted)


def drop_roles(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('permissions', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('accounts', '0004_user_avatar'),
        ('clients', '0001_initial'),
        ('projects', '0006_project_webhook_secret'),
        ('boards', '0014_card_issue'),
        ('sprints', '0002_core_abstracts'),
        ('billing', '0002_payment_project_period'),
    ]

    operations = [migrations.RunPython(create_roles, drop_roles)]
