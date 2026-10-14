# Refactor #134: uuid7 em todos os models e created/modified (TimeStampedModel) no lugar de CreatedModel.
from django.db import migrations

from hubflow.core.migration_ops import add_modified, add_uuid


class Migration(migrations.Migration):
    dependencies = [('sprints', '0002_core_abstracts')]

    operations = [
        add_modified('milestone'),
        *add_uuid('sprints', 'milestone'),
        add_modified('sprint'),
        *add_uuid('sprints', 'sprint'),
    ]
