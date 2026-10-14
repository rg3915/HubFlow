# Refactor #134: uuid7 em todos os models e created/modified (TimeStampedModel) no lugar de CreatedModel.
from django.db import migrations

from hubflow.core.migration_ops import add_uuid


class Migration(migrations.Migration):
    dependencies = [('permissions', '0003_permission_change')]

    operations = [
        *add_uuid('permissions', 'membership'),
        *add_uuid('permissions', 'permissionchange'),
    ]
