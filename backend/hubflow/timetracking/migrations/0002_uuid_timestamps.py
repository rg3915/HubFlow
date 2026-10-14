# Refactor #134: uuid7 em todos os models e created/modified (TimeStampedModel) no lugar de CreatedModel.
from django.db import migrations

from hubflow.core.migration_ops import add_modified, add_uuid


class Migration(migrations.Migration):
    dependencies = [('timetracking', '0001_initial')]

    operations = [
        add_modified('timeentry'),
        *add_uuid('timetracking', 'timeentry'),
    ]
